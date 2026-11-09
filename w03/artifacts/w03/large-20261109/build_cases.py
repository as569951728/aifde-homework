#!/usr/bin/env python3
"""由 large-expected.json 生成规模回归用例 tests-large.json。

期望全部来自 large_expected.py 的独立核算，不回填系统输出。
版本哈希先留空，首轮跑完由 actual 回填后再复验（judge 仅在 expected 含该键时比较）。
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
EXP = json.load(open(os.path.join(BASE, "large-expected.json"), encoding="utf-8"))

DATA_ID = "qinghe-w03-20260923-large"
DATA_SHA = EXP["orders_sha256"]

UNIT = {
    "order_count": "count", "paid_order_count": "count", "valid_order_count": "count",
    "cancelled_order_count": "count", "refund_order_count": "count",
    "partial_refund_order_count": "count", "full_refund_order_count": "count",
    "payment_cents": "cents", "refund_cents": "cents", "net_sales_cents": "cents",
    "gross_cents": "cents", "discount_cents": "cents",
    "buyer_count": "count", "refund_buyer_count": "count", "selling_store_count": "count",
    "valid_order_items": "count", "new_member_count": "count",
    "first_buyer_count": "count", "first_order_sales_cents": "cents",
    "first_order_count": "count", "repeat_order_count": "count",
    "monthly_buyer_count": "count", "monthly_repeat_buyer_count": "count",
    "monthly_repeat_rate": "ratio",
    "monthly_paid_buyer_count": "count", "monthly_paid_order_count": "count",
    "monthly_paid_sales_cents": "cents", "monthly_paid_repeat_buyer_count": "count",
    "monthly_paid_repeat_rate": "ratio", "monthly_paid_avg_order_value": "cents_per_order",
    "avg_order_value": "cents_per_order", "avg_buyer_value": "cents_per_member",
    "purchase_frequency": "orders_per_member", "refund_amount_rate": "ratio",
    "cancel_rate": "ratio", "refund_order_rate": "ratio", "discount_rate": "ratio",
    "items_per_order": "items_per_order",
}

SRC = ("独立核算：materials/data/large 原始 CSV 逐记录计算（脚本 artifacts/w03/large-20261109/large_expected.py，"
       "SHA256 orders.csv=%s）。口径来自 01_订单日报说明.md（金额/订单/有效/账户/件数）、02_财务邮件.md（八比率分子分母，零分母未定义）、"
       "03_会员运营周报.md（注册与观测期首购、月内复购≥2笔）、04_本期统计确认邮件.md（六项付费月报整月全店全渠道）、"
       "05_数据字典.md（一单一行、字段）、docs/w03/contract.md（半开区间）、docs/w03/B7-测试设计.md（月末资格）。"
       "有效订单=paid且实付减退款>0；比率用精确分数计算后转浮点，分母为零记 null；首购按账户全历史有效单排序（ordered_at, order_id）后判定首笔是否落窗。" % DATA_SHA)


def ok(cid, question, metrics, start, end, rows, group_by=None, filters=None, extra_src=""):
    return {
        "id": cid,
        "question": question,
        "expected": {
            "status": "ok",
            "intent": {"metrics": list(metrics), "start": start, "end": end,
                       "group_by": group_by or [], "filters": filters or []},
            "columns": (group_by or []) + list(metrics),
            "rows": rows,
            "units": {m: UNIT[m] for m in metrics},
            "data_version": DATA_ID,
            "data_sha256": DATA_SHA,
        },
        "expected_source": SRC + extra_src,
    }


def vals(bucket, keys):
    return [bucket[k] for k in keys]


cases = []
AUG = ("2026-08-01", "2026-09-01")
JUL = ("2026-07-01", "2026-08-01")
w8, w7 = EXP["window_2026-08"], EXP["window_2026-07"]

# 1 金额五项
keys = ["payment_cents", "refund_cents", "net_sales_cents", "gross_cents", "discount_cents"]
cases.append(ok("LG-B1", "请同时列出2026年8月青禾优选的实付金额、退款金额、净销售额、支付订单原价金额和优惠金额。",
                keys, *AUG, [vals(w8, keys)], extra_src=" 与 small 轮 B1-N01 同口径，规模数据独立重算。"))

# 2 订单数七项
keys = ["order_count", "paid_order_count", "valid_order_count", "cancelled_order_count",
        "refund_order_count", "partial_refund_order_count", "full_refund_order_count"]
cases.append(ok("LG-B2", "请同时列出2026年8月青禾优选的创建订单数、支付订单数、有效订单数、取消订单数、退款订单数、部分退款订单数和全额退款订单数。",
                keys, *AUG, [vals(w8, keys)], extra_src=" 恒等式：创建=支付+取消（%d=%d+%d）；退款=部分退+全退（%d=%d+%d）。" % (
                    w8["order_count"], w8["paid_order_count"], w8["cancelled_order_count"],
                    w8["refund_order_count"], w8["partial_refund_order_count"], w8["full_refund_order_count"])))

# 3 账户/门店/件数
keys = ["buyer_count", "refund_buyer_count", "selling_store_count", "valid_order_items"]
cases.append(ok("LG-B3", "请同时列出2026年8月青禾优选的购买会员数、退款会员数、成交门店数和有效订单商品件数。",
                keys, *AUG, [vals(w8, keys)]))

# 4 八项均值比率
keys = ["avg_order_value", "avg_buyer_value", "purchase_frequency", "refund_amount_rate",
        "cancel_rate", "refund_order_rate", "discount_rate", "items_per_order"]
cases.append(ok("LG-B4", "请同时列出2026年8月青禾优选的有效订单均额、购买会员人均消费、购买频次、退款金额占比、取消率、退款订单率、优惠率和单均商品件数。",
                keys, *AUG, [vals(w8, keys)], extra_src=" 比率在窗口内先聚合分子分母再相除，不取逐单或逐店比率的平均。"))

# 5 注册与观测期
k5 = EXP["b5_2026-08"]
keys = ["new_member_count", "first_buyer_count", "first_order_sales_cents", "first_order_count", "repeat_order_count"]
cases.append(ok("LG-B5", "请同时列出2026年8月青禾优选的注册会员数、观测期首购会员数、观测期首单净销售额、观测期首单数和观测期后续购买订单数。",
                keys, *AUG, [vals(k5, keys)], extra_src=" 该窗注册 0 人；首单数+后续单数=%d=%d。" % (
                    k5["first_order_count"] + k5["repeat_order_count"], w8["valid_order_count"])))

# 6 首购四种问法
keys = ["first_buyer_count", "first_order_sales_cents", "first_order_count", "repeat_order_count"]
cases.append(ok("LG-B5-h", "2026年8月青禾优选有多少会员是首次购买？他们的首单净销售额合计多少分、共几笔？此后这些账户又产生了多少笔有效订单？",
                keys, *AUG, [vals(k5, keys)], extra_src=" 与 LG-B5 同值不同问法；首购不代表终身首购。"))

# 7 月内购买与复购
m8 = EXP["monthly_2026-08"][0]
keys = ["monthly_buyer_count", "monthly_repeat_buyer_count", "monthly_repeat_rate"]
cases.append(ok("LG-B6", "请列出2026年8月青禾优选的月内购买会员数、月内复购会员数和月内复购率。",
                keys, *AUG, [m8[1:]], extra_src=" 复购=同月有效订单≥2笔的账户；复购率=复购人数/购买人数，分母 0 时为 null。"))

# 8 多月按月
mrows = [[r[0], *r[1:]] for r in (EXP["monthly_2026-07"] + EXP["monthly_2026-08"])]
mrows.sort(key=lambda r: r[0])
cases.append(ok("LG-B6-m", "请分别列出2026年7月和2026年8月青禾优选的月内购买会员数、月内复购会员数和月内复购率。",
                keys, "2026-07-01", "2026-09-01", mrows, group_by=["metric_time__month"],
                extra_src=" 多月按自然月分行，资格、账户与订单不跨月串用。"))

# 9 付费六项 8 月
keys6 = ["monthly_paid_buyer_count", "monthly_paid_order_count", "monthly_paid_sales_cents",
         "monthly_paid_repeat_buyer_count", "monthly_paid_repeat_rate", "monthly_paid_avg_order_value"]
p8, p7 = EXP["paid_2026-08"], EXP["paid_2026-07"]
cases.append(ok("LG-B7", "请同时列出2026年8月青禾优选的月末付费会员购买人数、月末付费会员有效订单数、月末付费会员净销售额、月末付费会员复购人数、月末付费会员复购率和月末付费会员订单均额。",
                keys6, *AUG, [vals(p8, keys6)], extra_src=" 月末资格按 2026-08-31 判定；先筛资格再连当月有效订单。"))

# 10 付费六项 7 月
cases.append(ok("LG-B7-jul", "2026年7月的月末付费会员六项月报指标分别是多少？",
                keys6, *JUL, [vals(p7, keys6)], extra_src=" 判定日为 2026-07-31，与 8 月独立重判。"))

# 11 按门店
cols = ["net_sales_cents", "valid_order_count", "buyer_count",
    "avg_order_value", "avg_buyer_value", "purchase_frequency", "refund_amount_rate",
    "cancel_rate", "refund_order_rate", "discount_rate", "items_per_order"]
cases.append(ok("LG-B4-store", "请按成交门店列出2026年8月青禾优选的净销售额、有效订单数、购买会员数和八项均值比率。",
                cols, *AUG, EXP["by_store_2026_08"], group_by=["store"],
                extra_src=" 每组独立聚合分子分母；门店来自 orders.store_id；24 家门店。"))

# 12 渠道筛选
mp = EXP["mini_program_2026_08"]
keys = ["net_sales_cents", "valid_order_count", "buyer_count"]
cases.append(ok("LG-B4-channel", "2026年8月青禾优选小程序渠道的净销售额、有效订单数和购买会员数是多少？",
                keys, *AUG, [vals(mp, keys)],
                filters=[{"field": "order__channel", "op": "eq", "value": "小程序"}],
                extra_src=" 渠道筛选取 orders.channel='小程序'；通用指标支持渠道过滤，六项付费月报不支持。"))

# 13 半月拒绝
cases.append({
    "id": "LG-X1",
    "question": "请列出2026年8月1日至8月15日青禾优选的月末付费会员购买人数和月末付费会员净销售额。",
    "expected": {"status": "unsupported"},
    "expected_source": "六项付费月报只支持完整自然月（04_本期统计确认邮件.md、docs/w03/contract.md）；半月窗口无法确定月末资格，应拒绝且不得截断计算或返回 0。",
})

# 14 付费按门店拒绝
cases.append({
    "id": "LG-X2",
    "question": "请将2026年8月青禾优选的月末付费会员购买人数按订单成交门店分别列出。",
    "expected": {"status": "unsupported"},
    "expected_source": "六项付费月报为全门店汇总口径，dimension_targets 未为其开放 store 维度；应拒绝，理由写口径或工具限制，不冒称客户政策。",
})

# 15 单指标另问法
cases.append(ok("LG-B1-b", "2026年8月青禾优选的净销售额（扣除退款后的实收金额）是多少分？",
                ["net_sales_cents"], *AUG, [[w8["net_sales_cents"]]],
                extra_src=" 与 LG-B1 同值不同问法，检验单指标识别与单位。"))

out = os.path.join(BASE, "tests-large.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(cases, fh, ensure_ascii=False, indent=2)
covered = set()
for c in cases:
    if c["expected"].get("status") == "ok":
        covered.update(c["expected"]["intent"]["metrics"])
print(json.dumps({"cases": len(cases), "ok_cases": sum(1 for c in cases if c['expected'].get('status') == 'ok'),
                  "distinct_metrics": len(covered), "written": out}, ensure_ascii=False))
