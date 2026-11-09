"""Reproduce comparator checks on immutable real-result copies; no API or DB.

Run from the workspace: python3 <this file> --report <metric_test_report.json>
The null example is explicitly synthetic because this metric is additive.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    judge_path = root / "customer/w03/judge.py"
    spec = importlib.util.spec_from_file_location("qinghe_judge", judge_path)
    judge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(judge)
    report = json.loads(args.report.read_text())
    cases = {x["id"]: x for x in report["cases"]}
    total = cases["NS01-aug-total"]
    grouped = cases["NS02-july-transaction-store"]
    assert judge.compare(total["expected"], total["actual"])["passed"]
    assert judge.compare(grouped["expected"], grouped["actual"])["passed"]
    records = []

    def run(name, case, mutate, want, kind="real_result_copy"):
        original = case["actual"]
        actual = copy.deepcopy(original)
        mutate(actual)
        result = judge.compare(case["expected"], actual)
        assert result["passed"] == want, (name, result)
        records.append({"id": name, "source_kind": kind,
                        "source_case": case["id"], "expected_passed": want,
                        "actual_comparison": result,
                        "original_result_unchanged": original == case["actual"]})

    run("correct_original", total, lambda a: None, True)
    run("row_order_only", grouped, lambda a: a["rows"].reverse(), True)
    def reorder_columns(a):
        a["columns"].reverse()
        a["rows"] = [list(reversed(r)) for r in a["rows"]]
    run("column_order_only", grouped, reorder_columns, True)
    run("wrong_date", total, lambda a: a["intent"].__setitem__("end", "2026-08-31"), False)
    run("wrong_metric", total, lambda a: a["intent"].__setitem__("metrics", ["paid_amount_cents"]), False)
    run("extra_filter", total, lambda a: a["intent"]["filters"].append(
        {"field": "store", "op": "eq", "value": "S01"}), False)
    run("wrong_unit", total, lambda a: a["units"].__setitem__("net_sales_cents", "yuan"), False)
    run("wrong_value_one_cent", total, lambda a: a["rows"][0].__setitem__(0, a["rows"][0][0] + 1), False)
    run("error_with_original_number", total, lambda a: a.__setitem__("status", "error"), False)
    run("wrong_data_version", total, lambda a: a.__setitem__("data_version", "synthetic-wrong-version"), False)
    run("missing_group", grouped, lambda a: a["rows"].pop(), False)
    run("duplicate_group", grouped, lambda a: a["rows"].append(a["rows"][0][:]), False)
    synthetic = copy.deepcopy(total)
    synthetic["id"] = "synthetic-null-comparator-only"
    synthetic["expected"]["rows"] = [[None]]
    synthetic["actual"]["rows"] = [[None]]
    run("null_replaced_by_zero", synthetic, lambda a: a.__setitem__("rows", [[0]]), False,
        "synthetic_null_contract_not_real_net_sales")
    result = {"status": "passed", "report": str(args.report),
              "report_sha256": hashlib.sha256(args.report.read_bytes()).hexdigest(),
              "judge_sha256": hashlib.sha256(judge_path.read_bytes()).hexdigest(),
              "checks": records, "total": len(records),
              "negative_checks": sum(not r["expected_passed"] for r in records),
              "negative_rejected": sum(not r["expected_passed"] and not r["actual_comparison"]["passed"] for r in records),
              "model_calls": 0, "queries": 0, "raw_results_modified": False}
    assert not args.output.exists(), "Use a new output; preserve prior evidence"
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "total", "negative_checks", "negative_rejected")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
