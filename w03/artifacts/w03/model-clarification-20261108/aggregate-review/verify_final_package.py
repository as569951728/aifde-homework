"""Final local package check; read-only outside aggregate-review, no API."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[3]
REPO = ROOT.parents[1]
checks = []


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(value, name):
    checks.append({"id": name, "passed": bool(value)})
    if not value:
        raise ValueError(name)


def ref(path):
    return {"path": path.relative_to(REPO).as_posix(), "sha256": sha(path)}


integrity = read(HERE / "final-integrity-check.json")
check(integrity["status"] == "mechanical_checks_passed" and not integrity["failed_checks"], "1059_integrity_checks_passed")
ledger = read(BASE / "execution_ledger.json")
completion = read(BASE / "completion.json")
progress = read(BASE / "progress.json")
independent = {(b["batch"], r["id"]): r for b in integrity["batches"] for r in b["records"]}
rows = ledger["executions"]
check(len(rows) == len(independent) == 7 and len({r["native_run"] for r in rows}) == 7, "seven_distinct_native_runs")
check(len({(r["stage"], r["id"]) for r in rows}) == 7, "no_duplicate_stage_case")
for row in rows:
    actual = independent[(row["stage"], row["id"])]
    check(row["verdict"] == actual["verdict"] and row["native_status"] == actual["native_status"]
          and row["http_attempts"] == actual["http_attempts"], row["stage"] + ":" + row["id"] + ":result")
    for field in ("output", "native_run", "review"):
        check(sha(ROOT / row[field]) == row[field + "_sha256"], row["stage"] + ":" + row["id"] + ":" + field)
current = ledger["current_case_results"]
check(len(current) == len({r["id"] for r in current}) == 6, "six_unique_cases")
check(all(r in rows for r in current), "current_rows_are_actual_evidence")
check({r["id"] for r in current if r["verdict"] == "failed"} == {"U05"}, "only_U05_current_failure")
check(all(r["stage"] == ("qa-02-u05-recovery" if r["id"] == "U05" else "qa-01") for r in current),
      "one_technical_recovery_not_best_of_selection")
counts = {
    "unique_cases": 6, "passed_cases": sum(r["verdict"] == "passed" for r in current),
    "unresolved_ids": [r["id"] for r in current if r["verdict"] != "passed"],
    "original_cases": sum(r["case_origin"] == "original_82" for r in current),
    "control_cases": sum(r["case_origin"] == "independent_control" for r in current),
    "native_runs": len(rows), "http_attempts": sum(r["http_attempts"] for r in rows),
    "successful_native_answers": sum(r["native_status"] == "succeeded" for r in rows),
    "original_82_not_rerun_on_new_body": 77,
    "tracks": {
      "model_only": {"cases": 4, "passed": 4, "unresolved_ids": []},
      "source_context_original": {"cases": 1, "passed": 0, "unresolved_ids": ["U05"]},
      "independent_control": {"cases": 1, "passed": 1, "unresolved_ids": []}}}
check(counts == ledger["counts"] == completion["counts"] == progress["counts"], "all_counts_synchronized")
check(counts["http_attempts"] == 8 and counts["successful_native_answers"] == 6 and counts["passed_cases"] == 5,
      "seven_runs_eight_HTTP_six_complete_answers_five_pass")
for track, predicate in (
    ("model_only", lambda r: r["input_track"] == "model_only"),
    ("source_context_original", lambda r: r["input_track"] == "model_with_source_context" and r["case_origin"] == "original_82"),
    ("independent_control", lambda r: r["case_origin"] == "independent_control")):
    subset = [r for r in current if predicate(r)]
    check(len(subset) == counts["tracks"][track]["cases"]
          and sum(r["verdict"] == "passed" for r in subset) == counts["tracks"][track]["passed"], track + ":disjoint_count")
mixed = independent[("qa-01", "U05")]
check(mixed["response_classification"] == "partial_public_text_then_terminal_failure" and mixed["http_attempts"] == 2
      and mixed["partial_public_response"] is True and mixed["final_public_response"] is False
      and mixed["verdict"] == "not_assessable_technical_failure" and ledger["original_qa01_U05_retained"],
      "qa01_mixed_failure_preserved_not_all_response_absent")
check(independent[("qa-02-u05-recovery", "U05")]["response_classification"] == "complete_answer"
      and independent[("qa-02-u05-recovery", "U05")]["verdict"] == "failed", "qa02_format_success_semantic_failure")
for item in ledger["stages"]:
    batch = BASE / item["stage"]
    review = read(batch / "independent-review/review.json")
    check(sha(batch / "independent-review/review.json") == item["review_sha256"]
          and sha(batch / "protocol_audit.json") == item["protocol_audit_sha256"]
          and item["summary"] == review["summary"], item["stage"] + ":review_summary")
for field, name in (("ledger_sha256", "execution_ledger.json"), ("report_sha256", "验证结果.md"),
                    ("continuity_manifest_sha256", "continuity_manifest.json")):
    check(completion[field] == sha(BASE / name), "completion:" + field)
check(completion["candidate_model_sha256"] == sha(BASE / "candidate/business_model.md")
      and completion["unchanged_prompt_sha256"] == sha(BASE / "qa-01/input/knowledge_prompt.txt"), "completion_version")
check(completion["formal_model_applied"] is False and completion["skill_replaced"] is False
      and completion["metric_queries_executed"] == 0 and progress["status"] == "results_recorded", "no_apply_or_overclaim")

continuity = read(BASE / "continuity_manifest.json")["files"]
before_manifest = read(BASE / "before-continuity/manifest.json")["files"]
check(len(continuity) == 6 and set(continuity) == set(before_manifest), "six_continuity_files")
diffs, continuity_evidence = [], []
for name, item in continuity.items():
    before_path, after_path = BASE / item["backup"], REPO / name
    check(item["before_sha256"] == before_manifest[name]["before_sha256"]
          and sha(before_path) == item["before_sha256"] and sha(after_path) == item["after_sha256"],
          "continuity_hash:" + name)
    before, after = before_path.read_text(), after_path.read_text()
    if name.endswith("W03-学习笔记.md"):
        preserved = all(tag not in ("delete", "replace") for tag, *_ in
                        difflib.SequenceMatcher(a=before.splitlines(), b=after.splitlines()).get_opcodes())
    else:
        start = after.index("**正文澄清停点（2026-11-08，最新）：**")
        end = after.index("**修复验证停点（2026-11-07，历史）：**")
        restored = (after[:start] + after[end:]).replace("**修复验证停点（2026-11-07，历史）：**",
                                                       "**修复验证停点（2026-11-07，最新）：**", 1)
        if name == "W03/W03-学习会话接续.md":
            check("2026-11-07 to 2026-11-08" in item["metadata_change"], "declared_update_date_change")
            restored = restored.replace("更新日期：2026-11-08。", "更新日期：2026-11-07。", 1)
        preserved = restored == before
    check(preserved, "historical_text_intact:" + name)
    check("5/6通过" in after, "current_result:" + name)
    continuity_evidence.append({"path": name, **item, "historical_content_preserved": True})
    diffs.extend(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                    fromfile="before/" + name, tofile="after/" + name))
with (HERE / "reviewed-continuity.diff").open("x", encoding="utf-8") as f:
    f.writelines(diffs)

metadata = read(BASE / "U05-correction-metadata.json")
correction_path = BASE / "U05-引用核对稿.md"
before_correction = BASE / "U05-引用核对稿-审核前状态.md"
review_path = ROOT / metadata["independent_review"]
review = read(review_path)
check(review["approved_static_working_copy"] and len(review["checks"]) == 16
      and all(c["passed"] is True for c in review["checks"]) and not review["failed_checks"], "mentor_16_static_checks")
check(sha(review_path) == metadata["independent_review_sha256"], "mentor_review_hash")
check(sha(correction_path) == metadata["draft_sha256"] and sha(before_correction) == metadata["reviewed_original_draft_sha256"]
      == review["reviewed_document_sha256"], "mentor_before_after_document_hash")
raw = read(ROOT / metadata["source_output"])
check(sha(ROOT / metadata["source_output"]) == metadata["source_output_sha256"], "mentor_raw_output_hash")
corrected = correction_path.read_text().split("## 导师修订全文（仅替换上述两处）\n\n", 1)[1].strip()
expected = raw["actual_answer"]
for change in metadata["changes"]:
    check(expected.count(change["before"]) == 1, "mentor_unique_change:" + change["before"][:30])
    expected = expected.replace(change["before"], change["after"], 1)
check(corrected == expected.strip() and hashlib.sha256(corrected.encode()).hexdigest() ==
      metadata["corrected_answer_sha256"] == review["corrected_answer_sha256"], "mentor_body_exact_two_changes")
for message_id, item in metadata["sources"].items():
    source = ROOT / item["source"]
    messages = read(source)["messages"]
    matching = [m for m in messages if message_id in m.values()]
    check(sha(source) == item["source_sha256"] and len(matching) == 1
          and matching[0]["content"] == item["content"], "mentor_source_content:" + message_id)
old_lines, current_lines = before_correction.read_text().splitlines(), correction_path.read_text().splitlines()
check(len(old_lines) == len(current_lines) and all(a == b or (a.startswith("状态：") and b.startswith("状态："))
      for a, b in zip(old_lines, current_lines)), "mentor_only_status_updated_after_review")
check(metadata["is_model_output"] is False and metadata["new_model_calls"] == 0 and metadata["original_grade_changed"] is False,
      "mentor_not_new_model_answer_or_score")
files = ["execution_ledger.json", "completion.json", "progress.json", "验证结果.md", "README.md", "变更说明.md",
         "continuity_manifest.json", "U05-correction-metadata.json", "U05-引用核对稿.md", "U05-引用核对稿-审核前状态.md"]
with (HERE / "reviewed-completion.json").open("xb") as f:
    f.write((BASE / "completion.json").read_bytes())
report = {"status": "passed", "recorded_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "failed_checks": [],
          "counts": counts, "continuity": continuity_evidence, "reviewed_files": [ref(BASE / x) for x in files],
          "integrity_check": ref(HERE / "final-integrity-check.json"), "verifier": ref(Path(__file__)),
          "reviewer_api_calls": 0, "semantic_rescoring_performed": False}
with (HERE / "final-package-check.json").open("x", encoding="utf-8") as f:
    f.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": "passed", "check_count": len(checks), "counts": counts, "reviewer_api_calls": 0},
                 ensure_ascii=False, indent=2))
