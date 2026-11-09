"""Exercise the unchanged course review/proposal state machine in isolated workspaces.

Read/extract/show are scripted setup. Extraction uses fixed claims, not another
LLM. Only audit and compose invoke the live model; apply is never called.
"""
import argparse
from copy import deepcopy
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import certifi

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "platform"))
from fde_product import extraction_workflow as wf
from fde_product.interview_extraction import Workspace, CheckError


def write(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


class FixedExtraction:
    mode = "fixture"

    def __init__(self, claims):
        self.claims = claims

    def complete(self, messages, tools):
        payload = json.loads(messages[-1]["content"])
        value = {"claims": self.claims} if "transcripts" in payload else {"conflicts": []}
        return {"role": "assistant", "content": json.dumps(value, ensure_ascii=False)}, {}


def prepare(base, item):
    folder = base / "runs" / item["id"]
    folder.mkdir(parents=True, exist_ok=False)
    ws = Workspace(folder / "workspace")
    fixture = json.loads((base / item["input"]).read_text())
    # Provision ONLY a new, isolated test workspace; never initialize the project.
    ws.write("docs/model.md", fixture["existing_model"].encode(), raw=True)
    ws.write("docs/notes.md", json.dumps(fixture["context"], ensure_ascii=False).encode(), raw=True)
    ws.write("customer/skill.md", (base / item["method"]).read_bytes(), raw=True)
    ws.write("customer/prompt.txt", b"Fixed extraction fixture; not a live extraction.", raw=True)
    ws.write("sources/transcript.json", fixture["transcript"])
    cfg = {"version": "w02-extractor-0.1.0", "scope_id": fixture["transcript"]["scope_id"],
           "sources": ["sources/transcript.json"], "prompt": "customer/prompt.txt",
           "focus_questions": [fixture["goal"]], "batch_chars": 18000,
           "max_batches": 24, "reconcile_chars": 96000, "profile": "deepseek-json"}
    ws.write("customer/extraction.json", cfg)
    task = {"version": wf.VERSION, "goal": fixture["goal"],
            "extraction_config": "customer/extraction.json", "skill": "customer/skill.md",
            "business_model": "docs/model.md", "notes": "docs/notes.md", "max_steps": 10}
    ws.write("customer/workflow.json", task)
    path = wf.start(ws, "customer/workflow.json")
    s = wf.load_session(ws, path)
    extractor = FixedExtraction(fixture["claims"])
    for name in ("inspect_materials", "extract_candidates", "show_evidence"):
        args = {} if name != "show_evidence" else {"claim_ids": [c["id"] for c in wf.facts(ws, s)[0]["claims"]]}
        result = wf.tool(ws, s, name, args, extractor)
        call_id = "scripted-setup-" + name
        s["messages"].append({"role": "assistant", "content": None, "tool_calls": [{
            "id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]})
        s["messages"].append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(result, ensure_ascii=False)})
        s["tool_events"].append({"step": 0, "name": name, "call_id": call_id, "result": result,
                                 "origin": "scripted_fixture_setup_not_model_decision"})
    wf.save(ws, path, s)
    ids = [c["id"] for c in wf.facts(ws, s)[0]["claims"]]
    before = {k: wf.digest(ws.raw(task[k])) for k in ("business_model", "notes")}
    try:
        wf.tool(ws, s, "propose_update", {"claim_ids": ids, "business_model": "sentinel",
                "notes_update": "sentinel", "next_questions": ["sentinel"], "summary": "sentinel"}, extractor)
        raise AssertionError("Premature proposal was accepted")
    except CheckError as e:
        assert e.code == "HUMAN_REVIEW_REQUIRED", e.code
    assert before == {k: wf.digest(ws.raw(task[k])) for k in before}
    write(folder / "setup.json", {"session": path, "claim_ids": ids,
          "scripted_setup": ["inspect_materials", "extract_candidates", "show_evidence"],
          "extractor": "fixed_fixture", "premature_proposal_rejected": True,
          "base_hashes": before, "apply_enabled": False})


def run_stage(base, item, stage, key):
    folder = base / "runs" / item["id"]
    setup = json.loads((folder / "setup.json").read_text())
    ws = Workspace(folder / "workspace")
    path = setup["session"]
    if (folder / (stage + ".json")).exists():
        raise SystemExit("Stage already run; retain prior result.")
    s = wf.load_session(ws, path)
    if stage == "compose":
        gate = json.loads((folder / "review-gate.json").read_text())
        assert gate["allow_compose"] is True
        assert gate["pending_sha256"] == wf.digest(json.dumps(s["pending"], ensure_ascii=False, sort_keys=True).encode())
        wf.review(ws, path, "【隔离验证中的测试审核，非学员/客户采纳】\n" + gate["feedback"])
    else:
        assert s["status"] == "active" and not s["human_reviews"]
    model = wf.WorkflowModel(url="https://api.deepseek.com/chat/completions", key=key,
        model="deepseek-flash", profile="deepseek-json", timeout=180,
        max_tokens=16384, retry_max_tokens=32768, retry_timeout=240)
    fixture = json.loads((base / item["input"]).read_text())
    result = wf.advance(ws, path, model, FixedExtraction(fixture["claims"]))
    checks = {k: wf.digest(ws.raw(result["task"][k])) == h for k, h in setup["base_hashes"].items()}
    assert all(checks.values()), "A source document changed without apply"
    summary = {"status": result["status"], "error": result["error"],
               "document_hashes_unchanged": checks, "calls_total": len(result["calls"]),
               "human_review_count": len(result["human_reviews"]), "apply_performed": False}
    if result["status"] == "awaiting_review":
        write(folder / (stage + "-review-request.json"), result["pending"])
        (folder / (stage + "-review-request.md")).write_text(result["pending"]["question"])
        try:
            wf.advance(ws, path, model, FixedExtraction(fixture["claims"]))
            raise AssertionError("Missing human feedback did not block")
        except CheckError as e:
            assert e.code == "HUMAN_ACTION_REQUIRED"
        summary["resume_without_feedback_blocked"] = True
    elif result["status"] == "awaiting_apply":
        write(folder / "proposal.json", result["proposal"])
        for key_name in ("business_model", "notes_update"):
            (folder / (key_name + ".md")).write_text(result["proposal"][key_name])
    write(folder / (stage + ".json"), summary)
    print(json.dumps({"id": item["id"], **summary}, ensure_ascii=False), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--suite", type=Path, required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--stage", choices=("prepare", "audit", "compose"), required=True)
    args = p.parse_args()
    base = args.suite.resolve()
    assert base.is_relative_to(ROOT / "artifacts/w03")
    for f, h in json.loads((base / "frozen.json").read_text()).items():
        assert hashlib.sha256((base / f).read_bytes()).hexdigest() == h, f
    plan = json.loads((base / "plan.json").read_text())
    assert plan["runner_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    item = next(x for x in plan["runs"] if x["id"] == args.id)
    if args.stage == "prepare":
        prepare(base, item)
        print(json.dumps({"id": args.id, "prepared": True}))
        return
    secret = subprocess.run(["/usr/bin/security", "find-generic-password", "-a", getpass.getuser(),
         "-s", "com.chenzhaowen.aifde.w02.deepseek", "-w"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
         text=True, check=False)
    key = secret.stdout.rstrip("\r\n")
    if secret.returncode or not key or any(c.isspace() for c in key):
        raise SystemExit("Configured credential unavailable")
    os.environ["SSL_CERT_FILE"] = certifi.where()
    run_stage(base, item, args.stage, key)


if __name__ == "__main__":
    main()
