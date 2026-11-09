"""Frozen-input runner; native course answer contract, independent live gate.

--check-only never reads credentials, constructs Agent, or calls a model.
No answer repair, semantic scoring, or runner-level model retries.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
SUPPORT = Path(__file__).resolve().parent
REPAIR = SUPPORT.parent
ROOT = SUPPORT.parents[3]
sys.path.insert(0, str(ROOT / "platform"))
from fde_product.agent import Agent
from fde_product.natural_knowledge import (
    CheckError, ContextModel, IMPLEMENTATION, SnapshotReader, Workspace,
    check_run, load_task, messages_for, require,
)

TRACKS = {"model_only", "model_with_fixed_materials", "model_with_source_context"}
POLICY = {"model": "deepseek-flash", "profile": "deepseek-json", "timeout": 180,
          "max_tokens": 8192, "retry_max_tokens": 16384, "retry_timeout": 240}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def json_sha(value):
    return text_sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_error(exc):
    # Do not serialize exception strings, tracebacks, request headers, or keys.
    return {"code": getattr(exc, "code", type(exc).__name__), "type": type(exc).__name__}


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_identical_or_new(path, value):
    if path.exists():
        require(read(path) == value, "EXISTING_ARTIFACT_DIFFERS", str(path))
    else:
        save_new(path, value)


def confined(base, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), "RELATIVE_PATH_REQUIRED")
    require(".." not in Path(relative).parts, "PATH_TRAVERSAL")
    path = (base / relative).resolve()
    require(path.is_relative_to(base.resolve()), "PATH_OUTSIDE_BOUNDARY")
    return path


def batch_path(value):
    path = Path(value).resolve()
    require(path.is_dir() and path.is_relative_to(REPAIR) and path != REPAIR
            and not path.is_relative_to(SUPPORT), "BATCH_OUTSIDE_REPAIR")
    return path


def by_id(items, label):
    require(isinstance(items, list), label + "_NOT_LIST")
    result = {}
    for item in items:
        require(isinstance(item, dict) and isinstance(item.get("id"), str)
                and re.fullmatch(r"[A-Za-z0-9_-]+", item["id"]), label + "_ID_INVALID")
        require(item["id"] not in result, label + "_DUPLICATE_ID")
        result[item["id"]] = item
    return result


def prepare(batch):
    """Read and validate all frozen input, without fetching credentials."""
    manifest_path = batch / "input/manifest.json"
    manifest = read(manifest_path)
    files = manifest["files"]
    require(isinstance(files, dict) and files, "MANIFEST_INVALID")
    required = {"input/business_model.md", "input/knowledge_prompt.txt", "input/knowledge.json",
                "input/requests.json", "input/selected_questions.json", "input/original_questions.json",
                "input/controls.json", "input/protected.json"}
    require(required <= files.keys(), "MANIFEST_REQUIRED_FILE_MISSING")
    actual = {p.relative_to(batch).as_posix() for p in (batch / "input").rglob("*")
              if p.is_file() and p != manifest_path}
    require(actual == set(files), "MANIFEST_FILE_SET_MISMATCH")
    for name, expected in files.items():
        require(name.startswith("input/"), "MANIFEST_PATH_INVALID")
        require(sha(confined(batch, name)) == expected, "FROZEN_INPUT_CHANGED", name)
    protected = read(batch / "input/protected.json")
    require(isinstance(protected, dict) and protected, "PROTECTED_EMPTY")
    for name, expected in protected.items():
        require(sha(confined(ROOT, name)) == expected, "PROTECTED_INPUT_CHANGED", name)
    cases = by_id(read(batch / "input/selected_questions.json")["cases"], "SELECTED")
    originals = by_id(read(batch / "input/original_questions.json")["cases"], "ORIGINAL")
    controls = by_id(read(batch / "input/controls.json")["cases"], "CONTROL")
    require(cases and not (originals.keys() & controls.keys()), "CONTROL_ORIGINAL_ID_COLLISION")
    if controls:
        require("input/new_control_approval.json" in files, "CONTROL_APPROVAL_NOT_FROZEN")
        approval = read(batch / "input/new_control_approval.json")
        require(approval.get("approved") is True and approval.get("controls_sha256") == sha(batch / "input/controls.json"),
                "CONTROL_NOT_APPROVED")
    requests_doc = read(batch / "input/requests.json")
    require(isinstance(requests_doc, dict) and set(requests_doc) == {"requests"}, "REQUEST_DOCUMENT_INVALID")
    requests = by_id(requests_doc["requests"], "REQUEST")
    require(cases.keys() == requests.keys(), "REQUEST_CASE_SET_MISMATCH")
    if "case_ids" in manifest:
        require(manifest["case_ids"] == list(cases), "MANIFEST_CASE_SET_MISMATCH")
    config_path = (batch / "input/knowledge.json").relative_to(ROOT).as_posix()
    reader = SnapshotReader(ROOT)
    config, document, prompt, _, _ = load_task(reader, config_path)
    require(config["business_model"] == (batch / "input/business_model.md").relative_to(ROOT).as_posix()
            and config["prompt"] == (batch / "input/knowledge_prompt.txt").relative_to(ROOT).as_posix()
            and config["profile"] == POLICY["profile"], "CONFIG_NOT_ISOLATED")
    checks = []
    for case_id, case in cases.items():
        reference = originals.get(case_id, controls.get(case_id))
        require(reference is not None and case == reference, "CASE_METADATA_CHANGED", case_id)
        require(case.get("input_track") in TRACKS, "TRACK_INVALID", case_id)
        request = requests[case_id]
        require(set(request) == {"id", "question"}, "REQUEST_FIELDS_CHANGED", case_id)
        question = request["question"]
        require(isinstance(question, str) and 0 < len(question.strip()) <= 8000, "QUESTION_INVALID", case_id)
        # Materials may be embedded directly in an independently approved control.
        # This runner never reconstructs or shortens the frozen question string.
        messages = messages_for(document, prompt, question, True)
        context_chars = len(json.dumps(messages, ensure_ascii=False))
        require(context_chars <= config["max_context_chars"], "CONTEXT_LIMIT", case_id)
        require(set(json.loads(messages[1]["content"])) == {"business_model", "question"}, "INPUT_FIELDS_CHANGED")
        checks.append({"id": case_id, "input_track": case["input_track"],
                       "question_sha256": text_sha(question), "messages_sha256": json_sha(messages),
                       "context_chars": context_chars, "expected_sent": False, "tools": [],
                       "case_origin": "original" if case_id in originals else "independent_control"})
    implementation = set(IMPLEMENTATION) | {"contracts/w02/natural_run.schema.json"}
    preflight = {"status": "input_checked", "actual_model_calls": 0,
                 "runner_sha256": sha(Path(__file__)), "manifest_sha256": sha(manifest_path),
                 "requests_sha256": sha(batch / "input/requests.json"),
                 "protected_sha256": sha(batch / "input/protected.json"),
                 "runtime_policy": POLICY, "max_concurrency": 2, "cases": checks,
                 "native_source_hashes": {name: hashlib.sha256(data).hexdigest()
                                          for name, data in sorted(reader.files.items())},
                 "implementation_hashes": {name: sha(ROOT / name) for name in sorted(implementation)},
                 "reviewer_expectations_sent": False, "semantic_review": "not_performed"}
    return {"batch": batch, "cases": cases, "requests": requests, "preflight": preflight,
            "config_path": config_path, "document": document, "prompt": prompt}


def check_gate(context):
    batch = context["batch"]
    preflight = read(batch / "preflight.json")
    require(preflight == context["preflight"], "PREFLIGHT_CHANGED_OR_STALE")
    gate = read(batch / "gate_acceptance.json")
    require(gate.get("approved") is True and gate.get("failed_checks") == [], "GATE_NOT_APPROVED")
    for key, path in (("runner_sha256", Path(__file__)),
                      ("manifest_sha256", batch / "input/manifest.json"),
                      ("preflight_sha256", batch / "preflight.json")):
        require(gate.get(key) == sha(path), "GATE_HASH_MISMATCH", key)
    review = confined(batch, gate.get("input_review", "input-review.json"))
    require(gate.get("input_review_sha256") == sha(review), "INPUT_REVIEW_CHANGED")
    # The independent gate author must reconcile review status, failed checks,
    # and narrative. This runner verifies that exact signed-off review, not prose.
    return gate


def read_key():
    require(sys.platform == "darwin", "LOCAL_MACOS_KEYCHAIN_REQUIRED")
    credential = subprocess.run(["/usr/bin/security", "find-generic-password", "-a", getpass.getuser(),
                                 "-s", "com.chenzhaowen.aifde.w02.deepseek", "-w"],
                                capture_output=True, text=True, timeout=20)
    key = credential.stdout.rstrip("\r\n")
    require(credential.returncode == 0 and key and not any(c.isspace() for c in key), "LOCAL_KEY_UNAVAILABLE")
    return key


def native_inventory(folder):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(folder.rglob("*")) if p.is_file()}


def find_native(context, question, before):
    found = []
    for path in (ROOT / "artifacts/w02/knowledge_runs").glob("*/settings.json"):
        if str(path.parent) in before:
            continue
        settings = read(path)
        if settings.get("config_path") == context["config_path"] and settings.get("question") == question:
            found.append(path.parent)
    return found


def execute(context, case_id, key):
    batch = context["batch"]
    # Recheck immediately before reserving this case, even during a subset run.
    fresh = prepare(batch)
    check_gate(fresh)
    case = context["cases"][case_id]
    question = context["requests"][case_id]["question"]
    marker = batch / "output" / (case_id + ".started.json")
    save_new(marker, {"case_id": case_id, "started_at": now(),
                      "question_sha256": text_sha(question), "gate_sha256": sha(batch / "gate_acceptance.json")})
    record = {"case_id": case_id, "started_at": read(marker)["started_at"],
              "question": case["question"], "fixture": case.get("fixture"),
              "input_track": case["input_track"], "fixed_materials": case.get("fixed_materials", []),
              "actual_question_sha256": text_sha(question), "requests_sha256": sha(batch / "input/requests.json"),
              "model_sha256": sha(batch / "input/business_model.md"),
              "gate_sha256": sha(batch / "gate_acceptance.json"),
              "result": None, "actual_answer": None, "native_structure_check": "not_completed",
              "runner_errors": [], "semantic_review": "pending_independent_review"}
    before = {str(p) for p in (ROOT / "artifacts/w02/knowledge_runs").glob("*")}
    agent = None
    native = []
    try:
        model = ContextModel(url="https://api.deepseek.com/chat/completions", key=key, **POLICY)
        model.deadline = time.monotonic() + 420
        agent = Agent(batch / "runtime" / case_id, model)
        record["result"] = agent.answer_business_model(
            ROOT, context["config_path"], question, include_knowledge=True,
            expected="", pair_id=None, reader=SnapshotReader(ROOT))
    except Exception as exc:
        record["runner_errors"].append({"phase": "native_execution", **safe_error(exc)})
    finally:
        if agent is not None:
            try:
                agent.close()
            except Exception as exc:
                record["runner_errors"].append({"phase": "agent_close", **safe_error(exc)})
    # Keep result and native files even when course check_run rejects the record.
    try:
        if record["result"] is not None:
            native = [confined(ROOT, record["result"]["run"]).parent]
        else:
            native = find_native(context, question, before)
        record["native_directories"] = [p.relative_to(ROOT).as_posix() for p in native]
        record["native_files"] = {k: v for folder in native for k, v in native_inventory(folder).items()}
        if len(native) == 1 and (native[0] / "run.json").exists():
            run_path = (native[0] / "run.json").relative_to(ROOT).as_posix()
            record["native_run"] = read(ROOT / run_path)
            record["native_run_sha256"] = sha(ROOT / run_path)
            run, settings, _, _ = check_run(Workspace(ROOT), run_path)
            require(run["mode"] == "live" and settings["include_knowledge"] is True, "RUN_MODE_CHANGED")
            require(settings["question"] == question and settings["expected"] == "", "INPUT_MISMATCH")
            require(run["model"]["name"] == POLICY["model"], "MODEL_CHANGED")
            record["native_structure_check"] = "passed"
            answer_path = native[0] / "answer.json"
            if run["status"] == "succeeded":
                record["actual_answer"] = read(answer_path)["answer"]
        else:
            record["native_structure_check"] = "missing_or_ambiguous_native_run"
    except Exception as exc:
        record["native_structure_check"] = "failed"
        record["runner_errors"].append({"phase": "native_structure_check", **safe_error(exc)})
    record["completed_at"] = now()
    result = record["result"] or {}
    record["status"] = "runner_error" if record["runner_errors"] or record["native_structure_check"] != "passed" else result.get("status", "runner_error")
    save_new(batch / "output" / (case_id + ".json"), record)
    return {"case_id": case_id, "status": record["status"], "run": result.get("run"),
            "error": result.get("error"), "native_structure_check": record["native_structure_check"]}


def update_index(context):
    batch = context["batch"]
    records = []
    for case_id in context["cases"]:
        path = batch / "output" / (case_id + ".json")
        if path.exists():
            record = read(path)
            records.append({"id": case_id, "status": record["status"], "result": record["result"],
                            "native_structure_check": record["native_structure_check"],
                            "output_sha256": sha(path)})
    index = {"completed_case_records": len(records), "total_selected": len(context["cases"]),
             "cases": records, "pending_case_ids": [i for i in context["cases"] if i not in {r["id"] for r in records}],
             "semantic_review": "pending_independent_review"}
    path = batch / "run_index.json"
    temp = batch / "run_index.json.tmp"
    temp.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--cases", nargs="+")
    args = parser.parse_args()
    batch = batch_path(args.batch)
    context = prepare(batch)
    selected = args.cases if args.cases is not None else list(context["cases"])
    require(len(set(selected)) == len(selected) and set(selected) <= context["cases"].keys(), "UNKNOWN_OR_DUPLICATE_CASE")
    if args.check_only:
        write_identical_or_new(batch / "preflight.json", context["preflight"])
        print(json.dumps({"status": "input_checked", "cases": len(context["cases"]), "actual_model_calls": 0}))
        return 0
    check_gate(context)
    for case_id in selected:
        require(not list((batch / "output").glob(case_id + ".*")), "CASE_OUTPUT_ALREADY_EXISTS", case_id)
        require(not (batch / "runtime" / case_id).exists(), "CASE_RUNTIME_ALREADY_EXISTS", case_id)
    # A batch lock prevents concurrent invocations from bypassing reservations.
    lock = batch / ".runner.lock"
    save_new(lock, {"pid": os.getpid(), "started_at": now(), "cases": selected})
    try:
        key = read_key()
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["FDE_MODEL_TIMEOUT"] = "180"
        results = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(execute, context, case_id, key): case_id for case_id in selected}
            for future in as_completed(futures):
                case_id = futures[future]
                try:
                    item = future.result()
                except Exception as exc:
                    item = {"case_id": case_id, "status": "runner_error", **safe_error(exc)}
                    path = batch / "output" / (case_id + ".runner-error.json")
                    if not path.exists():
                        save_new(path, item)
                results.append(item)
                update_index(context)
                print(json.dumps(item, ensure_ascii=False), flush=True)
        return 0 if all(item["status"] == "succeeded" for item in results) else 2
    finally:
        lock.unlink()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "failed", **safe_error(exc)}))
        raise SystemExit(2)
