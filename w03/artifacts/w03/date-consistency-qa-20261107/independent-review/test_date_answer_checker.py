"""Offline synthetic positives/mutations; never represents actual model answers."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from check_date_answer import check_answer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = ROOT / "artifacts/w03/date-boundary-qa-20261106/independent-review"
QUESTIONS = ROOT / "artifacts/w03/model-input-preflight-20261106/effective_tests/model_questions.json"


def synthetic_reference(case, independent_case):
    """No use of the checker's expected-value function.

    Condition flags come from the previously frozen independent review artifact.
    Effective ends below are separately enumerated for the twelve fixture patterns.
    """
    f = case["fixture"]
    flags = independent_case["required_conditions"]
    end_by_number = {1: "2026-08-20", 2: "2026-08-20", 3: "2026-08-20", 4: "2026-08-20",
                     5: "2026-08-20", 6: "2026-08-20", 7: "2026-08-15", 8: "2026-08-15",
                     9: "2026-08-15", 10: "2026-08-20", 11: "2026-08-20", 12: "2026-08-15"}
    yes = lambda value: "是" if value else "否"
    conclusion = "有效" if independent_case["expected_valid_independently_derived"] else "无效"
    rows = [f"判定日：{f['decision_date']}", "产品范围：纳入", f"结论：{conclusion}", "",
            "| 检查项 | 题设日期 | 判定日是否满足本项条件 | 依据 |", "| --- | --- | --- | --- |",
            f"| 生效日 | {f['valid_from']} | {yes(flags['start_inclusive'])} | 生效当天包含，模型第3节规则3。 |",
            f"| 计划结束日 | {f['valid_until']} | {yes(flags['planned_end_exclusive'])} | 计划结束当天不含，模型第3节规则3。 |",
            f"| 提前终止日 | {f['ended_at'] or '空'} | {yes(flags['early_end_exclusive_or_absent'])} | 提前终止当天不含；空值仍受计划截止限制，模型第3节规则3。 |", "",
            "| 区间种类 | 起点 | 含起点 | 终点 | 含终点 |", "| --- | --- | --- | --- | --- |",
            f"| 计划区间 | {f['valid_from']} | 是 | {f['valid_until']} | 否 |",
            f"| 综合有效区间 | {f['valid_from']} | 是 | {end_by_number[int(case['id'][2:])]} | 否 |", "",
            "来源与范围：产品范围依据模型第3节规则1，小林MSG-03848、MSG-03854；日期依据规则3及陈姐MSG-03886、MSG-03888、MSG-03890。人工合成情境，正式文件和生产核验未完成。"]
    return "\n".join(rows)


def cell(answer, row_name, position, value):
    lines = answer.splitlines()
    matches = [i for i, line in enumerate(lines) if line.startswith("| " + row_name + " |")]
    assert len(matches) == 1
    i = matches[0]
    values = [x.strip() for x in lines[i].strip("|").split("|")]
    values[position] = value
    lines[i] = "| " + " | ".join(values) + " |"
    return "\n".join(lines)


def main():
    questions = {c["id"]: c for c in json.loads(QUESTIONS.read_text())["cases"] if c["id"].startswith(("DY", "DQ"))}
    independent = {c["id"]: c for c in json.loads((OLD / "source-first-criteria.json").read_text())["cases"]}
    references = {key: synthetic_reference(c, independent[key]) for key, c in questions.items()}
    tests = []

    def add(name, case_id, answer=None, status="pass", codes=(), category="synthetic_positive", fixture=None, semantic_expected=None):
        tests.append({"name": name, "case_id": case_id, "nature": "offline synthetic/reference mutation, not a new live model answer",
                      "category": category, "fixture": deepcopy(fixture or questions[case_id]["fixture"]),
                      "actual_answer": references[case_id] if answer is None else answer,
                      "expected_machine_status": status, "expected_error_codes": list(codes),
                      "separate_semantic_expected": semantic_expected})

    def neg(name, case_id, answer, codes, status="fail"):
        add(name, case_id, answer, status, codes, "deliberate_negative")

    for key in questions:
        add("reference_" + key, key)
    # Literal anchors: neither flags nor endpoints are obtained from either oracle.
    manual_dq12 = """判定日：2026-05-19
产品范围：纳入
结论：无效

| 检查项 | 题设日期 | 判定日是否满足本项条件 | 依据 |
| --- | --- | --- | --- |
| 生效日 | 2026-05-20 | 否 | 陈姐说明生效当天起有效；本日尚未生效。 |
| 计划结束日 | 2026-08-20 | 是 | 陈姐说明结束当天起无效；本日尚未到计划结束。 |
| 提前终止日 | 2026-08-15 | 是 | 陈姐说明提前终止当天起无效；本日尚未到终止。 |

| 区间种类 | 起点 | 含起点 | 终点 | 含终点 |
| --- | --- | --- | --- | --- |
| 计划区间 | 2026-05-20 | 是 | 2026-08-20 | 否 |
| 综合有效区间 | 2026-05-20 | 是 | 2026-08-15 | 否 |

来源与范围：小林说明家庭季卡在本期范围；陈姐提供日期执行口述。此为人工合成参考，正式文件和生产核验未完成。"""
    manual_dy02 = """判定日：2025-08-20
产品范围：纳入
结论：有效

| 检查项 | 题设日期 | 判定日是否满足本项条件 | 依据 |
| --- | --- | --- | --- |
| 生效日 | 2025-08-20 | 是 | 生效当天包含。 |
| 计划结束日 | 2026-08-20 | 是 | 计划结束当天不包含，本日未到。 |
| 提前终止日 | 空 | 是 | 无提前终止，仍受计划截止限制。 |

| 区间种类 | 起点 | 含起点 | 终点 | 含终点 |
| --- | --- | --- | --- | --- |
| 计划区间 | 2025-08-20 | 是 | 2026-08-20 | 否 |
| 综合有效区间 | 2025-08-20 | 是 | 2026-08-20 | 否 |

来源与范围：小林说明悦享年卡在本期范围；陈姐提供日期执行口述。人工合成参考，不是实际模型答复或生产结果。"""
    add("manual_literal_anchor_DQ12", "DQ12", manual_dq12)
    add("manual_literal_anchor_DY02", "DY02", manual_dy02)
    # Presentation normalization is deliberately limited to balanced wrappers/space.
    decorated = references["DY07"].replace("判定日：2026-08-14", "**判定日**：`2026-08-14`")
    decorated = cell(decorated, "生效日", 1, " `2025-08-20` ")
    decorated = cell(decorated, "生效日", 2, "**是**")
    add("presentation_wrappers", "DY07", decorated)
    add("fullwidth_table_pipes", "DQ12", references["DQ12"].replace("|", "｜"))
    tie_fixture = deepcopy(questions["DY07"]["fixture"])
    tie_fixture["ended_at"] = "2026-08-20"
    tie_answer = cell(references["DY07"], "提前终止日", 1, "2026-08-20")
    tie_answer = cell(tie_answer, "综合有效区间", 3, "2026-08-20")
    add("equal_termination_and_planned_end", "DY07", tie_answer, fixture=tie_fixture)
    neg("R2_DQ12_wrong_combined_end_correct_conclusion", "DQ12", cell(references["DQ12"], "综合有效区间", 3, "2026-08-20"), ["INTERVAL_MISMATCH"])
    neg("wrong_combined_start", "DY07", cell(references["DY07"], "综合有效区间", 1, "2025-08-21"), ["INTERVAL_MISMATCH"])
    neg("wrong_planned_end", "DY07", cell(references["DY07"], "计划区间", 3, "2026-08-15"), ["INTERVAL_MISMATCH"])
    for row in ("计划区间", "综合有效区间"):
        neg("exclusive_start_" + row, "DY02", cell(references["DY02"], row, 2, "否"), ["INTERVAL_MISMATCH"])
        neg("inclusive_end_" + row, "DY05", cell(references["DY05"], row, 4, "是"), ["INTERVAL_MISMATCH"])
    for row in ("生效日", "计划结束日", "提前终止日"):
        neg("flip_condition_" + row, "DY07", cell(references["DY07"], row, 2, "否"), ["CONDITION_MISMATCH"])
    neg("null_cannot_disable_plan_end", "DY05", cell(references["DY05"], "计划结束日", 2, "是"), ["CONDITION_MISMATCH"])
    neg("null_wrongly_has_termination", "DY11", cell(references["DY11"], "提前终止日", 1, "2026-08-15"), ["FIELD_MISMATCH"])
    neg("true_conclusion_flipped", "DY07", references["DY07"].replace("结论：有效", "结论：无效"), ["CONCLUSION_MISMATCH"])
    neg("false_conclusion_flipped", "DQ12", references["DQ12"].replace("结论：无效", "结论：有效"), ["CONCLUSION_MISMATCH"])
    # Self-consistent wrong start-day policy: condition, both intervals and result agree.
    coordinated = cell(references["DY02"], "生效日", 2, "否")
    coordinated = cell(coordinated, "计划区间", 2, "否")
    coordinated = cell(coordinated, "综合有效区间", 2, "否").replace("结论：有效", "结论：无效")
    neg("coordinated_internally_consistent_wrong_rule", "DY02", coordinated, ["CONDITION_MISMATCH", "INTERVAL_MISMATCH", "CONCLUSION_MISMATCH"])
    # Self-consistent whole-record substitution must not evade fixture identity checks.
    coordinated = references["DY11"].replace("判定日：2026-08-10", "判定日：2026-08-31").replace("结论：有效", "结论：无效")
    coordinated = cell(coordinated, "计划结束日", 2, "否")
    neg("coordinated_runtime_date_substitution", "DY11", coordinated, ["FIELD_MISMATCH", "CONDITION_MISMATCH", "CONCLUSION_MISMATCH"])
    neg("runtime_date_only", "DQ11", references["DQ11"].replace("判定日：2026-08-10", "判定日：2026-08-31"), ["FIELD_MISMATCH"])
    swapped = cell(references["DY12"], "计划区间", 3, "2026-08-15")
    swapped = cell(swapped, "综合有效区间", 3, "2026-08-20")
    neg("planned_effective_interchanged", "DY12", swapped, ["INTERVAL_MISMATCH"])
    for row in ("生效日", "计划结束日", "提前终止日"):
        neg("numeric_condition_" + row, "DY07", cell(references["DY07"], row, 2, "1"), ["INVALID_ENUM"])
    neg("numeric_endpoint", "DY07", cell(references["DY07"], "综合有效区间", 4, "0"), ["INVALID_ENUM"])
    neg("truth_prefix_not_enum", "DY07", cell(references["DY07"], "生效日", 2, "是，但尚待核实"), ["INVALID_ENUM"])
    neg("date_keyword_prefix_not_date", "DY07", cell(references["DY07"], "生效日", 1, "起于2025-08-20"), ["INVALID_DATE"])
    neg("unknown_condition", "DY07", cell(references["DY07"], "生效日", 2, "待核"), ["UNKNOWN_REQUIRED_VALUE"])
    neg("unknown_interval", "DY07", cell(references["DY07"], "综合有效区间", 3, "待核"), ["UNKNOWN_REQUIRED_VALUE"])
    neg("unknown_conclusion", "DY07", references["DY07"].replace("结论：有效", "结论：待核"), ["UNKNOWN_REQUIRED_VALUE"])
    neg("unknown_product", "DY07", references["DY07"].replace("产品范围：纳入", "产品范围：待核"), ["UNKNOWN_REQUIRED_VALUE"])
    neg("wrong_product_scope", "DY07", references["DY07"].replace("产品范围：纳入", "产品范围：排除"), ["PRODUCT_SCOPE_MISMATCH"])
    neg("invalid_calendar_date", "DY07", cell(references["DY07"], "生效日", 1, "2025-02-30"), ["INVALID_DATE"])
    missing = "\n".join(x for x in references["DY07"].splitlines() if not x.startswith("| 提前终止日 |"))
    neg("missing_row", "DY07", missing, ["MISSING_ROW"], "unparseable")
    duplicate_row = next(x for x in references["DY07"].splitlines() if x.startswith("| 提前终止日 |"))
    neg("duplicate_row", "DY07", references["DY07"].replace(duplicate_row, duplicate_row + "\n" + duplicate_row), ["DUPLICATE_ROW"], "unparseable")
    neg("duplicate_label", "DY07", "判定日：2026-08-14\n" + references["DY07"], ["DUPLICATE_LABEL"], "unparseable")
    neg("unknown_row", "DY07", references["DY07"].replace("| 生效日 |", "| 其他日期 |"), ["UNKNOWN_ROW", "MISSING_ROW"], "unparseable")
    neg("wrong_table_header", "DY07", references["DY07"].replace("判定日是否满足本项条件", "是否有效"), ["UNKNOWN_TABLE_HEADER"], "unparseable")
    neg("empty_basis", "DY07", cell(references["DY07"], "生效日", 3, ""), ["EMPTY_BASIS"], "unparseable")
    neg("unparsed_leading_text", "DY07", "这张卡无效。\n" + references["DY07"], ["UNPARSED_LINE"], "unparseable")
    neg("extra_object_before_source", "DY07", references["DY07"].replace("来源与范围：", '{"extra":true}\n来源与范围：'), ["UNPARSED_LINE"], "unparseable")
    old_actual = json.loads((ROOT / "artifacts/w03/date-boundary-qa-20261106-r2/output/DQ12.json").read_text())["actual_answer"]
    neg("unchanged_R2_old_natural_language", "DQ12", old_actual, ["MISSING_LABEL", "TABLE_COUNT"], "unparseable")
    # Deliberate limitation: structurally valid prose can be false. Never claim full pass.
    wrong_prose = cell(references["DY07"], "生效日", 3, "生效日当天无效，且IT已验证全部生产规则。")
    add("semantic_gate_wrong_basis", "DY07", wrong_prose, category="semantic_gate", semantic_expected="fail")
    add("semantic_gate_wrong_source_tail", "DY07", references["DY07"] + "\n实际有效窗口永久无限。", category="semantic_gate", semantic_expected="fail")

    results = []
    for test in tests:
        result = check_answer(test["actual_answer"], test["fixture"])
        codes = {x["code"] for x in result["errors"]}
        ok = result["machine_status"] == test["expected_machine_status"] and set(test["expected_error_codes"]) <= codes
        ok = ok and result["semantic_review_required"] is True and result["full_answer_pass"] is None
        results.append({"name": test["name"], "category": test["category"], "expected_status": test["expected_machine_status"],
                        "actual_status": result["machine_status"], "actual_error_codes": sorted(codes), "test_pass": ok,
                        "separate_semantic_expected": test["separate_semantic_expected"]})
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "nature": "offline checker validation only; no live model calls",
              "checker_sha256": hashlib.sha256((HERE / "check_date_answer.py").read_bytes()).hexdigest(),
              "test_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "external_expected_source_sha256": hashlib.sha256((OLD / "source-first-criteria.json").read_bytes()).hexdigest(),
              "total": len(tests), "passed": sum(x["test_pass"] for x in results), "failed": sum(not x["test_pass"] for x in results),
              "original_date_fixtures_positive": 24, "category_counts": {k: sum(x["category"] == k for x in tests) for k in {t["category"] for t in tests}},
              "semantic_limit_confirmed": "2 deliberately false prose examples machine-pass but require semantic failure; full_answer_pass is never True.",
              "results": results}
    (HERE / "checker-offline-cases.json").write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n")
    (HERE / "checker-selftest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, ensure_ascii=False))
    for result in results:
        if not result["test_pass"]:
            print(json.dumps(result, ensure_ascii=False))
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
