"""Final aggregation only: hashes/counts/history, no model calls or rescoring."""
from copy import deepcopy
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[3]
REPO = ROOT.parents[1]
BATCH = BASE / "qa-01"
CHECKS = []


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(value, name):
    CHECKS.append({"id": name, "passed": bool(value)})
    if not value:
        raise ValueError(name)


def ref(path):
    return {"path": path.relative_to(REPO).as_posix(), "sha256": sha(path)}


ledger, completion, progress = [read(BASE / p) for p in ("execution_ledger.json", "completion.json", "progress.json")]
review_path = BATCH / "independent-review/review.json"
review = read(review_path)
protocol = read(BATCH / "protocol_audit.json")
cases = {c["id"]: c for c in ledger["cases"]}
judged = {c["id"]: c for c in review["cases"]}
indexed = {c["id"]: c for c in read(BATCH / "run_index.json")["cases"]}
requests = {c["id"]: c for c in read(BATCH / "input/requests.json")["requests"]}
ids = {"U05", "E01", "TRACECTRL01", "CTRL01", "U01", "P01"}
check(set(cases) == set(judged) == set(indexed) == set(requests) == ids, "six_case_sets_exact")
snapshot = read(BASE / "input-integrity/baseline_snapshot.json")
check(len(snapshot["files"]) == 270, "270_protected_snapshot_files")
for relative, digest in snapshot["files"].items():
    check(sha(ROOT / relative) == digest, "old_preserved:" + relative)
manifest = read(BATCH / "input/manifest.json")
for relative, digest in manifest["files"].items():
    check(sha(BATCH / relative) == digest, "frozen_input:" + relative)
protected = read(BATCH / "input/protected.json")
check(len(protected) == 12 and all(sha(ROOT / p) == h for p, h in protected.items()), "12_protected_unchanged")
gate = read(BATCH / "gate_acceptance.json")
check(gate["approved"] is True and gate["failed_checks"] == [], "execution_gate_approved")
for key, path in {"runner_sha256": BASE / "support/run_batch.py", "manifest_sha256": BATCH / "input/manifest.json",
                  "preflight_sha256": BATCH / "preflight.json",
                  "input_review_sha256": BATCH / gate["input_review"]}.items():
    check(sha(path) == gate[key], "gate:" + key)
native = []
for case_id, row in cases.items():
    output_path = BATCH / "output" / (case_id + ".json")
    output = read(output_path)
    run_path = ROOT / output["result"]["run"]
    run = read(run_path)
    check(sha(output_path) == row["output_sha256"] == judged[case_id]["output_sha256"] == indexed[case_id]["output_sha256"],
          case_id + ":output_hash")
    check(row["native_run"] == output["result"]["run"] and row["native_status"] == run["status"] and run == output["native_run"],
          case_id + ":native_result")
    for relative, digest in output["native_files"].items():
        check(sha(ROOT / relative) == digest, case_id + ":native_file:" + relative)
    check(row["passed"] == judged[case_id]["passed"] and row["verdict"] == judged[case_id]["status"],
          case_id + ":semantic_verdict_not_changed")
    check(row["review_sha256"] == judged[case_id]["review_sha256"]
          and sha(BATCH / "independent-review" / judged[case_id]["review"]) == judged[case_id]["review_sha256"],
          case_id + ":individual_review_hash")
    request = read(run_path.parent / "request.json")
    settings = read(run_path.parent / "settings.json")
    payload = json.loads(request["messages"][1]["content"])
    check(set(payload) == {"business_model", "question"} and payload["question"] == requests[case_id]["question"]
          and payload["business_model"] == (BATCH / "input/business_model.md").read_text()
          and settings["expected"] == "" and not request.get("tools"), case_id + ":exact_actual_input")
    attempts = read(run_path.parent / "attempts.json")["attempts"]
    check(len(attempts) == row["http_attempts"] and 1 <= len(attempts) <= 2, case_id + ":http_count")
    for attempt in attempts:
        check(attempt["request"]["messages"] == request["messages"], case_id + ":attempt_input_unchanged")
    if len(attempts) == 2:
        check(case_id in {"U05", "U01"} and attempts[0]["finish_reason"] == "length"
              and attempts[0]["error"] == "MODEL_OUTPUT_TRUNCATED", case_id + ":declared_native_expansion")
    answer_path = run_path.parent / "answer.json"
    answer = read(answer_path)["answer"] if answer_path.exists() else None
    check(answer == output["actual_answer"], case_id + ":actual_answer")
    if case_id == "P01":
        check(run["status"] == "failed" and run["error"]["code"] == "JSON_INVALID" and answer is None
              and (run_path.parent / "response.json").exists(), "P01_public_text_not_native_answer")
    native.append({"id": case_id, "run": ref(run_path), "output": ref(output_path),
                   "native_status": run["status"], "http_attempts": len(attempts), "passed": row["passed"]})
counts = {"selected": len(cases), "native_runs": len(native), "http_attempts": sum(x["http_attempts"] for x in native),
          "native_complete_answers": sum(x["native_status"] == "succeeded" for x in native),
          "overall_passed": sum(x["passed"] for x in native),
          "semantic_needs_revision": sum(not x["passed"] and x["native_status"] == "succeeded" for x in native),
          "protocol_failed": sum(x["native_status"] == "failed" for x in native)}
check(counts == ledger["counts"] == completion["counts"] == progress["counts"] == review["counts"],
      "6run_8HTTP_5answers_3pass_2semantic_1format_counts")
check(ledger["review_sha256"] == sha(review_path), "ledger_combined_review_hash")
check({x["id"] for x in native if x["passed"]} == {"E01", "TRACECTRL01", "CTRL01"}, "three_pass_ids")
check(protocol["audited_cases"] == 6 and protocol["http_attempts"] == 8 and protocol["successful_answers"] == 5
      and protocol["index_errors"] == [], "protocol_summary")
native_settings = [p for p in (ROOT / "artifacts/w02/knowledge_runs").glob("*/settings.json")
                   if read(p).get("config_path") == (BATCH / "input/knowledge.json").relative_to(ROOT).as_posix()]
check(len(native_settings) == 6 and len({x["run"]["path"] for x in native}) == 6, "no_extra_native_run")
check(ledger["original_cases"] == 4 and ledger["controls"] == 2
      and ledger["original_82_not_rerun_on_this_prompt"] == completion["original_82_not_rerun_on_this_prompt"] == 78,
      "four_original_two_controls_78_not_run")
check(ledger["mentor_corrections_are_native_passes"] is False and not completion["candidate_adopted"]
      and not completion["formal_model_applied"] and not completion["skill_replaced"]
      and completion["metric_queries_executed"] == 0, "not_adopted_and_static_not_native")
static_path = BASE / "independent-review/mentor-static-review.json"
static = read(static_path)
check(static["approved"] is True and len(static["checks"]) == 23 and all(x["passed"] for x in static["checks"])
      and not static["failed_checks"] and not static["new_model_execution_authorized"]
      and not static["current_native_verdict_changed"], "23_static_checks_only")
for relative, digest in static["reviewed_file_hashes"].items():
    check(sha(BASE / relative) == digest, "static_reviewed_file:" + relative)
check(static["current_native_review_sha256"] == sha(review_path), "static_binds_current_failed_verdicts")
for field, filename in {"ledger_sha256": "execution_ledger.json", "report_sha256": "验证结果.md",
                        "continuity_manifest_sha256": "continuity_manifest.json",
                        "source_review_sha256": "qa-01/independent-review/review.json",
                        "static_revision_review_sha256": "independent-review/mentor-static-review.json"}.items():
    check(completion[field] == sha(BASE / filename), "completion:" + field)
discrepancy_path = BATCH / "independent-review/expectation-discrepancy.json"
discrepancy = read(discrepancy_path)
check(sha(discrepancy_path) == review["expectation_discrepancy"]["sha256"]
      and sha(BATCH / "input/reviewer_expectations.json") == discrepancy["frozen_expectations_sha256"],
      "old_expectation_discrepancy_and_frozen_input_retained")
history = review["review_history"]
check((BATCH / "independent-review" / history["U05_initial_pass_retained"]).exists()
      and (BATCH / "independent-review" / history["U05_current"]).exists(), "initial_U05_review_and_r2_both_preserved")
revision = read(BASE / "expected-correction/revision.json")
old_expected = read(BATCH / "input/reviewer_expectations.json")
future_expected = read(BASE / "expected-correction/reviewer_expectations.json")
expected_copy = deepcopy(old_expected)
u05 = next(x for x in expected_copy["cases"] if x["id"] == "U05")
check(u05["required_points"][3] == revision["old"], "old_expected_clause")
u05["required_points"][3] = revision["new"]
check(expected_copy == future_expected and revision["frozen_batch_changed"] is False
      and revision["historical_grades_changed"] is False and revision["expected_was_sent_to_model"] is False,
      "one_future_expectation_field_no_old_edit_no_expected_input")
citation = read(BATCH / "independent-review/citation-audit.json")
check(citation["direct_or_source_phrase_occurrences"] == 44 and citation["raw_substring_matches"] == 41
      and len(citation["raw_nonmatches"]) == 3, "citation_counts_44_41_3_not_semantic_score")
before_manifest = read(BASE / "before-continuity/manifest.json")
changes = read(BASE / "continuity_manifest.json")["changes"]
check(len(changes) == len(before_manifest) == 6, "six_continuity_files")
diffs = []
for change in changes:
    name = change["path"]
    old_path = BASE / "before-continuity" / name
    current_path = REPO / name
    check(sha(old_path) == before_manifest[name] == change["before_sha256"]
          and sha(current_path) == change["after_sha256"], "continuity_hash:" + name)
    old, current = old_path.read_text(), current_path.read_text()
    check(current.count(change["inserted_text"]) == 1, "single_new_block:" + name)
    restored = current.replace(change["inserted_text"], "", 1)
    if change["historical_marker_only"]:
        restored = restored.replace("**正文澄清停点（2026-11-08，历史）：**", "**正文澄清停点（2026-11-08，最新）：**", 1)
    added_blank_after_title = name.endswith("W03-学习笔记.md") and restored == old.replace("# W03 学习笔记\n", "# W03 学习笔记\n\n", 1)
    check(restored == old or added_blank_after_title, "only_added_block_and_history_label:" + name)
    diffs.extend(difflib.unified_diff(old.splitlines(keepends=True), current.splitlines(keepends=True),
                                    fromfile="before/" + name, tofile="after/" + name))
with (HERE / "reviewed-continuity.diff").open("x", encoding="utf-8") as f:
    f.writelines(diffs)
with (HERE / "reviewed-completion.json").open("xb") as f:
    f.write((BASE / "completion.json").read_bytes())
files = ["execution_ledger.json", "completion.json", "progress.json", "验证结果.md", "README.md",
         "continuity_manifest.json", "qa-01/independent-review/review.json",
         "qa-01/independent-review/expectation-discrepancy.json", "independent-review/mentor-static-review.json"]
result = {"status": "passed", "recorded_at": datetime.now(timezone.utc).isoformat(), "checks": CHECKS,
          "failed_checks": [], "counts": counts, "native_records": native,
          "reviewed_files": [ref(BASE / p) for p in files], "verifier": ref(Path(__file__)),
          "reviewer_api_calls": 0, "semantic_rescoring_performed": False}
with (HERE / "mechanical-check.json").open("x", encoding="utf-8") as f:
    f.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": "passed", "check_count": len(CHECKS), "counts": counts, "reviewer_api_calls": 0},
                 ensure_ascii=False, indent=2))
