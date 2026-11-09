"""Check B1 identities and mutate real-result copies; never call a model or DB."""
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
report_path, output_path = map(Path, sys.argv[1:3])
before_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
report = json.loads(report_path.read_text())
assert report["complete"] and report["passed"] == report["total"] == 15
cases = {c["id"]: c for c in report["cases"]}
spec = importlib.util.spec_from_file_location("b1_judge", ROOT / "customer/w03/judge.py")
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)
identities, mutations = [], []
for case in report["cases"]:
    if not case["id"].startswith("B1-"):
        continue
    assert judge.compare(case["expected"], case["actual"])["passed"]
    actual = case["actual"]
    for i, row in enumerate(actual["rows"]):
        values = dict(zip(actual["columns"], row))
        one = values["payment_cents"] - values["refund_cents"] == values["net_sales_cents"]
        two = values["gross_cents"] - values["payment_cents"] == values["discount_cents"]
        assert one and two, (case["id"], i, values)
        identities.append({"case": case["id"], "row": i, "net_identity": one, "discount_identity": two})

def check(name, case_id, mutate, wanted):
    c = cases[case_id]
    a = copy.deepcopy(c["actual"])
    mutate(a)
    got = judge.compare(c["expected"], a)
    assert got["passed"] == wanted, (name, got)
    mutations.append({"id": name, "case": case_id, "expected_passed": wanted, "comparison": got})

def reorder(a):
    a["columns"].reverse()
    a["rows"] = [list(reversed(row)) for row in a["rows"]]

def omit_column(a):
    i = a["columns"].index("gross_cents")
    a["columns"].pop(i)
    for row in a["rows"]:
        row.pop(i)

def swap_values(a):
    i, j = a["columns"].index("payment_cents"), a["columns"].index("refund_cents")
    assert a["rows"][0][i] != a["rows"][0][j]
    a["rows"][0][i], a["rows"][0][j] = a["rows"][0][j], a["rows"][0][i]

def one_cent(a):
    i = a["columns"].index("discount_cents")
    a["rows"][0][i] += 1

check("multi_original", "B1-N01", lambda a: None, True)
check("multi_columns_reordered_with_values", "B1-N01", reorder, True)
check("multi_omit_one_column", "B1-N01", omit_column, False)
check("multi_swap_amount_values", "B1-N01", swap_values, False)
check("multi_one_metric_unit_wrong", "B1-N01", lambda a: a["units"].__setitem__("payment_cents", "yuan"), False)
check("multi_one_cell_wrong", "B1-N01", one_cent, False)
check("multi_extra_metric", "B1-N01", lambda a: a["intent"]["metrics"].append("paid_order_count"), False)
check("multi_omit_one_AND_filter", "B1-F01", lambda a: a["intent"]["filters"].pop(), False)
assert hashlib.sha256(report_path.read_bytes()).hexdigest() == before_hash
assert not output_path.exists(), "Keep earlier evidence"
out = {"status": "passed", "report_sha256": before_hash,
       "judge_sha256": hashlib.sha256((ROOT / "customer/w03/judge.py").read_bytes()).hexdigest(),
       "B1_A01": {"kind": "auxiliary_not_independent_expected", "rows_checked": len(identities), "checks": identities},
       "multi_metric_controls": {"total": len(mutations), "negative": sum(not c["expected_passed"] for c in mutations), "checks": mutations},
       "model_calls": 0, "queries": 0, "original_report_unchanged": True}
output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": "passed", "identity_rows": len(identities), "multi_controls": len(mutations)}, ensure_ascii=False))
