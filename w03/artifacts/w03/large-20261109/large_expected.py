#!/usr/bin/env python3
"""W03 规模数据（large）独立期望核算。只读原始 CSV 与业务材料，不读构建库、SQL 或实际结果。

口径来源：
  materials/w03/01_订单日报说明.md   金额、订单数、有效订单、购买账户、件数
  materials/w03/02_财务邮件.md       八项比率的分子分母、零分母未定义
  materials/w03/03_会员运营周报.md   注册、观测期首购、月内购买与复购
  materials/w03/04_本期统计确认邮件.md 六项月末付费会员月报、整月与全门店全渠道
  materials/w03/05_数据字典.md       订单粒度、字段、覆盖
  docs/w03/contract.md              半开区间、意图字段
  docs/w03/B7-测试设计.md            月末资格判定

判定口径（与 small 轮一致）：
  paid      = status == 'paid'
  valid     = paid 且 paid_cents - refund_cents > 0
  refunded  = paid 且 refund_cents > 0
  cancelled = status == 'cancelled'
  比率一律 Fraction 精确计算后再转 float；分母为零记 null，不记 0。
  首购：按账户全历史有效单排序（ordered_at, order_id），首笔落在窗口内即首购。
  月末资格：card_type ∈ {悦享年卡, 家庭季卡}；valid_from ≤ 月末；月末 < valid_until；
             ended_at 为空或 月末 < ended_at；任一张卡满足即可，不跨卡拼条件。
"""
import csv
import datetime
import hashlib
import json
import os
from collections import defaultdict
from fractions import Fraction

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
DATA = os.path.join(ROOT, "materials", "data", "large")
SMALL_MANIFEST = os.path.join(ROOT, "materials", "data", "small", "manifest.json")

PAID_TYPES = ("悦享年卡", "家庭季卡")
RATIO_DEFS = {
    "avg_order_value": ("net_sales_cents", "valid_order_count", "cents_per_order"),
    "avg_buyer_value": ("net_sales_cents", "buyer_count", "cents_per_member"),
    "purchase_frequency": ("valid_order_count", "buyer_count", "orders_per_member"),
    "refund_amount_rate": ("refund_cents", "payment_cents", "ratio"),
    "cancel_rate": ("cancelled_order_count", "order_count", "ratio"),
    "refund_order_rate": ("refund_order_count", "paid_order_count", "ratio"),
    "discount_rate": ("discount_cents", "gross_cents", "ratio"),
    "items_per_order": ("valid_order_items", "valid_order_count", "items_per_order"),
}


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def month_end(ms):
    y, m = int(ms[:4]), int(ms[5:7])
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return (datetime.date(y, m, 1) - datetime.timedelta(days=1)).isoformat()


def components(orders):
    paid = [o for o in orders if o["status"] == "paid"]
    valid = [o for o in paid if o["paid_cents"] > o["refund_cents"]]
    refunded = [o for o in paid if o["refund_cents"] > 0]
    cancelled = [o for o in orders if o["status"] == "cancelled"]
    v = {
        "order_count": len(orders),
        "paid_order_count": len(paid),
        "valid_order_count": len(valid),
        "cancelled_order_count": len(cancelled),
        "refund_order_count": len(refunded),
        "partial_refund_order_count": len([o for o in paid if 0 < o["refund_cents"] < o["paid_cents"]]),
        "full_refund_order_count": len([o for o in paid if o["refund_cents"] > 0 and o["refund_cents"] >= o["paid_cents"]]),
        "payment_cents": sum(o["paid_cents"] for o in paid),
        "refund_cents": sum(o["refund_cents"] for o in paid),
        "net_sales_cents": sum(o["paid_cents"] - o["refund_cents"] for o in paid),
        "gross_cents": sum(o["gross_cents"] for o in paid),
        "discount_cents": sum(o["gross_cents"] - o["paid_cents"] for o in paid),
        "buyer_count": len({o["member_id"] for o in valid}),
        "refund_buyer_count": len({o["member_id"] for o in refunded}),
        "selling_store_count": len({o["store_id"] for o in valid}),
        "valid_order_items": sum(o["quantity"] for o in valid),
    }
    return v, {"valid": len(valid)}


def ratios(v):
    out = {}
    for name, (num, den, unit) in RATIO_DEFS.items():
        f = Fraction(v[num], v[den]) if v[den] else None
        out[name] = (float(f) if f is not None else None, unit, str(f) if f is not None else None,
                     v[num], v[den])
    return out


def paid_eligible(cards_by_member, member, ms):
    end = month_end(ms)
    for c in cards_by_member.get(member, ()):
        if c["card_type"] not in PAID_TYPES:
            continue
        if not (c["valid_from"] <= end):
            continue
        if not (end < c["valid_until"]):
            continue
        if c["ended_at"] and not (end < c["ended_at"]):
            continue
        return True
    return False


def main():
    orders = load("orders.csv")
    cards = load("cards.csv")
    members = load("members.csv")
    for o in orders:
        for k in ("gross_cents", "paid_cents", "refund_cents", "quantity"):
            o[k] = int(o[k])
    orders.sort(key=lambda o: (o["member_id"], o["ordered_at"], o["order_id"]))
    cards_by_member = defaultdict(list)
    for c in cards:
        cards_by_member[c["member_id"]].append(c)

    # 每账户全历史有效单序列（首购判定用）
    member_valid = defaultdict(list)
    for o in orders:
        if o["status"] == "paid" and o["paid_cents"] - o["refund_cents"] > 0:
            member_valid[o["member_id"]].append(o)

    def window(rows, start, end, channel=None):
        sel = [o for o in rows if start <= o["ordered_at"] < end]
        if channel:
            sel = [o for o in sel if o["channel"] == channel]
        return sel

    def metrics_for(orders_sel, start, end):
        """通用 24 项 + 月内 3 项的窗口口径（非月内指标也按整窗算）。"""
        v, _ = components(orders_sel)
        r = ratios(v)
        out = dict(v)
        for k, (val, _u, _f, _n, _d) in r.items():
            out[k] = val
        return out

    def b5_for(start, end):
        win = [o for o in orders
               if o["status"] == "paid" and o["paid_cents"] - o["refund_cents"] > 0
               and start <= o["ordered_at"] < end]
        first_ids, repeat = set(), 0
        for m, seq in member_valid.items():
            for idx, o in enumerate(seq):
                if start <= o["ordered_at"] < end:
                    if idx == 0:
                        first_ids.add(o["order_id"])
                    else:
                        repeat += 1
        first_orders = [o for o in win if o["order_id"] in first_ids]
        return {
            "first_buyer_count": len({o["member_id"] for o in first_orders}),
            "first_order_sales_cents": sum(o["paid_cents"] - o["refund_cents"] for o in first_orders),
            "first_order_count": len(first_orders),
            "repeat_order_count": repeat,
            "new_member_count": len([m for m in members if start <= m["registered_at"] < end]),
        }

    def monthly_for(start, end):
        """按自然月分组：月内购买会员数、复购会员数、复购率。"""
        by_month = defaultdict(lambda: defaultdict(int))
        for o in orders:
            if o["status"] != "paid" or o["paid_cents"] - o["refund_cents"] <= 0:
                continue
            if not (start <= o["ordered_at"] < end):
                continue
            by_month[o["ordered_at"][:7] + "-01"][o["member_id"]] += 1
        rows = []
        for ms in sorted(by_month):
            buyers = by_month[ms]
            repeat = len([m for m, n in buyers.items() if n >= 2])
            rate = Fraction(repeat, len(buyers)) if buyers else None
            rows.append([f"{ms} 00:00:00", len(buyers), repeat, float(rate) if rate is not None else None])
        return rows

    def paid_monthly(ms):
        """六项月末付费会员月报：单月。"""
        v = {"monthly_paid_buyer_count": 0, "monthly_paid_order_count": 0,
             "monthly_paid_sales_cents": 0, "monthly_paid_repeat_buyer_count": 0}
        per_member = defaultdict(lambda: [0, 0])
        for o in orders:
            if o["status"] != "paid" or o["paid_cents"] - o["refund_cents"] <= 0:
                continue
            if o["ordered_at"][:7] + "-01" != ms:
                continue
            if not paid_eligible(cards_by_member, o["member_id"], ms):
                continue
            per_member[o["member_id"]][0] += 1
            per_member[o["member_id"]][1] += o["paid_cents"] - o["refund_cents"]
        for m, (n, net) in per_member.items():
            v["monthly_paid_buyer_count"] += 1
            v["monthly_paid_order_count"] += n
            v["monthly_paid_sales_cents"] += net
            if n >= 2:
                v["monthly_paid_repeat_buyer_count"] += 1
        rr = Fraction(v["monthly_paid_repeat_buyer_count"], v["monthly_paid_buyer_count"]) if v["monthly_paid_buyer_count"] else None
        av = Fraction(v["monthly_paid_sales_cents"], v["monthly_paid_order_count"]) if v["monthly_paid_order_count"] else None
        v["monthly_paid_repeat_rate"] = float(rr) if rr is not None else None
        v["monthly_paid_avg_order_value"] = float(av) if av is not None else None
        return v

    AUG = ("2026-08-01", "2026-09-01")
    JUL = ("2026-07-01", "2026-08-01")

    def sha(name):
        with open(os.path.join(DATA, name), "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()

    data_sha = sha("orders.csv")
    report = {"data_dir": DATA, "orders_sha256": data_sha, "counts": {
        "orders": len(orders), "members": len(members), "cards": len(cards)}}

    # 通用窗口指标
    for tag, (start, end) in [("2026-08", AUG), ("2026-07", JUL)]:
        sel = window(orders, start, end)
        report[f"window_{tag}"] = metrics_for(sel, start, end)
        report[f"b5_{tag}"] = b5_for(start, end)
        report[f"monthly_{tag}"] = monthly_for(start, end)
        report[f"paid_{tag}"] = paid_monthly(start)

    # 空月：找一个无有效单的完整月
    months_with = {o["ordered_at"][:7] for o in orders if o["status"] == "paid" and o["paid_cents"] - o["refund_cents"] > 0}
    empty = None
    cur = datetime.date(2024, 9, 1)
    while cur < datetime.date(2026, 9, 1):
        key = cur.isoformat()[:7]
        if key not in months_with:
            empty = key + "-01"
            break
        cur = (cur.replace(day=28) + datetime.timedelta(days=7)).replace(day=1)
    report["empty_month"] = empty
    if empty:
        report["paid_empty"] = paid_monthly(empty)
        report["b5_empty"] = b5_for(empty, month_end(empty)[:8] + "01") if False else None

    # 按门店分组（8 项比率 + 金额）
    sel = window(orders, *AUG)
    by_store = defaultdict(list)
    for o in sel:
        by_store[o["store_id"]].append(o)
    store_rows = []
    for s in sorted(by_store):
        v, _ = components(by_store[s])
        r = ratios(v)
        row = [s] + [v["net_sales_cents"], v["valid_order_count"], v["buyer_count"]] + [r[k][0] for k in RATIO_DEFS]
        store_rows.append(row)
    report["by_store_2026_08"] = store_rows

    # 渠道筛选（小程序）
    mp = [o for o in sel if o["channel"] == "小程序"]
    report["mini_program_2026_08"] = metrics_for(mp, *AUG)

    report["generated_by"] = "large_expected.py"
    out = os.path.join(BASE, "large-expected.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: report[k] for k in ("counts", "empty_month")}, ensure_ascii=False))
    print("written", out)


if __name__ == "__main__":
    main()
