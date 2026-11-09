"""One-time frozen-input preparation, explicitly requested by task owner.

No model or key access. Copy course runner/auditor exactly; do not initialize.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parents[2]
OLD_CLARIFICATION = ROOT / "artifacts/w03/model-clarification-20261108"
OLD_REPAIR = ROOT / "artifacts/w03/answer-repair-20261107"
SOURCE = OLD_REPAIR / "stage5-compact-evidence/input"
INPUT = BASE / "qa-01/input"
IDS = ["U05", "E01", "TRACECTRL01", "CTRL01", "U01", "P01"]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def copy_new(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as f:
        f.write(source.read_bytes())
    assert sha(source) == sha(target)


def main():
    scope = read(BASE / "scope.json")
    assert scope["case_ids"] == IDS
    assert not (INPUT / "manifest.json").exists()
    snapshot_paths = {p for p in OLD_CLARIFICATION.rglob("*") if p.is_file()}
    snapshot_paths.update({OLD_REPAIR / "completion.json", OLD_REPAIR / "execution_ledger.json"})
    snapshot_paths.update(p for p in OLD_REPAIR.rglob("*") if p.is_file() and
                          ("independent-review" in p.parts or p.name.startswith("final-aggregate-review.")))
    protected = read(SOURCE / "protected.json")
    assert len(protected) == 12
    for relative, digest in protected.items():
        assert sha(ROOT / relative) == digest
        snapshot_paths.add(ROOT / relative)
    snapshot_paths.add(ROOT / "artifacts/w02/workflows/WF-8d2ebffec9d94a25bc164ae489fe13a0/proposal-3.json")
    save(BASE / "input-integrity/baseline_snapshot.json", {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Entire previous model-clarification directory; previous repair completion/ledger/reviews; 12 protected files and old proposal",
        "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(snapshot_paths)},
        "old_clarification_file_count": sum(p.is_relative_to(OLD_CLARIFICATION) for p in snapshot_paths),
        "protected_file_count": 12})
    for filename in ("run_batch.py", "audit_results.py"):
        copy_new(OLD_CLARIFICATION / "support" / filename, BASE / "support" / filename)
    for filename in ("original_questions.json", "reviewer_expectations.json", "controls.json",
                     "new_control_approval.json", "protected.json"):
        copy_new(SOURCE / filename, INPUT / filename)
    model = ROOT / scope["model_source"]
    assert sha(model) == scope["model_sha256"] == "5fb4beed511b19c78333c38252f331c6a2aa159ec654a98eec8703f48d79ffe9"
    prompt = BASE / "candidate/knowledge_prompt.txt"
    assert sha(prompt) == scope["candidate_prompt_sha256"] == "74af26664273fe70d85cd0f84d13dc07bc7850614fb8368c2f822c74742ec40d"
    copy_new(model, INPUT / "business_model.md")
    copy_new(prompt, INPUT / "knowledge_prompt.txt")
    source_cases = {x["id"]: x for x in read(SOURCE / "selected_questions.json")["cases"]}
    source_requests = {x["id"]: x for x in read(SOURCE / "requests.json")["requests"]}
    source_origins = {x["id"]: x for x in read(SOURCE / "request_origins.json")["cases"]}
    save(INPUT / "selected_questions.json", {"client_date": "2026-11-08", "cases": [source_cases[i] for i in IDS]})
    save(INPUT / "requests.json", {"requests": [source_requests[i] for i in IDS]})
    save(INPUT / "request_origins.json", {"cases": [source_origins[i] for i in IDS]})
    config = read(SOURCE / "knowledge.json")
    config["business_model"] = (INPUT / "business_model.md").relative_to(ROOT).as_posix()
    config["prompt"] = (INPUT / "knowledge_prompt.txt").relative_to(ROOT).as_posix()
    save(INPUT / "knowledge.json", config)
    save(INPUT / "manifest.json", {
        "client_date": "2026-11-08", "frozen_at": datetime.now(timezone.utc).isoformat(),
        "frozen_before_execution": True, "case_ids": IDS,
        "files": {p.relative_to(INPUT.parent).as_posix(): sha(p) for p in sorted(INPUT.rglob("*")) if p.is_file()},
        "runtime_plan": {"model": "deepseek-flash", "profile": "deepseek-json", "timeout": 180,
                         "max_tokens": 8192, "retry_max_tokens": 16384, "retry_timeout": 240},
        "tested_input": "Same clarified model, exact Stage5 questions/materials/fixture/expectations; only the isolated answer prompt changes",
        "original_cases": 4, "control_cases": 2, "reviewer_expectations_sent": False,
        "model_sha256": sha(INPUT / "business_model.md"), "candidate_prompt_sha256": sha(prompt),
        "controls_note": "All six original approved control metadata records and their approval binding copied byte-for-byte; only TRACECTRL01 and CTRL01 selected",
        "stop_rule": "At most six new native runs, each case once; only native confirmed length expansion. No semantic/format resampling or separate network recovery this round."})
    save(BASE / "input-integrity/preparation.json", {
        "status": "input_frozen_pending_independent_review", "model_calls": 0, "keychain_reads": 0,
        "case_ids": IDS, "original_cases": 4, "control_cases": 2,
        "baseline_snapshot_sha256": sha(BASE / "input-integrity/baseline_snapshot.json"),
        "source_requests_file": (SOURCE / "requests.json").relative_to(ROOT).as_posix(),
        "source_requests_sha256": sha(SOURCE / "requests.json"),
        "manifest_sha256": sha(INPUT / "manifest.json"), "execution_approved": False})
    print(json.dumps({"status": "input_frozen_pending_independent_review", "cases": 6,
                      "protected_snapshot_files": len(snapshot_paths), "actual_model_calls": 0}))


if __name__ == "__main__":
    main()
