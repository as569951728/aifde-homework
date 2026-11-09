"""Final package cross-check. Writes only aggregate-review; zero model calls."""
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[3]
REPO = ROOT.parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


checks = []


def check(value, label):
    checks.append({"id": label, "passed": bool(value)})
    if not value:
        raise ValueError(label)


def ref(path):
    return {"path": path.relative_to(REPO).as_posix(), "sha256": sha(path)}


def new_json(name, data):
    with (HERE / name).open("x", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


integrity = read(HERE / "final-integrity-check.json")
check(integrity["status"] == "mechanical_checks_passed" and integrity["errors"] == [], "independent_integrity_passed")
ledger = read(BASE / "execution_ledger.json")
completion = read(BASE / "completion.json")
progress = read(BASE / "progress.json")
issues = read(BASE / "issue_matrix.json")
rows = ledger["executions"]
independent = {(s["stage"], c["id"]): c for s in integrity["stages"] for c in s["cases"]}
check(len(rows) == len(independent) == 105, "105_run_records")
check(len({(x["stage"], x["id"]) for x in rows}) == 105, "no_duplicate_stage_case")
check(len({x["native_run"] for x in rows}) == 105, "105_unique_native_runs")
for row in rows:
    key = (row["stage"], row["id"])
    native = independent[key]
    for left, right in (("verdict", "verdict"), ("native_status", "status"),
                        ("http_attempts", "http_attempts"), ("input_track", "input_track")):
        check(row[left] == native[right], ":".join((*key, left)))
    for field in ("output", "native_run", "review"):
        check(sha(ROOT / row[field]) == row[field + "_sha256"], ":".join((*key, field + "_hash")))
    batch = BASE / row["stage"]
    check(row["prompt_sha256"] == sha(batch / "input/knowledge_prompt.txt"), ":".join((*key, "prompt_hash")))
    check(row["model_sha256"] == sha(batch / "input/business_model.md"), ":".join((*key, "model_hash")))
all_questions = read(BASE / "stage5-compact-evidence/input/original_questions.json")["cases"]
original_ids = {x["id"] for x in all_questions if x["input_track"] != "artifact_review"}
check(len(original_ids) == 82, "82_original_qa_excludes_3_static_cases")
seen_original = {r["id"] for r in rows if r["id"] in original_ids}
seen_control = {r["id"] for r in rows if r["id"] not in original_ids}
for r in rows:
    check(r["case_origin"] == ("original_82" if r["id"] in original_ids else "independent_control"),
          r["stage"] + ":" + r["id"] + ":origin")
latest = [r for r in rows if r["stage"] == "stage5-compact-evidence"]
final_ids = {r["id"] for r in latest}
counts = {"native_runs": len(rows), "http_attempts": sum(r["http_attempts"] for r in rows),
          "successful_native_answers": sum(r["native_status"] == "succeeded" for r in rows),
          "unique_original_questions": len(seen_original), "unique_controls": len(seen_control),
          "all_run_verdicts": dict(Counter(r["verdict"] for r in rows)),
          "final_prompt_tests": len(latest), "final_prompt_original_questions": len(final_ids & original_ids),
          "final_prompt_independent_controls": len(final_ids - original_ids),
          "original_questions_not_rerun_on_final_prompt": len(original_ids - final_ids)}
check(counts == ledger["counts"] == completion["counts"], "ledger_completion_counts_exact")
check(counts["http_attempts"] == 107 and counts["successful_native_answers"] == 103
      and counts["unique_original_questions"] == 21 and counts["unique_controls"] == 8, "expected_totals")
check(set(ledger["final_prompt_untested_original_ids"]) == original_ids - final_ids
      and len(ledger["final_prompt_untested_original_ids"]) == 66, "66_final_unexecuted_originals_exact")
check(completion["latest"] == {"stage": "stage5-compact-evidence", "cases": 22, "passed": 21,
                             "semantic_failed_ids": ["U01"], "technical_no_answer_ids": []}, "latest_scope_and_failure")
closure = completion["failure_closure"]
baseline = read(ROOT / ledger["baseline_completion"])
check(sha(ROOT / ledger["baseline_completion"]) == ledger["baseline_completion_sha256"], "baseline_completion_preserved")
check(ledger["baseline_counts_unchanged"] == baseline["counts"], "baseline_71_of_82_unchanged")
old11 = set(baseline["counts"]["current_raw_failed_ids"])
check(len(old11) == 11 and {x["id"] for x in closure} == old11 | {"U04", "TRACECTRL01"}
      and len(closure) == 13, "13_historical_failure_closure_scope")
check(closure == ledger["failure_closure"], "ledger_completion_closure_exact")
last_by_id = {x["id"]: x for x in latest}
for item in closure:
    check(item["historical_failure_retained"] is True and item["evidence"] == last_by_id[item["id"]]
          and item["final_verdict"] == last_by_id[item["id"]]["verdict"], "closure:" + item["id"])
check(sum(last_by_id[i]["verdict"] == "passed" for i in old11) == 10, "10_of_11_original_failures_pass_latest")
check({x["id"] for x in issues["items"]} == {x["id"] for x in closure}, "issue_matrix_13_ids")
for item in issues["items"]:
    check(item["latest_observed_stage"] == "stage5-compact-evidence"
          and item["latest_observed_verdict"] == last_by_id[item["id"]]["verdict"]
          and item["regression_pass"] == (last_by_id[item["id"]]["verdict"] == "passed"), "issue:" + item["id"])
check(progress["actual_model_calls"] == 105 and progress["http_attempts"] == 107, "progress_totals")
for stage in integrity["stages"]:
    p = progress["stages"][stage["stage"]]
    c = stage["counts"]
    check(p.get("actual_calls", p.get("attempted")) == c["native_runs"] and p["native_answers"] == c["native_succeeded"]
          and p["semantic_pass"] == c["semantic_passed"] and p["semantic_fail"] == c["semantic_failed"],
          stage["stage"] + ":progress")
for name, count in integrity["cancelled_stage_native_counts"].items():
    check(count == 0 and progress["stages"][name]["actual_calls"] == 0 and name in ledger["unexecuted_batches"],
          name + ":zero_calls")
for key, filename in (("ledger_sha256", "execution_ledger.json"), ("report_sha256", "修复结果.md"),
                      ("continuity_manifest_sha256", "continuity_manifest.json")):
    check(completion[key] == sha(BASE / filename), "completion:" + key)
check(completion["result"] == "repair_not_fully_passed" and completion["formal_model_applied"] is False
      and completion["formal_prompt_or_skill_replaced"] is False and completion["metric_queries_executed"] == 0,
      "completion_not_overclaiming")
protected = read(BASE / "stage5-compact-evidence/input/protected.json")
check(len(protected) == 12 and all(sha(ROOT / p) == h for p, h in protected.items()), "12_protected_files_unchanged")
session_path = ROOT / "artifacts/w02/workflows/WF-8d2ebffec9d94a25bc164ae489fe13a0/session.json"
check(read(session_path)["status"] == "awaiting_apply", "workflow_still_awaiting_apply")
latest_review_path = BASE / "stage5-compact-evidence/independent-review/review.json"
latest_review = read(latest_review_path)
merged = {x["id"]: x for x in latest_review["cases"]}
reviewed_sets = []
for key in ("source_business_18", "numeric_date_format_4"):
    assignment = latest_review["review_assignment"][key]
    source = latest_review_path.parent / assignment["report"]
    check(sha(source) == assignment["sha256"], "stage5_split_review:" + key)
    sub = read(source)
    reviewed_sets.append({c["id"] for c in sub["cases"]})
    for c in sub["cases"]:
        check(c["verdict"] == merged[c["id"]]["verdict"] and c["output_sha256"] == merged[c["id"]]["output_sha256"],
              "merged_subreview:" + c["id"])
check(not (reviewed_sets[0] & reviewed_sets[1]) and reviewed_sets[0] | reviewed_sets[1] == final_ids,
      "18_plus_4_reviews_disjoint_complete")

continuity = read(BASE / "continuity_manifest.json")["files"]
before_manifest = read(BASE / "before-continuity/manifest.json")["files"]
check(len(continuity) == 6 and set(continuity) == set(before_manifest), "six_continuity_files")
continuity_details = []
diffs = []
for name, info in continuity.items():
    before_path = BASE / info["backup"]
    after_path = REPO / name
    check(info["before_sha256"] == before_manifest[name]["before_sha256"]
          and info["backup"] == before_manifest[name]["backup"]
          and sha(before_path) == info["before_sha256"] and sha(after_path) == info["after_sha256"],
          "continuity_hash:" + name)
    before = before_path.read_text()
    after = after_path.read_text()
    if name.endswith("W03-学习笔记.md"):
        removed = [before.splitlines()[i1:i2] for tag, i1, i2, j1, j2 in
                   difflib.SequenceMatcher(a=before.splitlines(), b=after.splitlines()).get_opcodes() if tag in ("replace", "delete")]
        preserved = removed == []
    else:
        start = after.index("**修复验证停点（2026-11-07，最新）：**")
        end = after.index("**全套验证停点（2026-11-07，历史）：**")
        restored = (after[:start] + after[end:]).replace("**全套验证停点（2026-11-07，历史）：**",
                                                      "**全套验证停点（2026-11-07，最新）：**", 1)
        preserved = restored == before
    check(preserved, "continuity_historical_content_exact:" + name)
    check("21通过、1语义失败、0技术无答" in after and "16道原题" in after and "6控制" in after,
          "continuity_current_result:" + name)
    continuity_details.append({"path": name, **info, "historical_content_preserved": True})
    diffs.extend(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                    fromfile="before/" + name, tofile="after/" + name))
with (HERE / "reviewed-continuity.diff").open("x", encoding="utf-8") as f:
    f.writelines(diffs)

metadata = read(BASE / "U01-correction-metadata.json")
correction_path = BASE / "U01-证据核对与待验证修订.md"
reviewed_draft_path = BASE / "progress-history/U01-correction-before-review.md"
correction_review_path = ROOT / metadata["independent_review"]
correction_review = read(correction_review_path)
check(correction_review["approved"] is True and len(correction_review["checks"]) == 15
      and all(x["passed"] is True for x in correction_review["checks"]) and correction_review["failed_checks"] == [],
      "mentor_15_static_checks_approved")
check(sha(correction_review_path) == metadata["independent_review_sha256"], "mentor_review_hash")
check(sha(correction_path) == metadata["draft_sha256"], "mentor_current_complete_draft_hash")
check(sha(reviewed_draft_path) == metadata["reviewed_original_draft_sha256"] == correction_review["reviewed_draft_sha256"],
      "mentor_reviewed_before_complete_draft_hash")
corrected = correction_path.read_text().split("## 导师核对稿（只替换两处，其余保持原答）\n\n", 1)[1].strip()
source_output = read(ROOT / metadata["source_output"])
check(sha(ROOT / metadata["source_output"]) == metadata["source_output_sha256"], "mentor_source_output_hash")
expected = source_output["actual_answer"]
for change in metadata["changes"]:
    check(expected.count(change["from"]) == 1, "mentor_exact_single_replacement:" + change["from"])
    expected = expected.replace(change["from"], change["to"], 1)
check(corrected == expected.strip() and text_sha(corrected) == metadata["corrected_answer_sha256"]
      == correction_review["reviewed_corrected_answer_sha256"], "mentor_exact_two_replacements_body_hash")
old_lines, new_lines = reviewed_draft_path.read_text().splitlines(), correction_path.read_text().splitlines()
check(len(old_lines) == len(new_lines) and all(a == b or (a.startswith("状态：") and b.startswith("状态："))
      for a, b in zip(old_lines, new_lines)), "mentor_postreview_only_status_line_changed")
check(metadata["is_model_output"] is False and metadata["model_calls"] == 0 and metadata["original_score_changed"] is False
      and metadata["changes_applied_to_formal_model"] is False and last_by_id["U01"]["verdict"] == "failed",
      "mentor_not_model_pass_or_apply")
for filename in ("completion.json", "progress.json"):
    with (HERE / ("reviewed-" + filename)).open("xb") as f:
        f.write((BASE / filename).read_bytes())
package_files = ["execution_ledger.json", "completion.json", "修复结果.md", "README.md", "progress.json", "issue_matrix.json",
                 "continuity_manifest.json", "before-continuity/manifest.json", "U01-correction-metadata.json",
                 "U01-证据核对与待验证修订.md", "progress-history/U01-correction-before-review.md"]
report = {"status": "passed", "recorded_at": datetime.now(timezone.utc).isoformat(), "checks": checks,
          "failed_checks": [], "counts": counts, "six_continuity_files": continuity_details,
          "reviewed_files": [ref(BASE / x) for x in package_files],
          "integrity_check": ref(HERE / "final-integrity-check.json"), "verifier": ref(Path(__file__)),
          "reviewer_api_calls": 0, "semantic_rescoring_performed": False,
          "scope": "Independent aggregation, hashes, preserved history and continuity; semantic verdicts remain the assigned independent reviewers' results."}
new_json("final-package-check.json", report)
print(json.dumps({"status": "passed", "check_count": len(checks), "counts": counts, "reviewer_api_calls": 0}, ensure_ascii=False, indent=2))
