"""Check source-backed identities and targeted mutations of saved real-result copies."""
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
small_path, fixture_path, output = map(Path, sys.argv[1:4])
assert not output.exists()
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [small_path, fixture_path]}
reports = [json.loads(p.read_text()) for p in [small_path, fixture_path]]
assert all(r["complete"] and r["passed"] == r["total"] for r in reports)
spec = importlib.util.spec_from_file_location("b2_judge", ROOT / "customer/w03/judge.py")
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)
cases = {c["id"]: c for r in reports for c in r["cases"]}
identities = []
for case in cases.values():
    assert judge.compare(case["expected"], case["actual"])["passed"]
    if not case["id"].startswith("B2-"):
        continue
    for i, row in enumerate(case["actual"]["rows"]):
        v = dict(zip(case["actual"]["columns"], row))
        assert v["order_count"] == v["paid_order_count"] + v["cancelled_order_count"]
        assert v["refund_order_count"] == v["partial_refund_order_count"] + v["full_refund_order_count"]
        identities.append({"case": case["id"], "row": i, "creation_identity": True, "refund_identity": True})

controls = []
def check(name, cid, mutate, wanted):
    c = cases[cid]
    a = copy.deepcopy(c["actual"])
    mutate(a)
    got = judge.compare(c["expected"], a)
    assert got["passed"] == wanted, (name, got)
    controls.append({"id": name, "case": cid, "wanted": wanted, "comparison": got})

def swap_paid_valid(a):
    i, j = a["columns"].index("paid_order_count"), a["columns"].index("valid_order_count")
    assert a["rows"][0][i] != a["rows"][0][j]
    a["rows"][0][i], a["rows"][0][j] = a["rows"][0][j], a["rows"][0][i]

def remove_cancelled(a):
    i = a["columns"].index("order__status")
    before = len(a["rows"])
    a["rows"] = [r for r in a["rows"] if r[i] != "cancelled"]
    assert len(a["rows"]) == before - 1

fixture_id = next(c["id"] for c in reports[1]["cases"] if c["id"].startswith("B2-Z01"))
def falsely_full_refund(a):
    columns = {c: i for i, c in enumerate(a["columns"])}
    rows = [r for r in a["rows"] if r[columns["paid_order_count"]] == 1 and r[columns["valid_order_count"]] == 0 and r[columns["refund_order_count"]] == 0]
    assert len(rows) == 1
    assert rows[0][columns["full_refund_order_count"]] == 0
    rows[0][columns["full_refund_order_count"]] = 1

check("original_counts", "B2-N01", lambda a: None, True)
check("status_rows_reordered", "B2-D01", lambda a: a["rows"].reverse(), True)
check("paid_and_valid_swapped", "B2-N01", swap_paid_valid, False)
check("cancelled_group_omitted", "B2-D01", remove_cancelled, False)
check("zero_paid_falsely_full_refund", fixture_id, falsely_full_refund, False)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items())
result = {"status": "passed", "report_sha256": hashes,
          "judge_sha256": hashlib.sha256((ROOT / "customer/w03/judge.py").read_bytes()).hexdigest(),
          "B2_A01": {"kind": "auxiliary_after_independent_expected", "rows_checked": len(identities), "checks": identities},
          "controls": controls, "total": len(controls), "negative": 3,
          "model_calls": 0, "queries": 0, "original_results_unchanged": True}
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": "passed", "controls": len(controls), "identity_rows": len(identities)}))
