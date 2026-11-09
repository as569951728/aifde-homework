# W03 可更新内容与影响范围 v3

2026-11-06 · 导师按原材料预整理，待独立审查；未运行正式提取/更新、未形成新模型或实际查询。

## 当前结论与边界

本次拟完善的是已定38项作业所需的业务认识与证据，不自动新增客户承诺。课程要求、角色对学员分期提案的认可、公司批准分别记录。资格规则直接影响6项付费月报；其余32项按各自定义核查，不能统一加付费筛选，也不能断言共享模型改动绝无影响。

本轮依现用 extract-business scope-first-v3 / 提取提示v2 / gap-review v0.3 的规则做预整理；实际只运行了gap-review的prepare_scope.py材料标题索引（paid_scope.json），不把整理UP编号冒称原生提取claim_id或Skill模型调用。正式更新应走内含提取的w02_workflow.py。

## 先看更新清单

| 编号 | 内容 | 变化 | 主要去向 | 直接指标影响 |
|---|---|---|---|---|
| UP-01 | 保留两个业务目标，补本期查数的作用 | 保留并补充 | 模型§1/§5：目标与候选用途；阶段成果细节进入SOW | 见下方条件性/非计算影响 |
| UP-02 | 账户、卡、订单、门店关系 | 本期新增，限定旧未知 | 模型§2：对象/关系；字段和粒度→指标核定与构建输入 | 见下方条件性/非计算影响 |
| UP-03 | 纳入产品与等级/购卡金额区分 | 新增规则 | 模型§2/§4：范围及资格规则；六指标引用 | monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value |
| UP-04 | 两类卡的日期端点与提前终止 | 新增规则，旧未知在本期收窄 | 模型§4：资格判定；字段表达→指标核定与构建 | monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value |
| UP-05 | 账户资格与多卡去重 | 新增规则 | 模型§2/§4；构建的账户资格派生层及连表粒度 | monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value |
| UP-06 | 有效购买与订单状态 | 本期新增定义，收窄旧未知 | 模型§2/§4：购买语义；各统计集合/字段→指标核定 | valid_order_count、buyer_count、selling_store_count、valid_order_items、avg_order_value、avg_buyer_value、purchase_frequency、items_per_order、first_buyer_count、first_order_sales_cents、first_order_count、repeat_order_count、monthly_buyer_count、monthly_repeat_buyer_count、monthly_repeat_rate、monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value |
| UP-07 | 退款归期、金额、件数与未定义 | 本期定义/解释边界补充 | 模型概念/使用边界；完整公式、时间、单位、null→指标核定/查询契约 | payment_cents、refund_cents、net_sales_cents、gross_cents、discount_cents、valid_order_items、avg_order_value、avg_buyer_value、refund_amount_rate、discount_rate、items_per_order、first_order_sales_cents、monthly_paid_sales_cents、monthly_paid_avg_order_value、purchase_frequency、cancel_rate、refund_order_rate、monthly_repeat_rate、monthly_paid_repeat_rate |
| UP-08 | 观测期首购与后续购买 | 本期新增分析语义 | 模型§2：首购/后续语义；排序和窗口→指标定义/派生模型 | first_buyer_count、first_order_sales_cents、first_order_count、repeat_order_count |
| UP-09 | 月内复购与当前分母 | 报表定义新增，替换旧稿口径的适用范围 | 模型§2：定义需范围；三项报表特定分子分母/窗口→指标核定 | monthly_buyer_count、monthly_repeat_buyer_count、monthly_repeat_rate |
| UP-10 | 月末资格选择与整月购买 | 本期修正旧候选的应用 | 模型引用本期报表选择，避免与旧候选冲突；详细选择及范围→指标核定 | monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value |
| UP-11 | 注册统计与维度归属 | 本期新增/明确 | 模型§2关系与§4使用边界；具体维度可达→构建/核定 | new_member_count |
| UP-12 | Excel用途与运营一般流程 | 补充已有流程，不建新系统事实 | 模型§3/§4：局部流程和来源边界；具体Excel字段→调查待办 | 见下方条件性/非计算影响 |
| UP-13 | 优惠券支持偏好与助手权限 | 补充偏好，保留原权限边界 | 模型§5：候选支持及前提；后续支持范围→SOW | 见下方条件性/非计算影响 |
| UP-14 | 门店配合与核对条件 | 补充既有协作条件 | 模型§3/§4；具体责任/工作量/排期→SOW待定 | 见下方条件性/非计算影响 |
| UP-15 | IT核查边界 | 补充范围/继续保留未知 | 模型§3/§4；实际接口、材料责任与依赖→SOW | 见下方条件性/非计算影响 |
| UP-16 | 角色核查职责与阶段成果 | 补充职责，阶段方案性质保留 | 模型保留角色职责/权限；详细双方成果责任及阶段范围→SOW | 见下方条件性/非计算影响 |
| UP-17 | 费用、变更与延期核查要求 | 新增SOW待补条目，正文只保留权限边界 | SOW范围/责任/依赖/变更/未决；来源与取舍→过程记录 | 见下方条件性/非计算影响 |
| UP-18 | 重分待核项与证据边界 | 保留并迁移旧待核状态 | 模型对应位置保留核心未知；缺口进度→interview_notes/model_changes；商业→SOW | 见下方条件性/非计算影响 |

## 影响到哪些交付物

| 层次 | 拟改变什么 | 不自动推出什么 |
|---|---|---|
| 模型 | 对象/关系、资格与购买语义、局部流程、角色和未知；保留两个目标 | 已采纳新模型、生产规则普适、公司已有完整闭环 |
| 指标 | 六项资格依赖及其他指标各自报表定义；时间/分子分母/支持范围 | 38项全部统一付费过滤、增加第39项、任意维度可查 |
| 工程 | 下一步补来源/重点/过时目标；构建Skill尚未开发，按依赖生成语义定义 | 当前已有青禾正式指标库需要返工、修改原CSV或重建环境 |
| 测试 | 已冻结85题及38项计划用来核候选；六项共享资格族核实际成员/订单 | 设计通过等于模型运行或数值已通过，改答案迎合输出 |
| SOW | 补本期/后续、双方工作/依赖、留证、变更/延期与待决 | 自动纳入筛选、自动营销、生产接入、收益或商业承诺 |
| 历史/记录 | 用新证据更新待核状态，取舍保留在记录 | 改写W02原稿/旧评分、删除旧失败或作废W04档案 |

## 逐项依据与拟议影响

### UP-01 保留两个业务目标，补本期查数的作用

**旧认识：** v0.4 §1、§5：原因验证与岗位提效分别观察
**可提炼内容：** 保留理解复购变化和减少重复整理核对两个目标。本期先形成定义可追溯、可独立核对的查数，支持核范围、名单和后续分析；不能据此写原因已查明、工时已节省或复购改善。
**适用范围：** 青禾整体目标与本期合成测试阶段分开
**去向：** 模型§1/§5：目标与候选用途；阶段成果细节进入SOW
**直接影响：** 无直接计算定义变更
**关联影响：** 影响38项的结果解释和阶段价值说明，不改变38项计算公式；解释审查需保留因果边界。
**回归检查：** U01、U06、E02、REG02
**仍待核：** 旧四季度报表复算、原因、岗位工时基线、收益目标仍未取得。
**交付范围判断：** 澄清既有阶段价值，不增加原因分析完成/效果承诺。
**依据：** [BASE §1、§5](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)；[D7 运营群、范围评审安排](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/07_客户内部沟通.md)；[D8 角色工作清单](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/08_业务目标与工作清单.md)；[L MSG-03855、MSG-03856、MSG-03865、MSG-03866](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)；[W MSG-03910、MSG-03911](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json)

### UP-02 账户、卡、订单、门店关系

**旧认识：** v0.4 §2会员行、购买行、保留设计：账号/卡/人对应及字段关联待核
**可提炼内容：** 本期测试数据中，一份members记录是一CRM账户，一账户可有多张卡和订单；订单成交门店不同于会员归属门店。账户不等于跨系统自然人，现有关系不指明某订单实际使用哪张卡。物理字段映射在字典/指标核定中展开。
**适用范围：** 仅本期四表测试覆盖；不推定生产身份统一或活动关联接通
**去向：** 模型§2：对象/关系；字段和粒度→指标核定与构建输入
**直接影响：** 无直接计算定义变更
**关联影响：** 38项目标可能共享表关系；具体连表/维度按各指标依赖判断。成交店与归属店相关维度、会员/等级及多卡连接重点复核，不能说每项都需连卡。
**回归检查：** U02、U03、B06、T02
**仍待核：** 旧POS自然人对齐、订单到卡/券/活动链路、生产关联质量仍未核。
**交付范围判断：** 补必要语义，不增加身份治理或生产接入交付。
**依据：** [D5 orders、members、stores、cards、课程方提供的数据接入层](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)；[D7 IT对接纪要](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/07_客户内部沟通.md)；[Z MSG-03874、MSG-03875、MSG-03876、MSG-03877](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json)

### UP-03 纳入产品与等级/购卡金额区分

**旧认识：** v0.4 §2会员/活跃、§4.1：范围未定，标签不能代定义
**可提炼内容：** 本期总部月报纳入悦享年卡和家庭季卡，排除异业联名卡及体验卡。等级与付费资格不同，购卡实付不能代替卡类型和有效状态；不具本期资格不自动归为全系统免费类别。
**适用范围：** 本期总部运营月报，不改其他报表或全系统分类
**去向：** 模型§2/§4：范围及资格规则；六指标引用
**直接影响：** monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value
**关联影响：** 其他32项不自动添加付费过滤；仅在共享连接实现改动时查无意过滤或行膨胀。
**回归检查：** P01、P02、P03、P04、P05、P06、P07、P08、P09、U02
**仍待核：** 其他报表产品范围及全系统类别互斥仍未核。
**交付范围判断：** 六项既定月报定义补齐，不新增筛选名单或“全部资格账户数”指标。
**依据：** [L MSG-03847、MSG-03848、MSG-03853、MSG-03854](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)；[D5 members、cards](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)；[BASE §2会员行](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)

### UP-04 两类卡的日期端点与提前终止

**旧认识：** v0.4 §2候选资格、§6历史资格待核；小林/老周初次不掌握
**可提炼内容：** 在提问限定的两类卡范围，指定判定日须不早于生效日，早于计划结束日；有提前终止时还须早于终止日。空提前终止仅表示本记录没有提前终止，计划有效期仍限制；不能拿当前状态代历史日。
**适用范围：** 两类纳入卡、本期测试月报；角色确认与生产凭据分层
**去向：** 模型§4：资格判定；字段表达→指标核定与构建
**直接影响：** monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value
**关联影响：** 日期模型若共享，按依赖检查；不向其他产品或全部报表推广。
**回归检查：** DY01、DY02、DY03、DY04、DY05、DY06、DY07、DY08、DY09、DY10、DY11、DY12、DQ01、DQ02、DQ03、DQ04、DQ05、DQ06、DQ07、DQ08、DQ09、DQ10、DQ11、DQ12、E04
**仍待核：** 具体规则文件、历史执行记录及生产普适性仍缺；不阻塞本期据角色答复更新/验证。
**交付范围判断：** 明确计算依据，不意味着生产规则/历史执行已验收。
**依据：** [C MSG-03885、MSG-03886、MSG-03889、MSG-03890](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json)；[L MSG-03849、MSG-03850](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)；[Z MSG-03874、MSG-03875](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json)；[D5 cards](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)

### UP-05 账户资格与多卡去重

**旧认识：** v0.4 §2账户/卡关系及重复关联风险尚未具体化
**可提炼内容：** 同一账户存在一张同时合范围且有效的卡即可有资格；其他失效或排除卡不否定。两张卡不能拼出不同条件；多张有效卡不重复计账户，也不重复累计同一订单。
**适用范围：** 本期资格账户与其订单关联
**去向：** 模型§2/§4；构建的账户资格派生层及连表粒度
**直接影响：** monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value
**关联影响：** 六项必须核账户/订单身份；其他32项只有受共享连接实现改动时才有间接风险，不应被迫连接卡表。
**回归检查：** C01、C02、C03、C04、C05、C06、U03
**仍待核：** 实际SQL连接、样本行归属和数值仍未验证。
**交付范围判断：** 防止既定指标重复计数，未增加新业务能力。
**依据：** [L MSG-03853、MSG-03854](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)；[C MSG-03885、MSG-03886、MSG-03890](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json)；[D5 cards、orders](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)

### UP-06 有效购买与订单状态

**旧认识：** v0.4 §2购买记录、§6：有效购买、退款取消待核
**可提炼内容：** 本期有效购买为paid且实付大于累计退款；取消、全退和零净额不计有效购买，部分退仍可有效。创建订单、paid订单和有效订单是不同集合，不能互相替代。
**适用范围：** 本期测试覆盖内订单定义，不追认旧四季度统计
**去向：** 模型§2/§4：购买语义；各统计集合/字段→指标核定
**直接影响：** valid_order_count、buyer_count、selling_store_count、valid_order_items、avg_order_value、avg_buyer_value、purchase_frequency、items_per_order、first_buyer_count、first_order_sales_cents、first_order_count、repeat_order_count、monthly_buyer_count、monthly_repeat_buyer_count、monthly_repeat_rate、monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value
**关联影响：** 创建/支付/退款/取消及相关比例需检查没有误套有效过滤；不把所有paid基量都改成有效单。
**回归检查：** B01、R03、R05、C05
**仍待核：** 实现、原始数据独立期望及生产状态差异仍需后续核。
**交付范围判断：** 完善既定38项的依赖，未新增订单系统功能。
**依据：** [D1 创建订单数、支付订单数、有效订单数、退款订单数](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/01_订单日报说明.md)；[D2 开头财务确认](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/02_财务邮件.md)；[D5 orders](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)

### UP-07 退款归期、金额、件数与未定义

**旧认识：** v0.4 §2购买/复购、§6：退款取消与计时待核
**可提炼内容：** 本期退款按原订单下单日归属；商品订单收入与购卡实付分开。金额是整数分，展示元须换算；退款不冲减原优惠，原始购买件数不是净销量。零分母未定义，覆盖外不是零。模型保留业务区别，具体公式和输出契约分置。
**适用范围：** 本期订单快照统计与测试覆盖
**去向：** 模型概念/使用边界；完整公式、时间、单位、null→指标核定/查询契约
**直接影响：** payment_cents、refund_cents、net_sales_cents、gross_cents、discount_cents、valid_order_items、avg_order_value、avg_buyer_value、refund_amount_rate、discount_rate、items_per_order、first_order_sales_cents、monthly_paid_sales_cents、monthly_paid_avg_order_value、purchase_frequency、cancel_rate、refund_order_rate、monthly_repeat_rate、monthly_paid_repeat_rate
**关联影响：** 零分母是11项比率/均值/频次的确定共同约束，均已列直接影响；覆盖外不能返回零是全部38项的共同查询约束，单列shared_contract_impacts。购买/退款人数的日期归属仍按各自订单集合核，不追加退款现金流指标。
**回归检查：** B01、B02、B03、B05
**仍待核：** 退款发生日现金流、退货件数及生产制度不从现有字段推算。
**交付范围判断：** 补既有定义与拒绝边界，不扩成现金流或净退货分析。
**依据：** [D1 退款金额、净销售额、优惠金额、有效订单商品件数](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/01_订单日报说明.md)；[D2 开头与八项比例定义](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/02_财务邮件.md)；[D5 orders、cards、覆盖](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)；[CONTRACT catalog单位、查询契约](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/contract.md)

补充直接定义依据：D3《会员运营周报》的月内复购率，D4《本期统计确认邮件》的月末付费复购率及订单均额，均明确分母零时未定义；与原D2总则一致。

### UP-08 观测期首购与后续购买

**旧认识：** v0.4 §2购买/复购尚无具体观测期排序定义
**可提炼内容：** 观测期首购是全测试历史内首笔有效订单；先按账户的日期、订单号排全历史，再筛查询窗口，非终身首购。第二笔及以后订单与月内复购人数分开。
**适用范围：** 全测试覆盖2024-09-01至2026-09-01不含止日
**去向：** 模型§2：首购/后续语义；排序和窗口→指标定义/派生模型
**直接影响：** first_buyer_count、first_order_sales_cents、first_order_count、repeat_order_count
**关联影响：** 与注册日期、月内复购分开；用相同排序派生层的四项都需回归，不能只测首单数。
**回归检查：** B04、T02
**仍待核：** 覆盖前真实购买历史未知，不能升级为终身首购。
**交付范围判断：** 落实既定四项，不增加终身客户分析。
**依据：** [D3 观测期首购会员数、观测期首单净销售额、观测期首单数、观测期后续购买订单数](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/03_会员运营周报.md)；[D5 覆盖、orders](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)

### UP-09 月内复购与当前分母

**旧认识：** v0.4 §2复购定义仍待核；03所述旧周报草稿曾用注册人群
**可提炼内容：** 本期月内复购在同一自然月有效购买账户中计算：至少两笔有效订单的账户为复购群体。当前分母是当月有效购买账户，非全部注册账户；多月逐月，不把月度去重人数相加成跨月人数。
**适用范围：** 业务材料D3限定完整自然月、全门店，未单独规定全渠道；当前工程要求月度定义设置full_month_only，其实现还禁止任何filter及除metric_time__month外的分组。技术限制不能冒称客户永久规则。
**去向：** 模型§2：定义需范围；三项报表特定分子分母/窗口→指标核定
**直接影响：** monthly_buyer_count、monthly_repeat_buyer_count、monthly_repeat_rate
**关联影响：** 按当前工程实现，普通月内三项也不能筛渠道/会员/等级等任意条件，或按非月份维度分组；多月必须逐月展示。目录未生成前这是已知静态支持边界，后续还要真实拒绝/支持测试。旧四季度趋势不能据此重认。
**回归检查：** R05、R07、B05、E02
**仍待核：** 具体各月数值、旧报表口径和历史趋势可比性仍待核。
**交付范围判断：** 修正本期定义，不承诺解释复购下降原因。
**依据：** [D3 开头统计调整、月内购买会员数、月内复购会员数、月内复购率](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/03_会员运营周报.md)

当前工具依据：[查询契约第29行](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/contract.md:29)、[引擎门禁](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/platform/fde_product/metrics/engine.py:117)。这是静态核查，不是查询成功证据。

### UP-10 月末资格选择与整月购买

**旧认识：** v0.4 §2候选归类：按购买发生时资格，由学员提出且待核
**可提炼内容：** 六项付费月报采用月末资格先选账户，再计整月有效购买。月底才生效但此前有购买仍纳入；购买时有资格月底失效则排除。本期购买人数只数合格且有有效购买账户，不能另增全体资格人数。旧购买时点方案保留历史，不用于本期六项。
**适用范围：** 六项、完整自然月、全渠道全门店；多月分列，暂不按门店/渠道拆
**去向：** 模型引用本期报表选择，避免与旧候选冲突；详细选择及范围→指标核定
**直接影响：** monthly_paid_buyer_count、monthly_paid_order_count、monthly_paid_sales_cents、monthly_paid_repeat_buyer_count、monthly_paid_repeat_rate、monthly_paid_avg_order_value
**关联影响：** 六项一起核入选账户、订单与分子分母。除D4业务范围外，当前full_month_only还禁止任何filter及除month外分组，见补充计划；其他32项不套付费资格，其中普通月内三项受相同引擎策略限制，其余按各自定义。
**回归检查：** R01、R02、R03、R04、R05、R06、U06
**仍待核：** 实际查询、独立计算和输出使用仍未完成。
**交付范围判断：** 符合既定六项；无新增第39项、任意筛选或自动触达。
**依据：** [D4 统计选择与六项定义](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/04_本期统计确认邮件.md)；[L MSG-03865、MSG-03866、MSG-03867、MSG-03868、MSG-03869、MSG-03870](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)；[BASE §2候选归类规则](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)

### UP-11 注册统计与维度归属

**旧认识：** v0.4 §2会员与购买、§4注册考核边界
**可提炼内容：** 本期注册统计按CRM账户注册日期；归属门店及等级可用于该项分组。注册账户不是购买者或自然人；注册统计也不等于导购考核口径。12个目标维度按各指标语义和可达关系分别核。
**适用范围：** 测试注册指标及允许维度；不裁定业务考核
**去向：** 模型§2关系与§4使用边界；具体维度可达→构建/核定
**直接影响：** new_member_count
**关联影响：** 维度审核覆盖12项目标但不是每项指标都支持12维度；成交店/归属店分组的实际路径须核。
**回归检查：** B06、F10、T02
**仍待核：** 注册计入导购考核的方法与最终确认人仍未核。
**交付范围判断：** 完成既定注册/维度目标，不建设考核模块。
**依据：** [D3 注册会员数](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/03_会员运营周报.md)；[D5 members、stores、orders](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)；[BASE §4.5](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)；[CONTRACT 维度目标与可达性](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/contract.md)

### UP-12 Excel用途与运营一般流程

**旧认识：** v0.4 §3运营准备、§4.7个人Excel、§6名单来源待核
**可提炼内容：** 小林个人Excel用于优惠券活动及未购会员回访，协调相关同事确认线上/门店安排并跟进。可辅助核对，不能直接当公司统一口径或交付数据。一般步骤包括明确对象/工作、确认执行协作、跟进反馈、整理结果与未核项；具体实例、条件和完整闭环仍未知。
**适用范围：** 角色实际经手的一般做法/个人工作记录，不是统一SOP或生产数据表
**去向：** 模型§3/§4：局部流程和来源边界；具体Excel字段→调查待办
**直接影响：** 无直接计算定义变更
**关联影响：** 影响问数结果解释、可核对依据展示和后续场景调查；不据此生成名单表/触达字段。
**回归检查：** U04、F01、F03、F05、F08、F09、E05
**仍待核：** 具体名单来源/筛选阈值、活动实例、表字段、反馈返回及下轮决策仍未知；作废W04的60天/周一等不采用。
**交付范围判断：** 后续工作线索，不把个人表直接接入或新建会员筛选功能。
**依据：** [L MSG-03857、MSG-03858、MSG-03861、MSG-03862、MSG-03869、MSG-03870](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)；[BASE §3、§4.7、§6](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)

### UP-13 优惠券支持偏好与助手权限

**旧认识：** v0.4 §5候选支持、§4.3业务人员确认
**可提炼内容：** 小林偏好先辅助优惠券活动的名单/执行记录整理核对与跟进；这是岗位偏好和痛点，未测工时。人群/执行方案由业务人员确认，助手不自动发券、联系或改记录；不能改写成小林本人无权限。
**适用范围：** 岗位偏好/候选支持，不是已获批交付
**去向：** 模型§5：候选支持及前提；后续支持范围→SOW
**直接影响：** 无直接计算定义变更
**关联影响：** 需回归解释与权限边界；对38计算定义无直接变化。未来真做筛选才评字段、授权、人员和验证。
**回归检查：** F02、F06、U06、REG01
**仍待核：** 筛选条件、负责人、替代哪些工作及效率效果基线仍待实际任务核。
**交付范围判断：** 若纳入本期或自动触达，将是实际范围变化，不能随模型更新自动加入。
**依据：** [L MSG-03855、MSG-03856、MSG-03859、MSG-03860、MSG-03861、MSG-03862](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)；[D8 小林工作清单](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/08_业务目标与工作清单.md)；[BASE §4.3、§5](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)

### UP-14 门店配合与核对条件

**旧认识：** v0.4 §3门店流程、§4.4/5工作量与考核
**可提炼内容：** 门店可按判定日逐卡核并归账户；配合前说明适用范围、工作量、现场问题处理责任和工作记录。要求不清或影响考核时先澄清再安排；仍未指定具体人手/工时/时间。
**适用范围：** 角色配合条件，不是门店已接受测试任务或正式验收
**去向：** 模型§3/§4；具体责任/工作量/排期→SOW待定
**直接影响：** 无直接计算定义变更
**关联影响：** 业务核对可帮助六项资格解释；计算独立验证仍由交付方准备，不能因规则可核就强派门店承担测试。
**回归检查：** F04、F10、C01、C06
**仍待核：** 实际参与门店、人手工时、现场负责人、工作记录和考核确认仍待定。
**交付范围判断：** 补协作条件，不自动增加门店执行工作或改变考核。
**依据：** [C MSG-03885、MSG-03886、MSG-03887、MSG-03888、MSG-03889、MSG-03890](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json)；[D8 陈姐工作清单](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/08_业务目标与工作清单.md)；[BASE §3、§4.4/5](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)

### UP-15 IT核查边界

**旧认识：** v0.4 §3数据核查协作、§4.6接入条件
**可提炼内容：** 说明核查对象、用途和范围后，老周配合核取数条件、统计范围/时间/说明，列待补记录与责任。具体记录名称和交付内容看实际材料；合成测试结构/覆盖/关联核对不等于生产已接通。
**适用范围：** 本期测试与协作条件，非生产访问授权
**去向：** 模型§3/§4；实际接口、材料责任与依赖→SOW
**直接影响：** 无直接计算定义变更
**关联影响：** 影响字段/覆盖检查与来源解释；工程输入只能列已有材料，不能假造生产交付。
**回归检查：** F07、E04、U06
**仍待核：** 生产权限、清洗接入联调、确切材料名称/交付日期仍未定。
**交付范围判断：** 不增加生产导入或联调承诺。
**依据：** [Z MSG-03872、MSG-03873、MSG-03876、MSG-03877、MSG-03880、MSG-03881、MSG-03882、MSG-03883](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json)；[D7 IT对接纪要](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/07_客户内部沟通.md)；[BASE §3、§4.6](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)

### UP-16 角色核查职责与阶段成果

**旧认识：** v0.4 §3数据协作及§5阶段讨论；本周新增王经理具体反馈
**可提炼内容：** 运营核业务范围，IT核字段覆盖，王经理参与统计口径与验收依据及财务合同材料核查；交付方准备实际查询、独立核对、追溯与责任草案，客户提供/确认相应范围材料。王经理认可学员阶段提案及提出要求，不等于公司批准。
**适用范围：** 课程要求38项与客户阶段核查意见分开；本期合成测试
**去向：** 模型保留角色职责/权限；详细双方成果责任及阶段范围→SOW
**直接影响：** 无直接计算定义变更
**关联影响：** 影响38项证据包与验收依据表达；测试目标不因角色支持而自动完成，核查意见不是验收签字。
**回归检查：** A01、A02、U06、E06
**仍待核：** 最终验收人、审批权限/额度、执行安排责任方与正式预算合同上线仍未定。
**交付范围判断：** 既定38项测试阶段的材料要求；会员筛选/运营执行另列后续。
**依据：** [D4 阶段验收范围与职责](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/04_本期统计确认邮件.md)；[D7 范围评审安排](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/07_客户内部沟通.md)；[W MSG-03910、MSG-03911、MSG-03918、MSG-03919、MSG-03930、MSG-03931、MSG-03932、MSG-03933](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json)

### UP-17 费用、变更与延期核查要求

**旧认识：** v0.4不含本期具体商业条款；sow.md仍模板
**可提炼内容：** 费用列构成与计价依据，未定金额待确认；结算对应约定成果与记录，节点/付款尚待谈。变更书面列内容及费用责任影响；假设客户延期需记缺项/通知/影响，执行安排由执行方决定，受影响排期费用双方书面确认再复核。
**适用范围：** 拟议交付条款和王经理核查要求；03928为假设，不是实际延期
**去向：** SOW范围/责任/依赖/变更/未决；来源与取舍→过程记录
**直接影响：** 无直接计算定义变更
**关联影响：** 影响交付材料，不改变指标公式或85题预期；未来出现真实范围/费用变更才履行确认。
**回归检查：** A03、A04、A05、A06
**仍待核：** 费用项细算、金额/节点/比例/期限、具体执行方及批准权限均未定。
**交付范围判断：** 不自动顺延、加费或视作已约定合同；仍需带SOW草稿/查询证据取得后续反馈。
**依据：** [W MSG-03922、MSG-03923、MSG-03924、MSG-03925、MSG-03926、MSG-03927、MSG-03928、MSG-03929、MSG-03930、MSG-03931](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json)；[TASK 第12步SOW反馈与修订](/Users/chenzhaowen/czw-code/AIFDE/W03/W03 材料包/05_作业任务书.md)

### UP-18 重分待核项与证据边界

**旧认识：** v0.4 §6全部待核清单；本周部分已获答，生产/商业仍未知
**可提炼内容：** 本期产品、端点、多卡及月报选择已有依据，转为待模型整合/实现验证；原文件和生产历史仍待取证。旧趋势/原因、活跃定义、名单条件、优惠限制、完整闭环、考核责任及授权继续未知；不把新测试定义覆盖所有旧问题。
**适用范围：** 按事项和用途标未决，非整体全开/全关
**去向：** 模型对应位置保留核心未知；缺口进度→interview_notes/model_changes；商业→SOW
**直接影响：** 无直接计算定义变更
**关联影响：** 回归85例的证据/权限/旧目标；测试预期仅作检查，不能当原始事实输入。
**回归检查：** E01、E02、E03、E04、E05、E06、T01、T02、T03、REG01、REG02
**仍待核：** 具体待核分级见unresolved列表；无已知共性规则缺口迫使暂停本次清单。
**交付范围判断：** 不以全部未知清零作为本期建模前提；进入生产/执行/验收时相应未决会约束推进。
**依据：** [BASE §1、§2、§4、§6](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)；[D3 本期统计调整](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/03_会员运营周报.md)；[L MSG-03849、MSG-03850、MSG-03855、MSG-03856、MSG-03861、MSG-03862](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)；[C MSG-03885、MSG-03886](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json)；[Z MSG-03883](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json)；[W MSG-03931、MSG-03933](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json)

## 未决项何时影响推进

| 项目 | 当前影响 | 后续门槛 | 怎样核 |
|---|---|---|---|
| 两类卡具体规则文件/历史执行凭据 | 不阻塞本期按角色确认梳理/测试；不得据此声明生产已验证 | 生产历史核验时需材料 | 已有记录指向运营核实，带具体记录请求，不循环索取已答规则 |
| 各指标字段转换、查询维度可达、账户/订单入选及数值 | 不阻塞本轮材料清单；是实现/验证必做 | 不完成不得说指标正确 | 沿38项独立覆盖计划从原始CSV形成期望并真实运行 |
| 优惠券筛选条件、真实活动实例、Excel字段、完整反馈链 | 保留未知；不用于六项资格/38指标计算，不追加作废W04条件 | 进入会员筛选或运营执行前需确认 | 具体场景/候选或查询形成后找小林及实际经手人核 |
| 生产数据、权限、清洗接入联调 | 合成测试可继续，不声称生产可用 | 生产接入前需技术/权限确认 | 老周对具体对象用途与接口条件核查 |
| 验收确认人、审批额度、执行安排责任、金额结算与付款 | 不阻塞本期模型/计算练习；SOW明确未决 | 正式签约、结算、验收、上线不可当已获批 | 带阶段成果与SOW定位公司实际授权/执行责任方，不让王经理代签 |
| 复购下降原因/旧四季可比性、活跃定义、工时收益 | 目标与假设保留；本期正确查数不能证明原因或效果 | 开展原因归因或收益承诺前另需验证 | 核原报表人群时间、记录及效果观察设计，按已有证据讨论下一阶段 |

## 下一小步

先审核本清单。通过后只准备本轮提取/维护输入：登记四份有效W03导出，更新过时goal与focus_questions，保持v2提取提示/v3维护Skill及docs/w03输出路径；先离线inspect检查，再走正式工作流的候选、审核、提案流程。配置拟议见input_plan.json，本轮未写活动配置。

实际生成候选后仍需独立审核，再用85题实际验证；本轮通过只能说明整理/影响评估有据，不是正式模型更新通过。会员筛选、自动触达、生产接入与ROI若拟纳入交付，才需另做范围、成本、授权和验证安排，不能由本清单自动承诺。

## 本次审核修正及公共影响

- REV-01：零分母直接约束全部11项比率/均值/频次，UP-07补5项遗漏；覆盖外不得返零另列全38公共约束。
- REV-02：业务材料边界与当前工具支持分写。9项月度定义启用full_month_only时，不能有任何filter或非month分组，多月按月，混合请求也受门禁。
- [指标测试计划补充](metric_plan_addendum.md)纠正旧计划“普通月内三项渠道支持待核”的表述。原冻结与85题不改，无实际运行。
