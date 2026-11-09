"""Index native reports and check result copies. No model or database calls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
rd = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
paths = [B / "test-new-v1/metric_test_report.json", B / "test-regression-v1/metric_test_report.json"]
reports = [rd(p) for p in paths]
assert [r["total"] for r in reports] == [12, 21]
assert all(r["complete"] and r["passed"] == r["total"] for r in reports)
fixtures = rd(B / "test-fixture-v1/metric_test_report.json")
assert fixtures["complete"] and fixtures["passed"] == fixtures["total"] == 1
all_cases = [c for r in reports for c in r["cases"]]
expected = rd(B / "tests-small-all.json")
assert [c["id"] for c in all_cases] == [c["id"] for c in expected]
assert len({c["id"] for c in all_cases}) == 33
index = {"kind": "derived_index_of_unchanged_native_cases_not_a_new_run", "contract_version": "w03-0.1.0",
         "complete": True, "passed": 33, "total": 33,
         "source_native_reports": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in paths],
         "cases": all_cases, "new_model_calls": 0, "new_queries": 0}
out = B / "combined-small-report.json"
assert not out.exists()
out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
spec = importlib.util.spec_from_file_location("b34_judge", ROOT / "customer/w03/judge.py")
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)
case_map = {c["id"]: c for c in all_cases}
for c in all_cases + fixtures["cases"]:
    assert judge.compare(c["expected"], c["actual"])["passed"]
controls = []
def check(name, cid, metric, wrong_value=None):
    c = case_map[cid]
    a = copy.deepcopy(c["actual"])
    if wrong_value is not None:
        col = a["columns"].index(metric)
        assert a["rows"][0][col] != wrong_value
        a["rows"][0][col] = wrong_value
    got = judge.compare(c["expected"], a)
    wanted = wrong_value is None
    assert got["passed"] == wanted
    controls.append({"id": name, "case": cid, "expected_passed": wanted, "comparison": got})

# Wrong values independently identified in B3's original-CSV discrimination audit.
check("correct_B3_original", "B3-U01", "buyer_count")
check("order_count_misused_as_account_count", "B3-U01", "buyer_count", 39)
check("refund_orders_misused_as_accounts", "B3-U01", "refund_buyer_count", 6)
check("multi_card_join_inflates_items", "B3-N01", "valid_order_items", 42)
assert all(sha(p) == s["sha256"] for p, s in zip(paths, index["source_native_reports"]))
record = {"status": "passed", "total": 4, "negative_rejected": 3, "controls": controls,
          "wrong_values_source": "independent-b3/sample-and-scope.json and auxiliary ledgers",
          "original_native_reports_unchanged": True, "model_calls": 0, "queries": 0}
(B / "b3-result-controls.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"small": "33/33", "fixture": "1/1", "B3_controls": "4/4", "derived_index": True}))
