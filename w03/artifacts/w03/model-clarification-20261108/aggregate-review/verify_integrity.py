"""Read-only clarification QA audit; no platform imports, keys or API calls.

Only new audit files inside this aggregate-review directory may be written.
Mechanical audit never grants semantic approval or predicts recovery success.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[3]
REPO = ROOT.parents[1]
PREVIOUS = ROOT / "artifacts/w03/answer-repair-20261107/stage5-compact-evidence"
RUNNER = PREVIOUS.parent / "support/run_batch.py"
IDS = {"qa-01": {"U01", "U05", "E03", "REG01", "P01", "CTRL02"},
       "qa-02-u05-recovery": {"U05"}}
CHECKS = []


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def check(value, name):
    CHECKS.append({"id": name, "passed": bool(value)})
    if not value:
        raise ValueError(name)


def unique(items):
    result = {item["id"]: item for item in items}
    check(len(result) == len(items), "unique_ids")
    return result


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def inspect_batch(name, complete):
    batch = BASE / name
    requests = unique(read(batch / "input/requests.json")["requests"])
    selected = unique(read(batch / "input/selected_questions.json")["cases"])
    check(set(requests) == set(selected) == IDS[name], name + ": scope")
    manifest = read(batch / "input/manifest.json")
    actual_files = {p.relative_to(batch).as_posix() for p in (batch / "input").rglob("*")
                    if p.is_file() and p.name != "manifest.json"}
    check(set(manifest["files"]) == actual_files, name + ": frozen_file_coverage")
    for relative, digest in manifest["files"].items():
        check(sha(batch / relative) == digest, name + ": frozen:" + relative)
    check(sha(batch / "input/business_model.md") == sha(BASE / "candidate/business_model.md"), name + ": candidate_body")
    for filename in ("knowledge_prompt.txt", "reviewer_expectations.json", "original_questions.json"):
        check(sha(batch / "input" / filename) == sha(PREVIOUS / "input" / filename), name + ": previous_" + filename)
    original = unique(read(batch / "input/original_questions.json")["cases"])
    controls = unique(read(batch / "input/controls.json")["cases"])
    previous_requests = unique(read(PREVIOUS / "input/requests.json")["requests"])
    for case_id, case in selected.items():
        check(case == original.get(case_id, controls.get(case_id)), name + ": original_metadata:" + case_id)
        check(requests[case_id] == previous_requests[case_id], name + ": exact_old_question:" + case_id)
    protected = read(batch / "input/protected.json")
    check(len(protected) == 12, name + ": 12_protected")
    for relative, digest in protected.items():
        check(sha(ROOT / relative) == digest, name + ": protected:" + relative)
    index_path = batch / "run_index.json"
    native_dirs = [p.parent for p in (ROOT / "artifacts/w02/knowledge_runs").glob("*/settings.json")
                   if read(p).get("config_path") == (batch / "input/knowledge.json").relative_to(ROOT).as_posix()]
    if not index_path.exists():
        check(not complete, name + ": required_run_index")
        return {"batch": name, "status": "pending_execution_or_recording", "native_started_count": len(native_dirs),
                "semantic_result": "not_assessed", "records": []}
    gate = read(batch / "gate_acceptance.json")
    check(gate["approved"] is True and gate["failed_checks"] == [], name + ": separate_execution_gate")
    for field, path in {"runner_sha256": RUNNER, "manifest_sha256": batch / "input/manifest.json",
                        "preflight_sha256": batch / "preflight.json",
                        "input_review_sha256": batch / gate["input_review"]}.items():
        check(sha(path) == gate[field], name + ": " + field)
    index = read(index_path)
    indexed = unique(index["cases"])
    output_paths = {p.stem: p for p in (batch / "output").glob("*.json") if "." not in p.stem}
    check(set(indexed) == set(output_paths), name + ": output_index_scope")
    check(len(indexed) == index["completed_case_records"], name + ": completed_count")
    if complete:
        check(set(indexed) == IDS[name] and len(native_dirs) == len(indexed), name + ": complete_unique_runs")
    review_path = batch / "independent-review/review.json"
    review = read(review_path) if review_path.exists() else None
    judged = unique(review["cases"]) if review else {}
    if complete:
        check(set(judged) == IDS[name], name + ": complete_independent_review")
    records = []
    for case_id, path in output_paths.items():
        output = read(path)
        run_path = ROOT / output["result"]["run"]
        run = read(run_path)
        check(sha(path) == indexed[case_id]["output_sha256"] and output["result"] == indexed[case_id]["result"],
              name + ": index_matches:" + case_id)
        check(run == output["native_run"] and sha(run_path) == output["native_run_sha256"], name + ": run_matches:" + case_id)
        for relative, digest in output["native_files"].items():
            check(sha(ROOT / relative) == digest, name + ": native:" + relative)
        check(output["gate_sha256"] == sha(batch / "gate_acceptance.json"), name + ": gate_bound:" + case_id)
        check(datetime.fromisoformat(gate["signed_at"]) <= datetime.fromisoformat(output["started_at"]),
              name + ": gate_precedes_run:" + case_id)
        request = read(run_path.parent / "request.json")
        settings = read(run_path.parent / "settings.json")
        user = json.loads(request["messages"][1]["content"])
        check(set(user) == {"business_model", "question"} and user["question"] == requests[case_id]["question"]
              and user["business_model"] == (batch / "input/business_model.md").read_text(),
              name + ": actual_input:" + case_id)
        check(settings["expected"] == "" and settings["question"] == user["question"] and not request.get("tools"),
              name + ": no_expected_or_tools:" + case_id)
        origins = unique(read(batch / "input/request_origins.json")["cases"])
        origin = origins[case_id]
        if "previous_request" in origin:
            old_path = ROOT / origin["previous_request"]
            check(sha(old_path) == origin["previous_request_sha256"], name + ": prior_request_hash:" + case_id)
            previous_request = read(old_path)
            check(request["messages"][0] == previous_request["messages"][0], name + ": unchanged_system_prompt:" + case_id)
            previous_user = json.loads(previous_request["messages"][1]["content"])
            check(user["question"] == previous_user["question"], name + ": unchanged_actual_question:" + case_id)
        attempts = read(run_path.parent / "attempts.json")["attempts"]
        check(1 <= len(attempts) <= 2, name + ": bounded_http:" + case_id)
        for number, attempt in enumerate(attempts):
            check(attempt["request"]["messages"] == request["messages"], name + ": attempt_inputs:" + case_id)
            check(attempt["max_tokens"] == (8192 if number == 0 else 16384), name + ": attempt_tokens:" + case_id)
            if number:
                check(attempts[0].get("finish_reason") == "length" and attempts[0].get("error") == "MODEL_OUTPUT_TRUNCATED",
                      name + ": native_truncation_expansion:" + case_id)
        partial = any(a.get("finish_reason") == "length" and bool(a.get("response", {}).get("content")) for a in attempts)
        final_response = (run_path.parent / "response.json").exists()
        answer = read(run_path.parent / "answer.json")["answer"] if run["status"] == "succeeded" else None
        check(answer == output["actual_answer"], name + ": actual_answer:" + case_id)
        classification = ("complete_answer" if answer is not None else
                          "partial_public_text_then_terminal_failure" if partial else
                          "no_public_response" if not final_response else "public_response_without_valid_answer")
        if name == "qa-01" and case_id == "U05":
            check(len(attempts) == 2 and attempts[0].get("finish_reason") == "length"
                  and attempts[1].get("error") == "MODEL_NETWORK_ERROR" and partial
                  and not final_response and answer is None, "qa01_U05_mixed_failure_not_pure_no_response")
        verdict = judged.get(case_id, {}).get("verdict", "pending_independent_review")
        if case_id in judged:
            item = judged[case_id]
            check(item["output_sha256"] == sha(path) and item["native_run_sha256"] == sha(run_path)
                  and item["actual_answer_sha256"] == (text_sha(answer) if answer is not None else None)
                  and item["http_attempts"] == len(attempts), name + ": review_evidence:" + case_id)
        records.append({"id": case_id, "run": ref(run_path), "output": ref(path), "verdict": verdict,
                        "native_status": run["status"], "http_attempts": len(attempts),
                        "response_classification": classification, "partial_public_response": partial,
                        "final_public_response": final_response, "accepted_answer": answer is not None})
    counts = {"native_runs": len(records), "http_attempts": sum(x["http_attempts"] for x in records),
              "native_answers": sum(x["accepted_answer"] for x in records),
              "semantic_passed": sum(x["verdict"] == "passed" for x in records),
              "semantic_failed": sum(x["verdict"] == "failed" for x in records),
              "semantic_not_assessable": sum(x["verdict"].startswith("not_assessable") for x in records),
              "semantic_pending": sum(x["verdict"] == "pending_independent_review" for x in records)}
    if review:
        for field in ("native_runs", "http_attempts", "semantic_passed", "semantic_failed", "semantic_not_assessable"):
            check(review["summary"][field] == counts[field], name + ": reviewed_count:" + field)
        check(review["model_sha256"] == sha(BASE / "candidate/business_model.md")
              and review["candidate_prompt_sha256"] == sha(PREVIOUS / "input/knowledge_prompt.txt"), name + ": reviewed_version")
    return {"batch": name, "status": "records_checked", "counts": counts, "records": records,
            "review": ref(review_path) if review else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    target = (HERE / args.output).resolve()
    check(target.parent == HERE and target.suffix == ".json", "new_report_inside_aggregate_only")
    baseline = read(BASE / "baseline_snapshot.json")
    check(len(baseline["files"]) == 268, "268_old_baseline_files")
    for relative, digest in baseline["files"].items():
        check(sha(ROOT / relative) == digest, "old_baseline_preserved:" + relative)
    preserved_qa1 = HERE / "qa01-preservation.json"
    if preserved_qa1.exists():
        for relative, digest in read(preserved_qa1)["files"].items():
            check(sha(ROOT / relative) == digest, "qa01_original_evidence_preserved:" + relative)
    scope = read(BASE / "scope.json")
    original = (ROOT / scope["original_model"]).read_text()
    for change in scope["changes"]:
        check(original.count(change["before"]) == 1, "single_candidate_change:" + change["before"][:35])
        original = original.replace(change["before"], change["after"], 1)
    check(len(scope["changes"]) == 3 and original == (BASE / "candidate/business_model.md").read_text(),
          "only_two_content_changes_plus_title")
    candidate_review = read(BASE / "independent-review/candidate-review.json")
    check(candidate_review["status"] == "source_review_pass" and candidate_review["failed_checks"] == []
          and candidate_review["blocking_findings"] == [], "source_review_pass_not_execution_approval")
    for field in ("candidate", "baseline", "source_criteria", "author_diff"):
        ref_item = candidate_review[field]
        check(sha(REPO / ref_item["path"]) == ref_item["sha256"], "source_review_bound:" + field)
    results = [inspect_batch(name, args.require_complete or name == "qa-01") for name in IDS]
    recovery = read(BASE / "qa-02-u05-recovery/recovery_basis.json")
    check(recovery["maximum_new_runs"] == 1 and recovery["maximum_http_attempts"] == 2
          and recovery["partial_response_sent_to_new_run"] is False
          and recovery["stop_after_this_new_run_even_if_failed"] is True, "bounded_separate_recovery")
    qa1_request = unique(read(BASE / "qa-01/input/requests.json")["requests"])["U05"]
    qa2_request = unique(read(BASE / "qa-02-u05-recovery/input/requests.json")["requests"])["U05"]
    check(qa1_request == qa2_request, "recovery_same_final_question_without_partial_response")
    check(sha(ROOT / recovery["original_failure"]) == recovery["original_failure_sha256"]
          and sha(ROOT / recovery["original_native_run"]) == recovery["original_native_run_sha256"],
          "original_mixed_failure_retained")
    before = read(BASE / "before-continuity/manifest.json")
    check(len(before["files"]) == 6, "six_before_continuity_files")
    for name, item in before["files"].items():
        check(sha(BASE / item["backup"]) == item["before_sha256"], "before_continuity_preserved:" + name)
    report = {"status": "mechanical_checks_passed", "recorded_at": datetime.now(timezone.utc).isoformat(),
              "batches": results, "checks": CHECKS, "failed_checks": [], "baseline_files_preserved": 268,
              "final_scope": {"original_cases": 5, "control_cases": 1, "other_82_originals_not_rerun": 77},
              "source_review": ref(BASE / "independent-review/candidate-review.json"),
              "old_baseline_snapshot": ref(BASE / "baseline_snapshot.json"),
              "verifier": ref(Path(__file__)), "reviewer_api_calls": 0, "final_package_approved": False,
              "limits": "Separate recovery counts do not erase qa01 partial-response failure. No whole-82 or causal/stability claim."}
    with target.open("x", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "check_count": len(CHECKS),
                      "batches": [{k: v for k, v in x.items() if k not in ("records", "review")} for x in results],
                      "reviewer_api_calls": 0}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
