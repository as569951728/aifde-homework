#!/usr/bin/env python3
"""Independent CSV audit. No generated library, SQL, actual result, API or keys read."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = ROOT / "materials/data/small"
METRIC = "net_sales_cents"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main():
    manifest = json.loads((DATA / "manifest.json").read_text())
    for name, expected_hash in manifest["sha256"].items():
        assert digest(DATA / name) == expected_hash, f"CSV snapshot changed: {name}"
    orders = read_csv("orders.csv")
    members = {row["member_id"]: row for row in read_csv("members.csv")}
    stores = {row["store_id"]: row for row in read_csv("stores.csv")}
    assert len(orders) == manifest["counts"]["orders"] == 48
    assert len({row["order_id"] for row in orders}) == len(orders)
    for row in orders:
        for field in ["gross_cents", "paid_cents", "refund_cents", "quantity"]:
            row[field] = int(row[field])
        assert row["member_id"] in members and row["store_id"] in stores
        assert 0 <= row["refund_cents"] <= row["paid_cents"]
        assert row["status"] in {"paid", "cancelled"}
    specs = [
        ("NS01-aug-total", "2026年8月青禾优选净销售额是多少？", "2026-08-01", "2026-09-01", [], []),
        ("NS02-july-transaction-store", "2026年7月青禾优选净销售额按订单成交门店编号分别列出。", "2026-07-01", "2026-08-01", ["store"], []),
        ("NS03-aug-mini-program", "2026年8月青禾优选小程序渠道的净销售额是多少？", "2026-08-01", "2026-09-01", [], [{"field": "order__channel", "op": "eq", "value": "小程序"}]),
        ("NS04-partial-refund-day", "2026年8月15日当天青禾优选净销售额是多少？", "2026-08-15", "2026-08-16", [], []),
        ("NS05-full-refund-day", "2026年8月10日当天青禾优选净销售额是多少？", "2026-08-10", "2026-08-11", [], []),
        ("NS06-covered-empty", "2026年6月1日至6月29日（含首尾两天）青禾优选净销售额是多少？", "2026-06-01", "2026-06-30", [], []),
    ]
    cases, ledger, summaries = [], [], []
    for case_id, question, start, end, groups, filters in specs:
        amounts = defaultdict(int)
        if not groups:
            amounts[()] = 0
        included = []
        matching_paid = matching_refunds = 0
        for order in orders:
            reason = "计入 paid 实付减累计退款"
            if not start <= order["ordered_at"] < end:
                reason = "排除：下单日期不在半开区间"
            elif filters and order["channel"] != filters[0]["value"]:
                reason = "排除：渠道不匹配"
            elif order["status"] != "paid":
                reason = "排除：cancelled"
            accepted = reason.startswith("计入")
            contribution = order["paid_cents"] - order["refund_cents"] if accepted else 0
            key = (order["store_id"],) if groups else ()
            if accepted:
                amounts[key] += contribution
                matching_paid += order["paid_cents"]
                matching_refunds += order["refund_cents"]
                included.append(order["order_id"])
            ledger.append({"case_id": case_id, **order, "home_store_id": members[order["member_id"]]["home_store_id"], "included": accepted, "reason": reason, "contribution_cents": contribution})
        rows = [list(key) + [amount] for key, amount in sorted(amounts.items())]
        expected = {"status": "ok", "intent": {"metrics": [METRIC], "start": start, "end": end, "group_by": groups, "filters": filters}, "columns": groups + [METRIC], "rows": rows, "units": {METRIC: "cents"}, "data_version": manifest["id"]}
        source = f"独立 CSV 核算；materials/w03/01_订单日报说明.md 净销售额及 02_财务邮件.md，05_数据字典.md 的成交门店/日期/金额字段；数据 {manifest['id']}，orders.csv SHA256={manifest['sha256']['orders.csv']}；Asia/Shanghai [{start},{end})，paid 实付 {matching_paid} 分减累计退款 {matching_refunds} 分={matching_paid - matching_refunds} 分；分组/筛选以 intent 为准。逐单纳入/排除原因见 artifacts/w03/net-sales-first-20261108/independent/order-ledger.csv 的 {case_id}，复算脚本同目录 calculate_expected.py。"
        cases.append({"id": case_id, "question": question, "expected": expected, "expected_source": source})
        summaries.append({"id": case_id, "rows": rows, "paid_cents": matching_paid, "refund_cents": matching_refunds, "total_cents": matching_paid - matching_refunds, "included_order_ids": included})
    cases.extend([
        {"id": "NS07-missing-time", "question": "青禾优选净销售额是多少？", "expected": {"status": "clarify"}, "expected_source": "docs/w03/test-guide.md §3.3 及 product/w03_intent_prompt.txt：没有必要日期且无会话上下文须澄清；不猜参考月，不比较成功结果字段。"},
        {"id": "NS08-outside-coverage", "question": "2026年9月青禾优选净销售额是多少？", "expected": {"status": "unsupported"}, "expected_source": "materials/data/small/manifest.json、materials/w03/05_数据字典.md：覆盖 [2024-09-01,2026-09-01)，2026年9月不在覆盖内；02_财务邮件.md 明确覆盖外不是零；docs/w03/contract.md 的不支持状态。"},
    ])
    july_home = defaultdict(int)
    for order in orders:
        if "2026-07-01" <= order["ordered_at"] < "2026-08-01" and order["status"] == "paid":
            july_home[members[order["member_id"]]["home_store_id"]] += order["paid_cents"] - order["refund_cents"]
    # Independent small-table calibration, read from raw rows before any generation.
    assert summaries[1]["rows"] == [["S01", 12500], ["S02", 10000], ["S03", 9000]]
    assert summaries[3]["included_order_ids"] == ["O0000003"] and summaries[3]["total_cents"] == 7000
    assert summaries[4]["included_order_ids"] == ["O0000004"] and summaries[4]["total_cents"] == 0
    assert summaries[5]["included_order_ids"] == [] and summaries[5]["total_cents"] == 0
    write_json("tests.json", cases)
    write_json("calculation-summary.json", {"data_version": manifest["id"], "cases": summaries, "wrong_role_july_home_store_comparison": dict(sorted(july_home.items()))})
    with (HERE / "order-ledger.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(ledger[0]))
        writer.writeheader()
        writer.writerows(ledger)
    inputs = ["materials/w03/01_订单日报说明.md", "materials/w03/02_财务邮件.md", "materials/w03/05_数据字典.md", "materials/data/small/manifest.json", "materials/data/small/orders.csv", "materials/data/small/members.csv", "materials/data/small/stores.csv", "docs/w03/contract.md", "docs/w03/test-guide.md", "customer/w03/dimension_targets.json", "product/w03_intent_prompt.txt", "platform/fde_product/metrics/engine.py"]
    write_json("expected-freeze.json", {"independence": "Business expectations derived solely from original materials and Python standard csv, before reading candidate Skill/judge, generated metrics/SQL or actual query results. Framework read only for contract shape.", "inputs": {name: digest(ROOT / name) for name in inputs}, "outputs": {name: digest(HERE / name) for name in ["calculate_expected.py", "tests.json", "calculation-summary.json", "order-ledger.csv"]}})
    print(json.dumps({"count": len(cases), "expectations": summaries, "wrong_role": dict(sorted(july_home.items()))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
