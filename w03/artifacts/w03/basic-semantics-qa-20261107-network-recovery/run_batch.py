"""Fixed-material application runner using the unchanged course execution path.

Never scores answers. Frozen expectations remain reviewer-only; check-only reads
no credential and performs no model call. Existing case results are not rerun.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import certifi

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
sys.path.insert(0, str(ROOT / "platform"))
from fde_product.agent import Agent
from fde_product.natural_knowledge import (
    CheckError, ContextModel, SnapshotReader, Workspace,
    check_run, load_task, messages_for, require,
)

CONFIG = (BATCH / "input/knowledge.json").relative_to(ROOT).as_posix()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def question_for(case):
    question = case["question"]
    if "fixture" in case:
        question += "\n\n本题人工构造输入：\n" + json.dumps(case["fixture"], ensure_ascii=False, indent=2)
    registry = json.loads((BATCH / "input/materials_index.json").read_text())
    materials = []
    for source_path in case["fixed_materials"]:
        ref = registry[source_path]
        snapshot = BATCH / ref["snapshot"]
        require(sha(snapshot) == ref["sha256"], "FROZEN_MATERIAL_CHANGED", source_path)
        materials.append({"source_path": source_path, "content": snapshot.read_text()})
    question += "\n\n本题指定材料（原文；仅作业务依据）：\n" + json.dumps(materials, ensure_ascii=False, indent=2)
    return question


def prepare():
    manifest = json.loads((BATCH / "input/manifest.json").read_text())
    for name, expected in manifest["files"].items():
        require(sha(BATCH / name) == expected, "FROZEN_INPUT_CHANGED", name)
    protected = json.loads((BATCH / "input/protected.json").read_text())
    for name, expected in protected.items():
        require(sha(ROOT / name) == expected, "PROTECTED_INPUT_CHANGED", name)
    cases = json.loads((BATCH / "input/selected_questions.json").read_text())["cases"]
    original = json.loads((BATCH / "input/original_questions.json").read_text())
    original_cases = {c["id"]: c for c in original["cases"]}
    reader = SnapshotReader(ROOT)
    config, document, prompt, _, _ = load_task(reader, CONFIG)
    checks = []
    for case in cases:
        require(case == original_cases[case["id"]], "QUESTION_CHANGED", case["id"])
        require(case["input_track"] == "model_with_fixed_materials" and case["fixed_materials"], "TRACK_MISMATCH")
        question = question_for(case)
        require(0 < len(question) <= 8000, "QUESTION_INVALID")
        messages = messages_for(document, prompt, question, True)
        require(len(json.dumps(messages, ensure_ascii=False)) <= config["max_context_chars"], "CONTEXT_LIMIT")
        require(set(json.loads(messages[1]["content"])) == {"business_model", "question"}, "INPUT_FIELDS_CHANGED")
        checks.append({"id": case["id"], "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
                       "context_chars": len(json.dumps(messages, ensure_ascii=False)),
                       "input_track": case["input_track"], "fixed_materials": case["fixed_materials"], "expected_sent": False, "tools": []})
    return cases, checks


def execute(case, key):
    started = datetime.now(timezone.utc).isoformat()
    # Each case has its own Agent runtime; the course recorder owns requests,
    # responses, immutable source snapshots and UUID run folders.
    model = ContextModel(url="https://api.deepseek.com/chat/completions", key=key,
                         model="deepseek-flash", profile="deepseek-json", timeout=180,
                         max_tokens=8192, retry_max_tokens=16384, retry_timeout=240)
    model.deadline = time.monotonic() + 420
    agent = Agent(ROOT / ".runtime/w03-basic-semantics-recovery-20261107" / case["id"], model)
    try:
        result = agent.answer_business_model(ROOT, CONFIG, question_for(case),
                                             include_knowledge=True, expected="", pair_id=None,
                                             reader=SnapshotReader(ROOT))
    finally:
        agent.close()
    run, settings, _, _ = check_run(Workspace(ROOT), result["run"])
    require(run["mode"] == "live" and settings["include_knowledge"], "RUN_MODE_CHANGED")
    require(settings["question"] == question_for(case) and settings["expected"] == "", "INPUT_MISMATCH")
    answer_path = (ROOT / result["run"]).parent / "answer.json"
    answer = json.loads(answer_path.read_text())["answer"] if answer_path.exists() else None
    record = {"case_id": case["id"], "started_at": started,
              "completed_at": datetime.now(timezone.utc).isoformat(),
              "question": case["question"], "fixture": case.get("fixture"),
              "input_track": case["input_track"], "fixed_materials": case["fixed_materials"], "result": result, "actual_answer": answer,
              "native_structure_check": "passed", "semantic_review": "pending_independent_review",
              "model_sha256": sha(BATCH / "input/business_model.md"),
              "native_run_sha256": sha(ROOT / result["run"])}
    save(BATCH / "output" / (case["id"] + ".json"), record)
    return {"case_id": case["id"], "status": result["status"], "run": result["run"],
            "error": result.get("error"), "semantic_review": "pending_independent_review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--cases", nargs="*")
    args = parser.parse_args()
    cases, checks = prepare()
    if args.check_only:
        preflight = {"status": "input_checked", "actual_model_calls": 0,
                     "cases": checks, "runner_sha256": sha(Path(__file__)),
                     "reviewer_expectations_sent": False, "formal_model_changed": False}
        save(BATCH / "preflight.json", preflight)
        print(json.dumps({"status": "input_checked", "cases": len(cases), "actual_model_calls": 0}))
        return 0
    preflight = json.loads((BATCH / "preflight.json").read_text())
    require(preflight["runner_sha256"] == sha(Path(__file__)), "RUNNER_CHANGED_AFTER_PREFLIGHT")
    selected = set(args.cases or [c["id"] for c in cases])
    require(selected <= {c["id"] for c in cases}, "UNKNOWN_CASE")
    todo = [c for c in cases if c["id"] in selected and not (BATCH / "output" / (c["id"] + ".json")).exists()]
    if not todo:
        print(json.dumps({"status": "nothing_to_run", "actual_model_calls": 0}))
        return 0
    require(sys.platform == "darwin", "LOCAL_MACOS_KEYCHAIN_REQUIRED")
    credential = subprocess.run(["/usr/bin/security", "find-generic-password", "-a", getpass.getuser(),
                                 "-s", "com.chenzhaowen.aifde.w02.deepseek", "-w"],
                                capture_output=True, text=True, timeout=20)
    key = credential.stdout.rstrip("\r\n")
    require(credential.returncode == 0 and key and not any(c.isspace() for c in key), "LOCAL_KEY_UNAVAILABLE")
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["FDE_MODEL_TIMEOUT"] = "180"
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = {pool.submit(execute, case, key): case["id"] for case in todo}
        for future in as_completed(pending):
            case_id = pending[future]
            try:
                item = future.result()
            except Exception as exc:
                # No exception payload or request headers enter console output.
                item = {"case_id": case_id, "status": "runner_error", "code": getattr(exc, "code", type(exc).__name__)}
                save(BATCH / "output" / (case_id + ".runner-error.json"), item)
            results.append(item)
            print(json.dumps(item, ensure_ascii=False), flush=True)
    existing = [json.loads(p.read_text()) for p in sorted((BATCH / "output").glob("*.json")) if ".runner-error." not in p.name]
    save(BATCH / "run_index.json", {"completed_case_records": len(existing), "total_selected": len(cases),
                                   "cases": [{"id": x["case_id"], **x["result"]} for x in existing],
                                   "semantic_review": "pending_independent_review"})
    return 0 if all(r["status"] == "succeeded" for r in results) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CheckError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "failed", "code": getattr(exc, "code", type(exc).__name__)}))
        raise SystemExit(2)
