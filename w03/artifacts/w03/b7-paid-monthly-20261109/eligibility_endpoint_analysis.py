"""B7 月末资格端点区分力分析（不调用模型、不依赖构建库）。

目的：判断 small 数据本身能否区分“月末资格”的四个端点条件。
做法：用独立实现按规则逐月算六项，再从基准规则逐一翻转一个端点，比较六项是否变化。
若翻转后数值不变，说明该端点在这份数据上无区分力，必须另造人工样本才能证明实现正确。

基准规则（与 Skill v0.1.5、library-v38 的 member_month_paid_eligibility.sql 一致）：
  单卡有效 = card_type in ('悦享年卡','家庭季卡')
           and valid_from <= 月末
           and 月末 < valid_until
           and (ended_at is null or 月末 < ended_at)
  账户资格 = 任一卡同时满足以上全部条件（条件不跨卡拼接）
  订单窗口 = 自然月整月；有效订单 = status=paid 且 paid_cents-refund_cents>0
  六项 = 有资格的账户中有有效订单的人数 / 其有效订单数 / 其净额 / 其中 >=2 单的人数 / 复购率 / 订单均额
  分母为零：复购率、均额返回 None（null），人数/单数/金额为 0
"""
import csv
import json
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "..", "..", "materials", "data", "small")

PAID_TYPES = ("悦享年卡", "家庭季卡")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def month_end(month_start):
    """下月 1 号减一天。"""
    y, m = month_start[:4], int(month_start[5:7])
    y, m = (int(y) + 1, 1) if m == 12 else (int(y), m + 1)
    import datetime
    return (datetime.date(y, m, 1) - datetime.timedelta(days=1)).isoformat()


def month_start_of(day):
    return day[:7] + "-01"


REAL = dict(type_ok=True, from_le=True, until_lt=True, ended_lt=True)


def eligible(cards, member, month_start, rule):
    end = month_end(month_start)
    for c in cards:
        if c["member_id"] != member:
            continue
        if rule["type_ok"] and c["card_type"] not in PAID_TYPES:
            continue
        if rule["from_le"]:
            if not (c["valid_from"] <= end):
                continue
        elif not (c["valid_from"] < end):
            continue
        if rule["until_lt"]:
            if not (end < c["valid_until"]):
                continue
        elif not (end <= c["valid_until"]):
            continue
        if c["ended_at"]:
            if rule["ended_lt"]:
                if not (end < c["ended_at"]):
                    continue
            elif not (end <= c["ended_at"]):
                continue
        return True
    return False


def compute(orders, cards, rule, months=None):
    agg = defaultdict(lambda: {"count": 0, "net": 0})
    for o in orders:
        if o["status"] != "paid":
            continue
        net = int(o["paid_cents"]) - int(o["refund_cents"])
        if net <= 0:
            continue
        ms = month_start_of(o["ordered_at"])
        key = (o["member_id"], ms)
        agg[key]["count"] += 1
        agg[key]["net"] += net
    by_month = defaultdict(lambda: {"buyers": 0, "orders": 0, "net": 0, "repeat": 0})
    for (member, ms), v in agg.items():
        if months and ms not in months:
            continue
        if not eligible(cards, member, ms, rule):
            continue
        m = by_month[ms]
        m["buyers"] += 1
        m["orders"] += v["count"]
        m["net"] += v["net"]
        if v["count"] >= 2:
            m["repeat"] += 1
    out = {}
    for ms, m in sorted(by_month.items()):
        repeat_rate = round(m["repeat"] / m["buyers"], 12) if m["buyers"] else None
        avg = round(m["net"] / m["orders"], 6) if m["orders"] else None
        out[ms] = [m["buyers"], m["orders"], m["net"], m["repeat"], repeat_rate, avg]
    return out


def main():
    orders = load("orders.csv")
    cards = load("cards.csv")
    base = compute(orders, cards, REAL)
    flips = {
        "valid_from 改为不含当天（<）": dict(REAL, from_le=False),
        "valid_until 改为含当天（<=）": dict(REAL, until_lt=False),
        "ended_at 改为含当天（<=）": dict(REAL, ended_lt=False),
        "卡产品不限（含联名卡/体验卡）": dict(REAL, type_ok=False),
    }
    report = {"base_rule": REAL, "months": base, "sensitivity": {}}
    for name, rule in flips.items():
        alt = compute(orders, cards, rule)
        changed = {ms: {"base": base[ms], "flipped": alt.get(ms)} for ms in base if alt.get(ms) != base[ms]}
        report["sensitivity"][name] = {"changed_months": sorted(changed), "detail": changed}
    # 逐卡端点清单：说明数据里有哪些端点实例
    rows = []
    for c in cards:
        rows.append({
            "card": c["card_id"], "member": c["member_id"], "type": c["card_type"],
            "from": c["valid_from"], "until": c["valid_until"], "ended": c["ended_at"] or None,
            "type_in_scope": c["card_type"] in PAID_TYPES,
            "note": "月末当天生效" if c["valid_from"].endswith(("-08-31", "-07-31", "-06-30")) else "",
        })
    report["cards"] = rows
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
