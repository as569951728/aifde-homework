"""Build a planning register from existing source plans; never compute test answers."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "artifacts/w03/metric-batch-plan-20261108"
OLD = ROOT / "artifacts/w03/full-test-design-20261106/v2"
FIRST = ROOT / "artifacts/w03/net-sales-first-20261108"
load = lambda p: json.loads(p.read_text())
targets = load(ROOT / "customer/w03/targets.json")
old = {c["id"]: c for c in load(OLD / "metric_coverage_plan.json")["cases"]}
names = {c["id"]: c["name"] for c in targets}
groups = [
    ("B1", "订单金额", ["payment_cents", "refund_cents", "net_sales_cents", "gross_cents", "discount_cents"]),
    ("B2", "订单数量", ["order_count", "paid_order_count", "valid_order_count", "cancelled_order_count", "refund_order_count", "partial_refund_order_count", "full_refund_order_count"]),
    ("B3", "账户去重、门店与件数", ["buyer_count", "refund_buyer_count", "selling_store_count", "valid_order_items"]),
    ("B4", "均值与比率", ["avg_order_value", "avg_buyer_value", "purchase_frequency", "refund_amount_rate", "cancel_rate", "refund_order_rate", "discount_rate", "items_per_order"]),
    ("B5", "注册与观测期首购／后续购买", ["new_member_count", "first_buyer_count", "first_order_sales_cents", "first_order_count", "repeat_order_count"]),
    ("B6", "普通月内购买与复购", ["monthly_buyer_count", "monthly_repeat_buyer_count", "monthly_repeat_rate"]),
    ("B7", "月末付费会员月报", ["monthly_paid_buyer_count", "monthly_paid_order_count", "monthly_paid_sales_cents", "monthly_paid_repeat_buyer_count", "monthly_paid_repeat_rate", "monthly_paid_avg_order_value"]),
]
dependencies = {
    "avg_order_value": ["net_sales_cents", "valid_order_count"],
    "avg_buyer_value": ["net_sales_cents", "buyer_count"],
    "purchase_frequency": ["valid_order_count", "buyer_count"],
    "refund_amount_rate": ["refund_cents", "payment_cents"],
    "cancel_rate": ["cancelled_order_count", "order_count"],
    "refund_order_rate": ["refund_order_count", "paid_order_count"],
    "discount_rate": ["discount_cents", "gross_cents"],
    "items_per_order": ["valid_order_items", "valid_order_count"],
    "monthly_repeat_rate": ["monthly_repeat_buyer_count", "monthly_buyer_count"],
    "monthly_paid_repeat_rate": ["monthly_paid_repeat_buyer_count", "monthly_paid_buyer_count"],
    "monthly_paid_avg_order_value": ["monthly_paid_sales_cents", "monthly_paid_order_count"],
}
cases = []
batches = []
for bid, label, metrics in groups:
    batch = {"id": bid, "name": label, "new_scope_metric_ids": metrics,
             "status": "next_batch" if bid == "B1" else "queued",
             "already_small_passed": [m for m in metrics if m == "net_sales_cents"],
             "metric_dependencies": {m: dependencies[m] for m in metrics if m in dependencies}}
    closure = set(metrics)
    while True:
        expanded = closure | {d for m in closure for d in dependencies.get(m, [])}
        if expanded == closure:
            break
        closure = expanded
    batch["primary_metric_dependency_closure"] = [t["id"] for t in targets if t["id"] in closure]
    batch["default_build_strategy"] = "累计已核范围+本批，一次重新生成新库；不merge各批不一致的同名模型"
    batches.append(batch)
    q = "请同时列出2026年8月青禾优选的" + "、".join(names[m] for m in metrics) + "。"
    cases.append({"id": bid + "-N01", "batch": bid, "metric_ids": metrics,
                  "kind": "normal_multi_metric", "question_or_fixture": q,
                  "expected_behavior": "逐项按其来源定义独立核算；统一窗口不等于各指标使用同一日期字段、分母或行集合；核每列值与单位。",
                  "fault_to_detect": "漏指标、交换列、套用同一口径、金额/人数/比率单位混用"})

def add(bid, suffix, title, rule, fault, metrics=None, kind="query_scenario"):
    ms = metrics or next(g[2] for g in groups if g[0] == bid)
    cases.append({"id": bid + "-" + suffix, "batch": bid, "metric_ids": ms,
                  "kind": kind, "question_or_fixture": title,
                  "expected_behavior": rule, "fault_to_detect": fault})

add("B1", "R01", "同时查2026年8月10日的实付、退款、净销售额、原价和优惠金额。", "全退paid仍计原实付/原价/原优惠，退款扣入净额；取消不计；按原订单日。", "把所有金额均过滤为有效单，或退款冲减优惠")
add("B1", "R02", "同时查2026年8月15日的上述五项金额。", "部分退款仅按相应指标扣减；逐单列gross、paid、refund及净额。", "实付提前扣退款、净额重复扣退、分元混用")
add("B1", "D01", "2026年7月五项金额按订单成交门店编号分别列出。", "各组独立核算；成交店不得换成归属店，不能只核总额。", "门店角色错、缺组、多组、重复组")
add("B1", "F01", "2026年8月小程序渠道、成交地区为华东的五项金额是多少？", "按原始订单及门店关系做AND过滤；冻结实际地区/渠道值。", "漏一项筛选、把AND当OR、错误归属地区")
add("B1", "Z01", "2026年6月1日至29日（含首尾）的五项金额是多少？", "覆盖内空窗的金额加总为0；不含6月30日，不把空窗当无覆盖。", "零/未知混用、结束日偏移")
add("B1", "D02", "2026年8月五项金额逐日列出。", "按ordered_at归日；先核实际返回日集合及每项值，不凭空补无返回的分组。", "按退款发生日归属、日期组错位")
add("B1", "A01", "辅助交叉检查：同窗口/筛选/分组比较实付－退款＝净额，原价－实付＝优惠。", "每项先有独立原CSV期望，再做恒等式辅助检查；恒等式不是独立期望的替代。", "多指标整体算错却仍满足关系", kind="cross_metric_assertion")

add("B2", "R01", "2026年8月10日的七项订单数量分别是多少？", "全退paid仍是支付单，不是有效单；正实付且全退才计全退；取消与退款分开。", "全退当取消或漏支付单")
add("B2", "R02", "2026年8月15日的七项订单数量分别是多少？", "部分退保留有效性，同时计退款/部分退款；边界均按整数比较。", "部分退款当无效、两端误含")
add("B2", "D01", "2026年8月按订单状态分别列七项订单数量。", "创建单包含取消；其他指标按各自状态与金额条件，保留分组身份。", "对全部指标预先筛paid，或取消金额0导致漏计订单")
add("B2", "Z01", "隔离边界例：paid记录分别为0实付0退款、正实付0退款、部分退、全退，并有取消单。", "零实付paid计支付不计有效/退款/全退；其余条件逐条核；先找原样本，缺例另建fixture。", "0=0被误认全退；边界<=和<错误", kind="fixture_design")
add("B2", "D02", "查询2026年6月30日至7月1日（含首尾）的七项订单数量，按日列出。", "查询协议[6月30日,7月2日)，逐日计唯一order_id；同额订单不能合并。", "少一天、重复订单或sum distinct金额误当订单数")
add("B2", "A01", "辅助检查：创建单＝支付单＋取消单；退款单＝部分退单＋全退单。", "先独立核所有分量；关系适用当前字典paid/cancelled及退款边界，不能替代各值校验。", "分支遗漏及重复计数", kind="cross_metric_assertion")

add("B3", "D01", "2026年7月购买会员、退款会员、成交门店和有效订单件数按成交门店分别列出。", "按组建立账户/门店集合；同账户可出现在不同组，整体去重不能简单加组人数。", "把去重数当可加指标、成交与归属角色混用")
add("B3", "R01", "2026年8月15日购买会员数、退款会员数、成交门店数和有效订单商品件数是多少？", "部分退款有效单使用原quantity，不能从金额推退货件数。", "净件数猜测、退款账户遗漏")
add("B3", "R02", "2026年8月10日上述四项指标是多少？", "全退单不产生购买账户/有效件数/有效成交店，但可产生退款账户。", "四项共用同一个成员集合")
add("B3", "U01", "隔离边界例：一个账户多次有效购买、多次退款并持多卡；另一个账户的订单金额相同。", "账户按member_id去重，订单金额相同不合并；卡不参与这些四项的筛选或放大。", "多卡/多单重复计人，误作跨系统自然人去重", kind="fixture_design")
add("B3", "F01", "2026年8月小程序渠道上述四项指标是多少？", "先按允许的订单筛选，再分别去重和加件；不是全库账户数。", "去重先于窗口/筛选导致群体错误")

add("B4", "Z01", "2026年6月1日至29日（含首尾）的八项均值和比率是多少？", "逐项独立分子分母；分母0为null，不是0，不是unsupported。", "除零给0、整数除法截断")
add("B4", "R01", "2026年8月10日的八项均值和比率是多少？", "全退日各分母不同，不能一律给null或一律给0；保存每个分子分母。", "统一分母、支付单和有效单混用")
add("B4", "D01", "2026年7月八项均值和比率按成交门店列出，同时核全店整体。", "各组和整体均先聚合分子分母再除；整体不平均门店比率。", "平均平均数、平均比率、去重分母相加")
add("B4", "F01", "2026年8月小程序渠道八项均值和比率是多少？", "分子分母使用一致窗口及筛选，但分别遵守其行集合规则。", "只过滤分子，或把有效订单过滤套到paid分母")
add("B4", "U01", "核正常八指标回答：金额均值、单/账户、件/单与无量纲比率的展示。", "按契约单位逐项核；金额分转元，比例展示百分数只影响文字；浮点容差在运行前固定。", "比例乘100后冒充原值、单位列互换", kind="answer_and_numeric_review")

add("B5", "D01", "2026年8月注册会员数按会员归属门店、会员等级列出。", "按registered_at计账户，未购买的注册账户仍计，不用ordered_at或成交店。", "把注册人数当购买人数，错误日期或门店角色", ["new_member_count"])
add("B5", "H01", "2026年8月观测期首购人数、首单金额、首单数和后续购买单数是多少？", "先在全覆盖有效订单中按账户排序，再筛8月；不能在8月重新找第一笔。", "窗口首单冒充观测期首单", groups[4][2][1:])
add("B5", "H02", "隔离排序例：同账户首条记录取消或全退，其后同一天有两笔有效订单。", "跳过无效单；有效单同日按order_id排序；首单1笔，其余进入后续。", "取创建首单、时间并列不稳定、重复首单", groups[4][2][1:], "fixture_design")
add("B5", "H03", "隔离历史例：账户7月已有有效首单，8月又买；另一账户8月第一次有效买。", "前一账户8月计后续不计首购；后一账户计首购；仅为观测期，不推终身。", "按查询窗口重新排名、冒称终身新客", groups[4][2][1:], "fixture_design")
add("B5", "Z01", "2026年6月1日至29日分别列注册数及四项观测期指标。", "不同日期字段各自选记录，不能因没有订单就断定注册为0；期望由两张原表独立求出。", "跨事实表共享空结果")
add("B5", "A01", "辅助检查：同窗首购账户数＝首单数；首单数＋后续单数＝有效订单数。", "全覆盖排序口径一致且字段核定后使用；每项仍保留独立期望和首单身份。", "集合错但合计凑对", groups[4][2][1:] + ["valid_order_count"], "cross_metric_assertion")

add("B6", "M01", "分别列出2026年7月和8月的月内购买会员数、月内复购会员数和复购率。", "按月展示；每月账户去重和>=2有效订单；不跨月加总人数或平均比率。", "跨月两单当同月复购、用全部注册会员作分母")
add("B6", "R01", "隔离月内例：一账户当月1有效单、一账户2有效单、一账户1有效单加1全退单。", "只有2有效单者为复购；分别保留当月购买/复购集合。", "全退凑复购、用全量订单行简单条件代替账户月汇总", kind="fixture_design")
add("B6", "Z01", "选择经核对无有效购买的完整自然月，查月内人数及复购率。", "购买/复购人数为0，比率null；该月须在覆盖内；若原样本无例另用隔离fixture。", "零分母给0或误称无覆盖", kind="window_selection_required")
add("B6", "X01", "查询2026年8月1日至15日的月内购买人数、复购人数和复购率。", "不支持部分月，不能偷偷扩成整月。", "静默改时间", kind="unsupported_design")
add("B6", "X02", "2026年8月普通月内三项指标按成交门店分别列出。", "当前材料只支持全门店；拒绝拆店，不以结构可达代替业务支持。", "把普通订单维度能力扩散到受限月报", kind="unsupported_design")
add("B6", "X03", "2026年8月小程序渠道的普通月内购买人数、复购人数和复购率是多少？", "03原文未明确渠道；当前full_month_only契约统一限制全渠道。登记为当前引擎不支持，不冒称客户原文禁止；批前记录支持边界依据。", "把实现限制冒称客户事实，或计划成当前可执行ok", kind="engine_limit_design")

add("B7", "M01", "分别列出2026年7月与8月的六项月末付费会员月报指标。", "每月月底重判卡资格，再选当月有效订单；多月分行，资格、账户和订单不跨月串用。", "按当前日或购买日判资格、跨月加总人数")
add("B7", "Q01", "资格人工边界：两种纳入产品分别有效；收费联名卡、体验卡；普通等级配合格卡、金卡配不合格卡。", "按已获小林规则判断产品，金额和等级不代替资格；六指标分别看入选账户及订单。", "按付款>0或等级判断付费", kind="fixture_design")
add("B7", "Q02", "对悦享年卡和家庭季卡分别构造：判定日在生效日前/当天/后、计划结束日前/当天/后、提前终止日前/当天/后。", "生效含、结束与终止不含；按历史月末；每个产品和端点分支落实子例ID与期望后才能执行。", "端点闭开错误、只测一种卡、看当前状态", kind="parameterized_fixture_design")
add("B7", "Q03", "资格人工边界：终止空值、计划结束早于终止、终止早于计划结束、尚未生效但已有未来终止。", "空终止只表示没有提前终止，仍看计划结束；开始和两种结束条件同卡同时满足。", "空值当无限期、只看某一个日期", kind="fixture_design")
add("B7", "Q04", "资格人工边界：有效纳入卡混失效/排除卡；双年卡；年卡加季卡；一张在范围却失效、另一张范围外却有效。", "至少一张同卡同时满足范围与日期即可；不能跨卡拼条件；多卡不重复账户和订单金额。", "多卡扇出、全卡都要有效、跨卡拼资格", kind="fixture_design")
add("B7", "Q05", "月末生效但月中已购买；购买当天有效但月底失效；月末有资格但无购买/仅全退；一单与两笔有效单。", "资格按月末；购买用当月全部有效单；无购买资格账户不进入付费购买人数；复购需>=2有效单。", "资格人数代购买人数、按购买日截单、全退凑单", kind="fixture_design")
add("B7", "Q06", "原数据完整时无卡账户；另设卡数据缺失的受控测试输入。", "先有独立完整性清单或明确受控故障标记才可判记录缺失；不能仅凭卡表无行猜现实无卡。完整无卡可判不合格；异常输入不改正式CSV。", "缺失与不具资格混为一谈", kind="data_integrity_design")
add("B7", "Z01", "选择覆盖内无付费有效购买的完整月，查六项付费月报指标。", "四项人数/单数/金额加总为0，两项率/均额分母0为null；原样本缺例用独立fixture。", "有资格无购买算买家、null当0", kind="window_selection_required")
add("B7", "X01", "查询2026年8月1日至15日的六项付费月报指标。", "不支持部分月，不扩月、不报0。", "静默改问法", kind="unsupported_design")
add("B7", "X02", "2026年8月六项付费月报按成交门店分别列出。", "业务原文和当前引擎均限制全店，拒绝拆店。", "可达维度冒充支持范围", kind="unsupported_design")
add("B7", "X03", "2026年8月小程序渠道六项付费月报指标是多少？", "业务原文与当前引擎均要求全渠道；不支持渠道过滤。", "只对每卡局部做汇总、范围外查询报正常值", kind="unsupported_design")

for c in cases:
    c.update(state="design_pending_definition_and_expected", executable=False,
             expected_state="not_computed", execution_state="not_run",
             data_state="待检查原CSV是否能区分错误；不足另建标明人工构造的隔离fixture，不改课程数据",
             expected_method="；".join(dict.fromkeys(old[m]["independent_expected_method"] for m in c["metric_ids"])),
             source_refs=list({(s["path"], s["locator"]): s for m in c["metric_ids"] for s in old[m]["source_refs"]}.values()))

# Existing eight are references to immutable genuine runs, not newly run tests.
for t in load(FIRST / "independent/tests.json"):
    cases.append({"id": t["id"], "batch": "B1", "metric_ids": ["net_sales_cents"],
                  "kind": "existing_real_case", "question_or_fixture": t["question"],
                  "expected_behavior": "沿用已冻结独立期望；不是本轮新查询。",
                  "fault_to_detect": "见原用例来源、意图、判定及解释审查",
                  "state": "passed_on_recorded_library", "executable": True,
                  "expected_state": "frozen", "execution_state": "passed",
                  "expected_reference": "artifacts/w03/net-sales-first-20261108/independent/tests.json#" + t["id"],
                  "result_reference": "artifacts/w03/net-sales-first-20261108/test-v2/metric_test_report.json#" + t["id"],
                  "review_reference": "artifacts/w03/net-sales-first-20261108/independent/final-review.json",
                  "data_version": "qinghe-w03-20260923-small",
                  "catalog_sha256": "587271f8e3ee11d468a34125903b086fcb6cdd01306f37806ea8cd1ddb925694"})

for batch in batches:
    required = set(batch["new_scope_metric_ids"])
    required.update(m for c in cases if c["batch"] == batch["id"] for m in c["metric_ids"])
    while True:
        expanded = required | {d for m in required for d in dependencies.get(m, [])}
        if expanded == required:
            break
        required = expanded
    batch["test_required_dependency_closure"] = [t["id"] for t in targets if t["id"] in required]
    batch["local_build_rule"] = "局部构建取本批主目标与测试所选指标的并集，再递归闭合metric依赖；还须核派生模型及维度关系。B5交叉检查因此为6项而不是仅5项。"

common = copy.deepcopy(load(OLD / "metric_common_plan.json"))
common["status"] = "inherited_design_with_current_evidence_links"
for d in common["dimensions"]:
    d["status"] = "planned_not_run"
    d.pop("evidence", None)
    if d["id"] == "store":
        d.update(status="one_grouping_case_passed", evidence="NS02-july-transaction-store")
    if d["id"] == "order__channel":
        d.update(status="one_eq_filter_case_passed", evidence="NS03-aug-mini-program")
common["qualification_note"] = "共享资格设计不是已跑用例；B7参数化设计必须落实子例和独立资格/订单明细，不以单题或模型理解题代替六指标覆盖。"
common["judge_current_evidence"] = "artifacts/w03/net-sales-first-20261108/judge-injections-v2.json：13检查，10反例全拒；旧J01-J20不一律改passed，具体检查见原报告。"
common["normal_month_channel_note"] = "03仅明确整月全店；contract full_month_only目前一并限制全渠道，业务原文与运行限制分别登记（B6-X03）。"
common["release_gates"] = ["当前W03 v0.5正文已审，按批核指标来源/字段/依赖/范围", "独立CSV期望先于实际查询冻结", "构建/加载检查、完整结构结果、解释分别审", "变更Skill或重建库后回归全部已通过用例", "最终38项完整库、规模与多问法、聊天入口证据、交付与SOW另行完成"]

registry = {"version": "w03-metric-register-v1", "updated_at": "2026-11-08", "design_review": "pending",
            "purpose": "逐指标状态账；当前用户要求按指标族分批推进，替代逐项停点",
            "target_source": "customer/w03/targets.json", "batches": batches, "metrics": []}
unit_override = {"avg_order_value": "cents_per_order", "avg_buyer_value": "cents_per_member", "purchase_frequency": "orders_per_member", "items_per_order": "items_per_order", "monthly_paid_avg_order_value": "cents_per_order"}
for t in targets:
    m = t["id"]; o = old[m]; done = m == "net_sales_cents"
    batch = next(g[0] for g in groups if m in g[2])
    unit = unit_override.get(m, "ratio" if m in dependencies else "cents" if m.endswith("cents") else "count")
    registry["metrics"].append({"id": m, "name": t["name"], "batch": batch,
        "source_refs": o["source_refs"], "definition_candidate": o["definition"], "grain_candidate": o["grain"],
        "time_field_candidate": o["time_field"], "unit_token_candidate": unit,
        "basis_status": "材料+有效角色说明已取得" if batch == "B7" else "材料已有定义",
        "definition_status": "已核字段与范围" if done else "待批量核定字段与范围（非无依据）",
        "build_status": "build-v3已构建/加载" if done else "未构建",
        "test_design_status": "原8例已运行；新增批次场景待冻结" if done else "候选场景已登记",
        "expected_status": "原8例已冻结；新增场景待算" if done else "待独立核算/冻结",
        "small_status": "原8例通过" if done else "未运行",
        "explanation_status": "6成功+2非成功已审" if done else "未审",
        "scale_status": "未运行", "current_adopted_library_scope": "首项小样本库" if done else "无已采用实现",
        "dependency_metric_ids": dependencies.get(m, []),
        "test_case_ids": [c["id"] for c in cases if m in c["metric_ids"]],
        "known_pending": "新增多指标用例与规模仍待做" if done else "待核字段/支持范围、原样本区分力和独立期望；不自动视为需要再访谈",
        "specific_test_boundary": o["specific_boundaries"], "independent_expected_method": o["independent_expected_method"],
        "result_reference": "artifacts/w03/net-sales-first-20261108/completion.json" if done else "尚无执行证据"})
registry["summary"] = {"total_metrics": 38, "metrics_with_design": 38, "metrics_with_frozen_existing_tests": 1,
                       "metrics_with_small_pass": 1, "metrics_with_scale_pass": 0,
                       "existing_real_cases": 8, "new_design_entries": len(cases) - 8,
                       "new_model_calls": 0, "new_queries": 0}
plan = {"version": "w03-metric-test-plan-v3", "status": "design_pending_review",
        "not_native_tests_json": True, "source_plan": str(OLD.relative_to(ROOT)),
        "rule": "新条目为设计，未含expected.rows，不可直接交w03 test；未知期望不写0/null。参数化一行不是已具备多个可执行子例。",
        "promotion": "核定义/字段/支持范围→展开每条独立问句和fixture子例→核原样本并独立算期望→独立审核→冻结原生tests及数据/库版本→真实运行→解释复核；按批升级",
        "expansion_before_freeze": ["运行问句必须独立完整，将上述/五项/七项等设计简写替换成明确指标名称，不依赖上一题上下文", "B4-D01的门店分组与全店整体拆成独立intent/子例，分别核算期望，再辅助对照，不塞进一个不支持的双意图", "B7-Q02按产品和端点落实唯一子例ID；Q06记录独立完整性依据或受控故障标记"],
        "cases": cases, "common_design": common}

def dump(rel, body):
    p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n")

def render():
    rows = ["# W03 指标核对与测试登记", "", "更新：2026-11-08。当前推进单位改为**一个指标批次**。每批先核口径与测试，再构建、核数和审解释；仅真实业务取舍交本人，常规修复由导师和独立Agent处理。", "",
            "当前：**38项已登记；38项均有测试场景设计；仅净销售额具备已跑的8例；其余37项尚未冻结数值期望、未构建/问数；规模0/38。** 本轮新增模型调用/查询为0。", "",
            "有材料依据≠字段核定；设计完成≠期望已冻结；期望正确≠查询已通过；查询通过≠解释忠实或客户验收。设计审查状态见本轮独立报告。", "",
            "## 分批顺序", "", "| 批次 | 内容 | 指标数 | 当前安排 |", "| --- | --- | ---: | --- |"]
    for bid, label, ms in groups:
        rows.append(f"| {bid} | {label} | {len(ms)} | " + ("下一批：新增4项金额，同时回归净销售额" if bid == "B1" else "排队，依赖核定后整批推进") + " |")
    rows += ["", "默认累计已核范围＋当前批次，在新目录一次构建，避免同名语义模型冲突；比率的分子/分母必须在同次生成目标内。业务批次不等于可直接merge的文件包。若因输出规模改成局部试验库，取本批主目标与测试所选指标的并集，再递归闭合依赖，并核派生模型与维度：例如B5主目标5项，但交叉检查需要有效订单数，局部测试库至少6项目标。最终仍需一次一致的38项库和全套回归；不得手改生成物拼装。", "",
             "## 逐项状态", "", "来源01/02/03/04对应工程materials/w03同编号材料；全部另核05字典。B7还沿用小林/陈姐有效W03访谈及当前v0.5正文。\n\n“待核”是现有依据尚待本批映射和审核，不等于客户尚无规则；不为32项已有定义重复访谈。"]
    for bid, label, ms in groups:
        rows += ["", f"### {bid} · {label}", "", "| 指标 | 来源 | 定义/字段 | 构建 | 测试准备 | 小样本/解释 | 规模 |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for m in ms:
            src = "01" if bid in {"B1", "B2", "B3"} else "02" if bid == "B4" else "03" if bid in {"B5", "B6"} else "04＋访谈"
            if m == "net_sales_cents":
                states = "已核 | 已构建 | 原8例期望冻结；新增场景待算 | 原8/8通过、解释已审 | 未跑"
            else:
                states = "有依据，待批核 | 未构建 | 场景已列，期望待算 | 未跑/未审 | 未跑"
            rows.append(f"| {names[m]} `{m}` | {src} | {states} |")
    rows += ["", "## 测试怎么推进", "",
             "- [完整测试场景与状态](指标模型测试集设计.md)：按批次给出问题/边界、期望规则、要抓的错误；每指标映射到具体用例ID。",
             "- [机器登记账](../../customer/w03/metric_register.json)：精确来源、候选定义/粒度/日期/单位、依赖、测试ID与各阶段状态。",
             "- [候选测试设计](../../customer/w03/test-plans/metric_cases.json)不是运行tests.json；新期望未计算，不填假0或null。",
             "- [已具备的原生8例](../../customer/w03/tests.json)及[净销售额完成证据](../../artifacts/w03/net-sales-first-20261108/结果速览.md)保留；新增用例按批审核后追加，不覆盖旧失败。",
             "- [旧38项覆盖计划](../../artifacts/w03/full-test-design-20261106/v2/metric_coverage_plan.md)作为历史设计保留；其旧“均未运行”不代表本次最新状态。", "",
             "## 每批完成与登记规则", "",
             "1. 批前固定目标、来源、字段/粒度/单位、依赖、允许与拒绝的范围；已知规则直接用，真实缺口才停。",
             "2. 独立Agent从原CSV核算，保存订单/账户/月归属及分子分母；缺边界另建人工fixture。成功用例的完整expected和来源须先于查询冻结。",
             "3. 一次构建/加载本批库；同条件多指标问题减少重复调用，但每个指标须在成功expected.intent.metrics中出现并逐列验证，澄清/拒绝题不能冒充成功覆盖。",
             "4. 核查询条件、分组身份、每个值、单位、空值和版本，另审解释。新库/Skill变更回归所有已通过用例，不把旧库成绩搬给新库。",
             "5. 批后登记实际报告、库/数据/Skill版本、失败与修复、独立结论、仍待核事项；新增场景即便涉及已通过指标，也保持未运行直到真跑。",
             "6. 全38项小样本后另做规模独立期望、多问法与全部回归；规模、聊天接入、SOW与提交不并入本表的单指标通过数。", "",
             "当前边界：12维度已结构可达，仅成交门店分组与渠道eq筛选有首项真实用例；其余维度行为待测。普通月内三项的03材料只明确整月全店，当前full_month_only引擎还限制全渠道；实现限制与业务原文分开记录。", "",
             "本表为导师整理与独立设计审查，不登记本人已逐项作答、客户批准或正式提交。"]
    (ROOT / "docs/w03/指标核对与测试登记.md").write_text("\n".join(rows) + "\n")
    out = ["# W03 指标模型测试集设计与用例登记", "", f"更新：2026-11-08。沿用11月6日38项覆盖计划，现形成{len(cases)-8}条新增设计条目，另引用8条真实已跑用例。设计条目数不是最终执行题数：参数化边界会拆子例，多个相关指标可在同题比较。", "",
           "**每个指标都需要测试；未核定指标先登记测试问题、规则来源和要抓的错误，核定后独立算值。** 本文新条目均未计算期望、未运行，不能直接作为原生tests.json。主状态账见[指标登记](指标核对与测试登记.md)。", "",
           "## 先看一条新增测试长什么样", "", "B1-R01：查询8月10日的五项金额。要检查全额退款paid订单仍计原实付、原价和原优惠，而净贡献为0。先从CSV列出每个order_id及gross/paid/refund，再算五列期望；不能用当前净额0反推其余四列。现在状态是设计，金额期望待独立核算。", "",
           "## 本轮已有真实证据", "", "净销售额NS01—NS08在记录的small/library-v2上通过；6份成功回答、2份非成功理由已独立审。只覆盖原题、原库和对应范围，不覆盖下方新设计。", "", "| ID | 实际题目 | 状态 |", "| --- | --- | --- |"]
    for c in cases:
        if c["kind"] == "existing_real_case":
            out.append(f"| {c['id']} | {c['question_or_fixture']} | 原库已通过 |")
    for bid, label, ms in groups:
        out += ["", f"## {bid} · {label}", "", "本批指标：" + "、".join(f"`{m}`" for m in ms) + "。每项来源、独立核算方法和用例映射见机器登记账；下表未写执行结果，统一为**设计／待核字段、样本及独立期望**。", "",
                "| ID | 问题或边界输入 | 期望规则（非已算数值） | 要拦的错误 |", "| --- | --- | --- | --- |"]
        for c in cases:
            if c["batch"] == bid and c["kind"] != "existing_real_case":
                out.append(f"| {c['id']} | {c['question_or_fixture']} | {c['expected_behavior']} | {c['fault_to_detect']} |")
    out += ["", "## 共享覆盖与升级为可执行测试", "",
            "1. 所有新增成功设计先核原始样本能否区分目标错误。取消金额本来为0、全退净额也为0，单比金额不够；需核行集合、SQL与解释，必要时借支付单数区分，不伪造客户数据。退款时间列不存在，不能声称现金退款跨月已实证。",
            "2. 期望程序不导入被测库或SQL。数据/材料版本、独立原始明细、结构化intent、columns/rows/units与expected_source审核后才能进入customer/w03/tests.json。运行前将‘上述/五项/七项’等简写展开成独立完整问句；B4-D01门店分组与全店整体拆成独立intent/子例。未知期望在设计字段标待算，不写expected.rows的null；null仅用于已确定的零分母。",
            "3. 资格边界B7-Q01—Q06共享设计适用于六项指标；要保存逐卡→账户→月份→订单的入选/排除理由及各项数值。Q02为两产品多端点的参数化设计，未拆具体记录/子例前不可运行，也不算多个题已完成。",
            "4. 12维度沿用旧common计划，当前只store分组及order__channel的eq筛选有真实证据；还需归属门店/名称/地区、会员、等级、成交名称/地区、日期/月分组。每个维度按实际可达指标核，受限月报不能强加全部维度。",
            "5. 状态共享：缺日期澄清、覆盖外不支持已有净额实例；部分月/维度限制见B6/B7。error只用受控故障副本测试，不能制造业务事实。OR、任意SQL与不支持维度拒绝场景沿契约补入对应批次。",
            "6. 原判定器的13项真实副本检查与独立合成检查保留，不能把旧common里20项全改通过。多指标新增时补错列/漏指标/列交换、多单位、比率容差与百分数误作原值等判定对照；非模型新调用。",
            "7. 每批至少正常多指标用例＋区分核心业务错误的专项；同义问法放批后及规模回归。小样本与规模分别冻结期望。新库回归全部原先通过用例；同批通过后一次汇报，不逐指标等待确认。", "",
            "来源：[原38项计划](../../artifacts/w03/full-test-design-20261106/v2/metric_coverage_plan.md)、[测试指南](test-guide.md)、[契约](contract.md)、01—05材料及有效W03小林/陈姐访谈。机器记录保留逐项具体来源和旧共享计划：[metric_cases.json](../../customer/w03/test-plans/metric_cases.json)。"]
    (ROOT / "docs/w03/指标模型测试集设计.md").write_text("\n".join(out) + "\n")

if __name__ == "__main__":
    dump("customer/w03/metric_register.json", registry)
    dump("customer/w03/test-plans/metric_cases.json", plan)
    render()
    print(json.dumps(registry["summary"], ensure_ascii=False))
