# 38项指标测试覆盖计划 v2

本轮仅设计覆盖；没有计算数值期望，没有填正式tests.json，也没有执行查询。每项后续须固定原始数据及口径，独立求期望，再对完整结果契约判断。

| 指标 | 粒度与定义 | 区分错误的边界 | 独立期望方法 |
| --- | --- | --- | --- |
| order_count（创建订单数） | 一订单；所有创建订单，含取消 | 同日期paid/cancelled均计；起日含止日不含 | 逐行按ordered_at与条件筛后数唯一order_id |
| paid_order_count（支付订单数） | 一订单；status=paid，含后来全退 | 全退仍paid；cancelled不计；零实付paid仍计 | 独立筛status=paid后按窗口计订单 |
| valid_order_count（有效订单数） | 一订单；paid且实付减退款>0 | 部分退保留；全退/零净/取消排除 | 独立逐单计算净值并标有效，再计数 |
| cancelled_order_count（取消订单数） | 一订单；status=cancelled | paid退款不当取消；取消金额零不妨碍计订单 | 独立筛cancelled后计订单 |
| refund_order_count（退款订单数） | 一订单；paid且refund>0 | 部分与全退均计；退款0排除 | 独立标记退款正值的paid订单 |
| partial_refund_order_count（部分退款订单数） | 一订单；paid且0<refund<paid | refund=0和refund=paid两端排除 | 逐单比较三个整数条件，计入选订单 |
| full_refund_order_count（全额退款订单数） | 一订单；paid且paid>0且refund=paid | 零支付零退款不算全退 | 独立比较正支付与退款相等 |
| payment_cents（实付金额） | 一订单；paid订单实付合计 | 全退仍计原实付；cancelled不计；购卡不计 | 逐行累加paid订单paid_cents |
| refund_cents（退款金额） | 一订单；paid订单累计退款合计，归原订单日 | 跨快照退款仍按原订单日；不能按退款日现金流 | 按ordered_at筛选后累计原始refund_cents |
| net_sales_cents（净销售额） | 一订单；paid实付减累计退款合计 | 部分退/全退/取消；整数分；同账户多卡不膨胀 | 逐单从原始CSV算paid-refund后汇总，列order_id归属 |
| gross_cents（支付订单原价金额） | 一订单；paid订单原价合计 | 含全退paid原价；cancelled不计 | 筛paid独立累加gross_cents |
| discount_cents（优惠金额） | 一订单；paid订单gross-paid | 退款不抵扣原始优惠；取消排除 | 逐单算gross-paid，绝不减refund |
| buyer_count（购买会员数） | 一账户/查询组；有有效订单的不同CRM账户 | 同人多订单、多卡只一个账户；账户不等于自然人 | 有效订单按查询窗口过滤，再集合member_id |
| refund_buyer_count（退款会员数） | 一账户/查询组；有paid退款订单的不同账户 | 同账户多次退款只一人；部分/全退均计 | 退款paid订单形成member_id集合 |
| selling_store_count（成交门店数） | 一成交店/查询组；有有效订单的不同成交店 | home_store不代成交店；仅全退的店不计 | 有效订单形成store_id集合 |
| valid_order_items（有效订单商品件数） | 一有效订单；有效订单原始quantity之和 | 部分退款仍原始件数；不是净销量；全退不计 | 按有效单独立累加quantity |
| avg_order_value（有效订单均额） | 查询组汇总；net_sales_cents/valid_order_count | 先各自聚合再相除；分母零null；分组规模不同不能平均子组比率 | 从原始记录独立算分子net_sales_cents、分母valid_order_count，保留两值再除 |
| avg_buyer_value（购买会员人均消费） | 查询组汇总；net_sales_cents/buyer_count | 先各自聚合再相除；分母零null；分组规模不同不能平均子组比率 | 从原始记录独立算分子net_sales_cents、分母buyer_count，保留两值再除 |
| purchase_frequency（购买频次） | 查询组汇总；valid_order_count/buyer_count | 先各自聚合再相除；分母零null；分组规模不同不能平均子组比率 | 从原始记录独立算分子valid_order_count、分母buyer_count，保留两值再除 |
| refund_amount_rate（退款金额占比） | 查询组汇总；refund_cents/payment_cents | 先各自聚合再相除；分母零null；分组规模不同不能平均子组比率 | 从原始记录独立算分子refund_cents、分母payment_cents，保留两值再除 |
| cancel_rate（取消率） | 查询组汇总；cancelled_order_count/order_count | 先各自聚合再相除；分母零null；分组规模不同不能平均子组比率 | 从原始记录独立算分子cancelled_order_count、分母order_count，保留两值再除 |
| refund_order_rate（退款订单率） | 查询组汇总；refund_order_count/paid_order_count | 先各自聚合再相除；分母零null；分组规模不同不能平均子组比率 | 从原始记录独立算分子refund_order_count、分母paid_order_count，保留两值再除 |
| discount_rate（优惠率） | 查询组汇总；discount_cents/gross_cents | 先各自聚合再相除；分母零null；分组规模不同不能平均子组比率 | 从原始记录独立算分子discount_cents、分母gross_cents，保留两值再除 |
| items_per_order（单均商品件数） | 查询组汇总；valid_order_items/valid_order_count | 先各自聚合再相除；分母零null；分组规模不同不能平均子组比率 | 从原始记录独立算分子valid_order_items、分母valid_order_count，保留两值再除 |
| new_member_count（注册会员数） | 一CRM账户；按registered_at统计新注册账户 | 注册无购买仍计；按归属店/等级；边界日期 | 独立读members按registered_at筛选、核member_id |
| first_buyer_count（观测期首购会员数） | 一账户；全覆盖期首有效订单落入窗口的账户 | 窗口前首单、首记录无效、同日排序、非终身 | 全覆盖orders先筛有效，按member/date/id排序，再筛首单日期 |
| first_order_sales_cents（观测期首单净销售额） | 一账户首有效订单；全覆盖期首单净额按首单日期 | 同日两单取order_id第一；窗口前首单不换首 | 独立全历史排序取首单，窗口筛选再累计净额 |
| first_order_count（观测期首单数） | 一账户首有效订单；首有效订单在窗口内的单数 | 先全历史后窗口；第一条无效跳过 | 独立取全覆盖有效单首位并数窗口内order_id |
| repeat_order_count（观测期后续购买订单数） | 一有效订单；全覆盖期每账户第二笔及以后 | 非月内复购人数；窗口第一笔可能是历史后续 | 独立全覆盖排序rank>=2后按订单日筛 |
| monthly_buyer_count（月内购买会员数） | 一账户/自然月；月内>=1有效单账户数 | 月内多单去重；两月分别一单；零购买月 | 独立逐月有效订单归并member_id |
| monthly_repeat_buyer_count（月内复购会员数） | 一账户/自然月；同月>=2有效订单账户数 | 1单/2单/全退不凑单；跨月一单各不算复购 | 独立按月账户数有效order_id，再数>=2账户 |
| monthly_repeat_rate（月内复购率） | 一自然月；月内复购账户/月内购买账户 | 旧注册会员分母拒绝；零分母null；多月分别 | 独立形成两个人群集合计数后相除 |
| monthly_paid_buyer_count（月末付费会员购买人数） | 一合格账户/自然月；月末合格且月内有有效购买 | 月末生效前已有购买；购买有效月末失效；资格无购买 | 逐月按末日逐卡判并归账户，再与当月有效订单账户相交 |
| monthly_paid_order_count（月末付费会员有效订单数） | 一有效订单/合格账户月；月末合格账户的当月全部有效单 | 多卡不能复制订单；月末生效纳入早单 | 独立资格账户集合筛当月有效order_id |
| monthly_paid_sales_cents（月末付费会员净销售额） | 一有效订单/合格账户月；月末合格账户当月有效单净额 | 部分退/全退；多卡不可翻倍；购卡收入排除 | 独立按合格账户集合筛有效单后逐单累计净额 |
| monthly_paid_repeat_buyer_count（月末付费会员复购人数） | 一合格账户/自然月；合格账户当月>=2有效单 | 一单/两单；全退不凑单；多卡不凑次数 | 独立资格集合与月有效订单计数>=2账户相交 |
| monthly_paid_repeat_rate（月末付费会员复购率） | 一自然月；月末付费复购人数/付费购买人数 | 分母非全部合格账户；零分母null；多月分列 | 独立资格下两个人群计数相除 |
| monthly_paid_avg_order_value（月末付费会员订单均额） | 一自然月；月末付费净额/有效订单数 | 分母非卡数/账户数；0订单null；整数金额除法 | 独立资格订单集合净额总和除订单数 |

## 支持范围与来源

16项订单基量以01为据；8项均值比例以02为据；8项注册/首购/月内量以03为据；6项月末付费量以04、小林与陈姐为据。逐项路径、定位、单位、查询种子、支持/拒绝范围、small/scale计划见metric_coverage_plan.json。

普通月内三项仅完整自然月、全门店；渠道条件需按原文与可达关系核定，不自行增加规则。付费六项完整自然月、全门店、全渠道，多月逐月；不支持门店/渠道拆分。

## 通用覆盖

12个维度都指定了候选验证指标，尚未声明库已支持；4类返回状态；20个判定自检场景（含课程要求的10类错误注入、额外身份/类型错误及正确对照）；解释审查、重建与规模回归均另列在metric_common_plan.json。

数值期望独立从CSV计算，按订单/账户/月份保留归属证据；不调用被测指标SQL。分组身份、遗漏/多余/重复、每个值、单位、空值、意图与版本都核对。正确数字配错误范围仍须失败。

## 实施顺序

1. 冻结模型候选并通过独立审查。
2. 逐项核定38定义和12维度适用范围；为各项建立small数值期望。
3. 完成构建与纯比较判定，先用错误和正确对照自检。
4. 跑真实查询并单独审解释；修构建后重建重测。
5. scale单独求期望并做回归，再整理SOW与未决确认。

## 六项付费指标共享资格边界

六行均明确连接 metric_common_plan.json 的 PAID-QUAL-COMMON：两类纳入与两类排除、金额/等级不能替代、两类卡完整日期分支、任一卡与跨卡不能拼条件、多卡去重、月末/购买日反向、逐月变化及零购买。未来独立核入选/排除账户和订单身份，再核每项总值及分子分母；模型题通过不能替代此组数值测试。原CSV缺边界时另建隔离人工fixture并单独冻结，不改课程数据。
