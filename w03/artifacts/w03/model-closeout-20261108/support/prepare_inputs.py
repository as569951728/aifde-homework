"""One-time input copy and targeted preservation manifest; no credentials or API."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parents[2]
PRIOR = ROOT / "artifacts/w03/citation-alignment-20261108"
SOURCE = ROOT / "artifacts/w03/answer-repair-20261107/stage5-compact-evidence/input"
CALIBRATION = ROOT / "artifacts/w03/source-semantics-audit-20261108"
INPUT = BASE / "qa-01/input"
IDS = ["U05", "U01", "P01", "E01", "TRACECTRL01", "CTRL01", "E03"]
MODEL_SHA = "63513ef37e2d1f41cc0e540fd4b771b4035c83e3674d33e0897a521bc698a72d"
EXPECTED_SHA = "f799da7f4420620386e73f6b447efe219ed37f22ef881f08595f995b2b5280a2"
PROMPT_SHA = "9614640cce2ef475a3f90e40f6264bbc97ad9ef7548b2caf57923de1572fa67c"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


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
    assert not (INPUT / "manifest.json").exists()
    model = CALIBRATION / "candidate/business_model.md"
    expected = CALIBRATION / "candidate/reviewer_expectations.json"
    prompt = BASE / "candidate/knowledge_prompt.txt"
    assert sha(model) == MODEL_SHA and sha(expected) == EXPECTED_SHA and sha(prompt) == PROMPT_SHA
    old_protected = read(SOURCE / "protected.json")
    assert len(old_protected) == 12
    for p, digest in old_protected.items():
        assert sha(ROOT / p) == digest
    protected = dict(old_protected)
    def protect(path):
        protected[path.relative_to(ROOT).as_posix()] = sha(path)
    protect(ROOT / "artifacts/w02/workflows/WF-8d2ebffec9d94a25bc164ae489fe13a0/proposal-3.json")
    # Preserve the existing evidence chain, not entire historical directories.
    for relative in [
        "answer-repair-20261107/completion.json", "answer-repair-20261107/execution_ledger.json",
        "answer-repair-20261107/aggregate-review/final-aggregate-review.json",
        "model-clarification-20261108/completion.json", "model-clarification-20261108/execution_ledger.json",
        "model-clarification-20261108/qa-01/independent-review/review.json",
        "model-clarification-20261108/qa-02-u05-recovery/independent-review/review.json",
        "citation-alignment-20261108/completion.json", "citation-alignment-20261108/execution_ledger.json",
        "citation-alignment-20261108/qa-01/independent-review/review.json",
        "citation-alignment-20261108/aggregate-review/final-review.json",
        "citation-alignment-20261108/input-integrity/baseline_snapshot.json",
        "source-semantics-audit-20261108/completion.json",
        "source-semantics-audit-20261108/reviewed_candidate_manifest.json",
        "source-semantics-audit-20261108/aggregate-review/final-review.json",
    ]:
        protect(ROOT / "artifacts/w03" / relative)
    for p in [model, expected, SOURCE / "requests.json", SOURCE / "selected_questions.json",
              SOURCE / "request_origins.json", CALIBRATION / "input/original_questions.json"]:
        protect(p)
    for g in ["model_and_artifact", "fixed_materials", "source_context"]:
        protect(CALIBRATION / "reviews" / g / "revision-review.json")
    # Directly preserve the seven latest comparable answers and their native public evidence.
    for case_id in IDS:
        old_batch = (PRIOR / "qa-01" if case_id != "E03" else
                     ROOT / "artifacts/w03/model-clarification-20261108/qa-01")
        output = old_batch / "output" / (case_id + ".json")
        protect(output)
        record = read(output)
        for name, digest in record["native_files"].items():
            path = ROOT / name
            if path.parent.as_posix() == (ROOT / record["result"]["run"]).parent.as_posix():
                assert sha(path) == digest
                protect(path)
    save(BASE / "input-integrity/baseline_snapshot.json", {
        "captured_at": datetime.now(timezone.utc).isoformat(), "files": protected,
        "scope": "12 formal protections, old proposal, prior summary/review chains, seven comparable outputs and native top-level evidence; hashes only, no historical directory copy",
        "formal_protected_count": 12})
    for filename in ["run_batch.py", "audit_results.py"]:
        copy_new(PRIOR / "support" / filename, BASE / "support" / filename)
    for filename in ["controls.json", "new_control_approval.json"]:
        copy_new(SOURCE / filename, INPUT / filename)
    copy_new(CALIBRATION / "input/original_questions.json", INPUT / "original_questions.json")
    copy_new(expected, INPUT / "reviewer_expectations.json")
    copy_new(model, INPUT / "business_model.md")
    copy_new(prompt, INPUT / "knowledge_prompt.txt")
    save(INPUT / "protected.json", protected)
    cases = {x["id"]: x for x in read(SOURCE / "selected_questions.json")["cases"]}
    requests = {x["id"]: x for x in read(SOURCE / "requests.json")["requests"]}
    origins = {x["id"]: x for x in read(SOURCE / "request_origins.json")["cases"]}
    save(INPUT / "selected_questions.json", {"client_date": "2026-11-08", "cases": [cases[i] for i in IDS]})
    save(INPUT / "requests.json", {"requests": [requests[i] for i in IDS]})
    save(INPUT / "request_origins.json", {"cases": [origins[i] for i in IDS]})
    config = read(SOURCE / "knowledge.json")
    config.update(business_model=(INPUT / "business_model.md").relative_to(ROOT).as_posix(),
                  prompt=(INPUT / "knowledge_prompt.txt").relative_to(ROOT).as_posix())
    save(INPUT / "knowledge.json", config)
    save(INPUT / "manifest.json", {
        "frozen_at": datetime.now(timezone.utc).isoformat(), "frozen_before_execution": True,
        "case_ids": IDS, "original_cases": 5, "control_cases": 2,
        "files": {p.relative_to(INPUT.parent).as_posix(): sha(p) for p in sorted(INPUT.rglob("*")) if p.is_file()},
        "model_sha256": MODEL_SHA, "expected_sha256": EXPECTED_SHA, "candidate_prompt_sha256": PROMPT_SHA,
        "reviewer_expectations_sent": False,
        "runtime_plan": {"model": "deepseek-flash", "profile": "deepseek-json", "timeout": 180,
                         "max_tokens": 8192, "retry_max_tokens": 16384, "retry_timeout": 240},
        "input_reuse": "All seven final questions including fixtures and materials are exact Stage5 strings; E03 is model_only and unchanged. Six control metadata/approval records retained.",
        "control_source_kinds": {"CTRL01": "actual W02 Chen interview", "TRACECTRL01": "synthetic control"},
        "stop_rule": "At most seven native runs, each once. Only native confirmed length expansion; no semantic/format/network retry or recovery."})
    save(BASE / "input-integrity/preparation.json", {
        "status": "frozen_pending_independent_review", "execution_approved": False,
        "case_ids": IDS, "original_cases": 5, "controls": 2, "model_calls": 0, "keychain_reads": 0,
        "manifest_sha256": sha(INPUT / "manifest.json"), "preserved_files": len(protected),
        "baseline_snapshot_sha256": sha(BASE / "input-integrity/baseline_snapshot.json")})
    print(json.dumps({"status": "frozen_pending_independent_review", "cases": len(IDS), "preserved_files": len(protected), "model_calls": 0}))


if __name__ == "__main__":
    main()
