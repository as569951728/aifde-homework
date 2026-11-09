# W03 完整业务模型测试设计 v1

共 **78 例**；导师设计，待独立设计审核。所有被测模型运行均未执行。

本阅读版含预期，只供审阅。运行只用 model_questions.json 中单题输入；预期由独立审核者持有。U01/U02沿用已冻结首批内容；本套不修改原记录。完整指覆盖当前已知要求，不代表穷尽任意输入。

模型单独问答、模型加固定材料、来源审查、文档审查分别记录。旧v0.4缺W03新事实只记覆盖缺口；不倒改W02评分。

## U01 · 模型用途与业务目标
输入轨道：`model_only`；状态：未执行。

请用业务语言说明青禾这份业务模型服务哪些目标。复购原因调查、口径核查、本期查数和小林的岗位支持之间是什么关系？哪些成果能够支持下一步判断，哪些还不能说明业务效果？

应观察：
- 区分理解复购变化／支持改善选择与减少小林重复整理核对两个目标；岗位提效不证明复购改善。
- 保留沈总优先验证复购下降原因、会员老化是待验证假设；口径和记录核查是前提及当前支持路径，不偷换成全部经营目标。
- 本期可核对问数能支持范围、依据、缺口及下一步分析判断；不能从测试正确推出真实原因、三个月改善或投入回报。

拦截：
- 用“完成38项”替代原因验证目标
- 把会员老化写成已证实原因
- 把省时或复购提升写成已发生

依据：W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-0d5ba288-a623-56f1-84ac-bec076880d43-transcript.json MSG-01731、MSG-01733、MSG-01737、MSG-01739；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json MSG-01925；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03856、MSG-03860；W03/实操工程/artifacts/w03/model-understanding-design-20261106/before-extension/business_model-v0.4.md §1、§5

## U02 · 概念含义与状态区分
输入轨道：`model_only`；状态：未执行。

在当前模型中，会员账户、会员卡、等级、付费资格、活跃、购买记录和复购率分别表示什么？请说明它们的区别，并举一个同一账户同时具有不同属性或状态的例子，指出哪些状态不能相互推出。

应观察：
- 账户是本期统计标识，卡是可多张关联的权益记录，等级不等于付费资格；账户不自动等于跨系统自然人。
- 付费资格依业务范围和判定日；活跃依定义、期间、范围，是当前模型的分析属性，不是与付费／免费并列的永久第三身份；活跃定义未核时不能从无购买直接判不活跃。
- 购买是行为，由订单记录承载；复购率是有定义与范围的群体指标，定义与某期数值分开，不能当单个会员的固定身份。
- 例子中的结论条件一致，例如普通等级可有本期资格，但资格不证明发生购买，也不替代活跃定义。可接受其他有依据的例子，不要求固定措辞或本体术语。

拦截：
- 把会员、卡、账户、自然人混成一个对象
- 把活跃定义为未经确认的固定阈值或第三身份
- 把等级、资格、购买和复购任意等同

依据：W03/实操工程/artifacts/w03/model-understanding-design-20261106/before-extension/business_model-v0.4.md §2：会员、活跃、购买记录／订单、复购率；W03/实操工程/materials/w03/05_数据字典.md orders、members、cards；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03848、MSG-03854、MSG-03868、MSG-03870

## U03 · 关系、统计粒度与关联路径
输入轨道：`model_only`；状态：未执行。

请用“一个对象可以对应几个对象”的方式说明账户、卡、订单和门店之间的关系。假设账户归属A店、订单在B店成交，按成交门店查购买应归哪边？能否从现有关系确定订单使用了该账户的哪张卡？请说明依据及未知。

应观察：
- 本期一账户可多卡、可多订单；订单关联一个CRM账户和一个成交门店，记录粒度分别是账户、卡、订单，不能按卡数重复计人或订单。
- 订单成交门店与账户归属门店是不同关系；题设成交统计归B店，不因账户归属A店改为A店。
- 仅有订单到账户、卡到账户的关联，不证明订单具体使用哪张卡；不能凭同属一个账户创造订单用卡事实。
- 本期测试数据关系可用于建模，不推断生产CRM与旧POS的自然人身份已统一；无需逐字背字段名或给SQL。

拦截：
- 把归属门店当所有订单的成交门店
- 把账户的每张卡都连成订单实际用卡
- 多卡关联造成重复对象或重复订单

依据：W03/实操工程/materials/w03/05_数据字典.md orders.member_id／store_id；members.home_store_id；cards.member_id；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886、MSG-03890；W03/实操工程/materials/w03/07_客户内部沟通.md IT对接纪要

## U04 · 工作流程、角色和未知交接
输入轨道：`model_only`；状态：未执行。

小林准备一次会员优惠券活动，如果需要门店配合，模型目前能确认哪些工作步骤和交接？哪些仍是我方设计或待核？请选一个缺口，说清需要什么记录、向哪类经手人核对以及它影响什么判断。

应观察：
- 结合小林先明确面向谁／做什么、确认执行方式与协作人、跟进发放使用反馈、整理结果和未核问题的一般做法；不捏造实际某场活动的名单条件。
- 门店准备要明确范围、门店任务、工作量、现场答复和记录；陈姐与门店相关同事确认人员及执行，整理完信息不等于已安排。
- 陈姐与小林的局部活动／反馈对接已有陈述；具体后续分析者、答复返回方式和同一实例闭环仍未核，不能说完整经营闭环已运行，也不能说不存在该流程。
- 活动、反馈、名单、Excel等可按用途说明输入产出与关联；不强制都建成独立对象／系统。提出可核查的下一步并保留具体责任人未知，不擅自任命。

拦截：
- 将我方经营框架写成客户实际已运行流程
- 把未知交接写成没有交接
- 把小林个人Excel直接当统一交付数据或完整活动平台

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03858、MSG-03860、MSG-03862；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-d260d7d2-47a6-5778-9d7c-47fac88a497f-transcript.json MSG-01945、MSG-01949、MSG-01953；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03888、MSG-03890；W03/实操工程/artifacts/w03/model-understanding-design-20261106/before-extension/business_model-v0.4.md §2保留设计、§3局部流程与经营框架

## U05 · 证据性质、来源和纠错
输入轨道：`model_with_source_context`；状态：未执行。

请审查以下说法，逐条说明可采用、需要修正或尚不能判断，并给依据：A.陈姐已给本期卡日期规则，但具体文件与历史凭据未取得；B.小林独立证实之前项目全面无人使用；C.模型尚未核实反馈怎样返回门店，所以青禾没有这一环节；D.80万活跃与120万全量可直接算出活跃率；E.王经理认可分期思路，所以最终验收已获批准。

固定材料：W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json

应观察：
- A保留为正确W03角色业务规则依据与尚缺凭据的并列状态，不能因文件未得而把已回答规则全部退回未知。
- B需修正：原问题01918先带入“没人用”，01919的回应不构成独立证实；保留操作负担为个人感受，精确步骤与失败原因仍待核。
- C需修正：未核实不代表不存在；D不能直接计算，两个角色数字的口径、来源、时点仍需核实。
- E需修正：王经理提出核查意见，最终验收人、授权和批准仍未定。结论需与相应主体和来源对应，不只列一串无关引用。

拦截：
- 所有说法一概待核，忽略已有日期规则
- 截掉提问前提，把角色顺答升级为独立事实
- 用同人复述冒充多源交叉验证或凭核查意见宣布批准

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json MSG-01918、MSG-01919、MSG-01921；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-d260d7d2-47a6-5778-9d7c-47fac88a497f-transcript.json MSG-01945、MSG-01953；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-0d5ba288-a623-56f1-84ac-bec076880d43-transcript.json MSG-01719；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-c4fe490a-ddae-5bcb-a51b-f44dd796b854-transcript.json MSG-01744；W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03911、MSG-03931、MSG-03933

## U06 · 综合应用与模型分工
输入轨道：`model_with_fixed_materials`；状态：未执行。

以下仅为测试假设：本期38项指标在合成数据内已完成查询和独立核对。小林希望拿结果做优惠券活动。请结合业务模型和给定本期资料，说明结果现在能支持什么判断、还缺哪些条件、下一步由哪些角色参与。并说明卡资格规则、月末统计选择、候选名单和执行安排各应在哪里表达，哪些不能从测试正确直接推出。

固定材料：W03/实操工程/materials/w03/04_本期统计确认邮件.md；W03/实操工程/materials/w03/07_客户内部沟通.md；W01/修订记录/20261106-W03新访谈修订/docs/w01/project_assessment.md

应观察：
- 问数可帮助小林核名单和口径、发现遗漏或重复，为后续分析准备基础；没有真实业务归因、节省工时或复购改善证据。
- 卡范围、有效期与账户关系进入业务模型；本期月末时点、分子分母与完整自然月等属于指标定义；执行安排和阶段职责在流程／SOW表达，过程取舍留审核记录。可有交叉引用，不强制所有内容复制进模型正文。
- 统计人群、待审核候选和最终执行人群不同；需确认具体活动筛选条件、数据及审核／执行责任；不自动发券、联系会员或改记录，个人Excel不是独立真值或直接交付数据。
- 结合已知角色分工说明下一步：运营核业务范围与实际任务、门店按明确条件配合、IT核字段覆盖、王经理核统计与验收依据；具体未知负责人继续落实。
- 测试正确不等于生产已接通、预算／合同／正式验收批准或收益达成。必须保留“测试假设”性质，不把题设写回项目实际进度。

拦截：
- 把月末资格写成一切业务的永久规则
- 从月报购买人数直接产生已授权营销名单
- 以测试通过宣布正式上线、验收或复购改善

依据：W03/实操工程/materials/w03/04_本期统计确认邮件.md 统计选择与本阶段验收范围；W03/实操工程/materials/w03/07_客户内部沟通.md 运营群、IT纪要、范围评审；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03858、MSG-03860、MSG-03862、MSG-03868、MSG-03870；W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03911、MSG-03919、MSG-03931；W01/修订记录/20261106-W03新访谈修订/docs/w01/project_assessment.md §1、§5

## P01 · 产品与等级
输入轨道：`model_only`；状态：未执行。

仅据本期总部月报口径和下列完整卡记录，判断账户A在判定日是否有付费资格，并解释。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "account": "A", "tier": "普通", "cards_complete": true, "cards": [{"card_type": "悦享年卡", "state_on_decision_day": "有效", "card_paid_cents": 10000}]}`

应观察：
- 有资格；普通等级不能推出无资格。

拦截：
- 混淆等级、支付金额、产品范围或有效状态。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03847、MSG-03848、MSG-03853、MSG-03854；W03/实操工程/materials/w03/05_数据字典.md cards、members

## P02 · 产品与等级
输入轨道：`model_only`；状态：未执行。

仅据本期总部月报口径和下列完整卡记录，判断账户A在判定日是否有付费资格，并解释。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "account": "A", "tier": "普通", "cards_complete": true, "cards": [{"card_type": "家庭季卡", "state_on_decision_day": "有效", "card_paid_cents": 3000}]}`

应观察：
- 有资格；不能漏掉家庭季卡。

拦截：
- 混淆等级、支付金额、产品范围或有效状态。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03847、MSG-03848、MSG-03853、MSG-03854；W03/实操工程/materials/w03/05_数据字典.md cards、members

## P03 · 产品与等级
输入轨道：`model_only`；状态：未执行。

仅据本期总部月报口径和下列完整卡记录，判断账户A在判定日是否有付费资格，并解释。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "account": "A", "tier": "金卡", "cards_complete": true, "cards": [{"card_type": "悦享年卡", "state_on_decision_day": "已失效", "card_paid_cents": 10000}]}`

应观察：
- 无资格；金卡等级不能替代有效卡。

拦截：
- 混淆等级、支付金额、产品范围或有效状态。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03847、MSG-03848、MSG-03853、MSG-03854；W03/实操工程/materials/w03/05_数据字典.md cards、members

## P04 · 产品与等级
输入轨道：`model_only`；状态：未执行。

仅据本期总部月报口径和下列完整卡记录，判断账户A在判定日是否有付费资格，并解释。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "account": "A", "tier": "金卡", "cards_complete": true, "cards": [{"card_type": "异业联名卡", "state_on_decision_day": "有效", "card_paid_cents": 10000}]}`

应观察：
- 无资格；收费不能使联名卡进入本期范围。

拦截：
- 混淆等级、支付金额、产品范围或有效状态。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03847、MSG-03848、MSG-03853、MSG-03854；W03/实操工程/materials/w03/05_数据字典.md cards、members

## P05 · 产品与等级
输入轨道：`model_only`；状态：未执行。

仅据本期总部月报口径和下列完整卡记录，判断账户A在判定日是否有付费资格，并解释。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "account": "A", "tier": "普通", "cards_complete": true, "cards": [{"card_type": "体验卡", "state_on_decision_day": "有效", "card_paid_cents": 0}]}`

应观察：
- 无资格；有效状态不能代替产品纳入。

拦截：
- 混淆等级、支付金额、产品范围或有效状态。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03847、MSG-03848、MSG-03853、MSG-03854；W03/实操工程/materials/w03/05_数据字典.md cards、members

## P06 · 产品与等级
输入轨道：`model_only`；状态：未执行。

仅据本期总部月报口径和下列完整卡记录，判断账户A在判定日是否有付费资格，并解释。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "account": "A", "tier": "普通", "cards_complete": true, "cards": [{"card_type": "家庭季卡", "state_on_decision_day": "有效", "card_paid_cents": 0}]}`

应观察：
- 有资格；不能用购卡金额大于零作资格门槛。

拦截：
- 混淆等级、支付金额、产品范围或有效状态。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03847、MSG-03848、MSG-03853、MSG-03854；W03/实操工程/materials/w03/05_数据字典.md cards、members

## P07 · 信息不足
输入轨道：`model_only`；状态：未执行。

只知道账户A等级为金卡，卡记录尚未提供。能否判断其本期付费资格？还需什么信息？

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "cards_provided": false, "tier": "金卡"}`

应观察：
- 不能确认；需卡产品、判定日及有效期/终止记录。

拦截：
- 直接判有资格或无资格。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03848、MSG-03854；W03/实操工程/materials/w03/05_数据字典.md cards

## P08 · 规则适用范围
输入轨道：`model_only`；状态：未执行。

能否把本期总部月报的纳入产品范围直接推广到所有历史报表和合作方报表？请说明可用范围和下一步。

应观察：
- 仅本期总部月报；其他报表须核其范围与口径。

拦截：
- 全公司永久统一排除联名卡。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03848

## DY01 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2025-08-19"}`

应观察：
- 无效；本例区分生效前。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY02 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2025-08-20"}`

应观察：
- 有效；本例区分生效当天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY03 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2025-08-21"}`

应观察：
- 有效；本例区分生效后。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY04 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-08-19"}`

应观察：
- 有效；本例区分计划结束前一天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY05 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-08-20"}`

应观察：
- 无效；本例区分计划结束当天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY06 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-08-21"}`

应观察：
- 无效；本例区分计划结束后。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY07 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": "2026-08-15", "decision_date": "2026-08-14"}`

应观察：
- 有效；本例区分提前终止前一天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY08 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": "2026-08-15", "decision_date": "2026-08-15"}`

应观察：
- 无效；本例区分提前终止当天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY09 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": "2026-08-15", "decision_date": "2026-08-16"}`

应观察：
- 无效；本例区分提前终止后。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY10 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": "2026-08-25", "decision_date": "2026-08-20"}`

应观察：
- 无效；本例区分计划结束早于记录所填终止日。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DY11 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "悦享年卡", "valid_from": "2025-08-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-08-10", "hypothetical_run_date": "2026-08-31"}`

应观察：
- 有效；本例区分历史判定而非运行时当前状态。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ01 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-05-19"}`

应观察：
- 无效；本例区分生效前。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ02 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-05-20"}`

应观察：
- 有效；本例区分生效当天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ03 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-05-21"}`

应观察：
- 有效；本例区分生效后。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ04 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-08-19"}`

应观察：
- 有效；本例区分计划结束前一天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ05 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-08-20"}`

应观察：
- 无效；本例区分计划结束当天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ06 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-08-21"}`

应观察：
- 无效；本例区分计划结束后。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ07 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": "2026-08-15", "decision_date": "2026-08-14"}`

应观察：
- 有效；本例区分提前终止前一天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ08 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": "2026-08-15", "decision_date": "2026-08-15"}`

应观察：
- 无效；本例区分提前终止当天。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ09 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": "2026-08-15", "decision_date": "2026-08-16"}`

应观察：
- 无效；本例区分提前终止后。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ10 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": "2026-08-25", "decision_date": "2026-08-20"}`

应观察：
- 无效；本例区分计划结束早于记录所填终止日。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## DQ11 · 日期端点
输入轨道：`model_only`；状态：未执行。

在本期产品范围内，判断这张卡在指定判定日是否有效，并逐项说明日期依据。

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "card_type": "家庭季卡", "valid_from": "2026-05-20", "valid_until": "2026-08-20", "ended_at": null, "decision_date": "2026-08-10", "hypothetical_run_date": "2026-08-31"}`

应观察：
- 有效；本例区分历史判定而非运行时当前状态。开始日含，计划结束日及提前终止日不含；空终止不取消计划结束限制。

拦截：
- 日期判断相反；忽略任一日期约束；把空终止当永久有效或拿运行日代替判定日。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890；W03/实操工程/materials/w03/05_数据字典.md cards

## C01 · 多卡与订单去重
输入轨道：`model_only`；状态：未执行。

账户A有两张属于本期范围、在判定日均已确认有效的卡，并有两笔不同的有效订单O1、O2。应计几个有资格账户、几笔有效订单？关联时怎样避免错误？

人工测试输入：`{"nature": "人工构造的隔离测试情境；不是课程CSV真实行或客户实际活动", "cards": ["A-C1", "A-C2"], "orders": ["O1", "O2"], "records_complete": true}`

应观察：
- 1个账户、2笔订单。
- 先按账户确认存在合格卡，或等效去重后关联；每笔order_id只累计一次。

拦截：
- 按卡算2人或复制成4笔订单；人数对但订单翻倍。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03854；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886；W03/实操工程/materials/w03/05_数据字典.md orders、cards

## C02 · 多卡混合
输入轨道：`model_only`；状态：未执行。

A完整卡记录中有一张已确认有效的家庭季卡、一张失效悦享年卡和一张异业联名卡。A在本期有资格吗？

应观察：
- 有；存在一张合范围且有效卡即可，其他卡不否定。

拦截：
- 要求所有卡都有效或都纳入。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03853、MSG-03854；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886

## C03 · 同一卡满足条件
输入轨道：`model_only`；状态：未执行。

A完整卡记录只有失效悦享年卡和有效异业联名卡，能否合并两张卡的条件判为有资格？

应观察：
- 不能；必须同一张卡同时合范围且有效，本例无资格。

拦截：
- 从不同卡分别取类型和状态拼成资格。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03848、MSG-03854；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886

## C04 · 无卡与未知区分
输入轨道：`model_only`；状态：未执行。

已确认本期完整卡表中A没有任何卡记录，是否有本期付费资格？这与卡表未提供有何不同？

应观察：
- 完整无卡为无资格；未提供卡表为未知，不能混同。

拦截：
- 一律未知或把未提供也判无资格。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03854；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886

## C05 · 资格与行为分开
输入轨道：`model_only`；状态：未执行。

A有一张本期已确认有效卡，完整订单记录显示其当月没有有效购买。分别判断资格、购买和活跃状态。

应观察：
- 有资格；当月无有效购买；活跃须另有定义，不能仅据该条件确定。

拦截：
- 把资格当购买或默认活跃；无购买反推无资格。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03848、MSG-03868；W03/实操工程/materials/w03/03_会员运营周报.md 月内购买会员数

## R01 · 月末与购买时点
输入轨道：`model_with_fixed_materials`；状态：未执行。

人工情境：A的悦享年卡2026-08-31生效、2027-08-31计划结束、无提前终止；A在2026-08-10有一笔有效购买。8月付费购买人数是否纳入A？

固定材料：W03/实操工程/materials/w03/04_本期统计确认邮件.md

应观察：
- 纳入；8月末有资格，按月末选择账户后纳入整月有效购买。

拦截：
- 按8月10日无卡资格排除早期购买。

依据：W03/实操工程/materials/w03/04_本期统计确认邮件.md 本期统计选择；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03865、MSG-03866、MSG-03867、MSG-03868；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886

## R02 · 月末反方向
输入轨道：`model_with_fixed_materials`；状态：未执行。

人工情境：A的家庭季卡2026-06-30生效、2026-08-31计划结束、无提前终止，无其他卡；8月10日有一笔有效购买。8月付费购买人数是否纳入A？

固定材料：W03/实操工程/materials/w03/04_本期统计确认邮件.md

应观察：
- 不纳入；月底计划结束当天已无资格，购买当时有效不替代月底状态。

拦截：
- 按购买当时有效纳入。

依据：W03/实操工程/materials/w03/04_本期统计确认邮件.md 本期统计选择；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03865、MSG-03866、MSG-03867、MSG-03868；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886

## R03 · 月末有资格但未购买
输入轨道：`model_with_fixed_materials`；状态：未执行。

人工情境：A月末已确认有资格，但完整8月订单只有一笔全额退款订单；B月末也有资格但无订单。8月付费购买人数是否纳入A、B？

固定材料：W03/实操工程/materials/w03/01_订单日报说明.md；W03/实操工程/materials/w03/04_本期统计确认邮件.md

应观察：
- 均不纳入；均无当月有效购买，不把全部有资格账户当购买账户。

拦截：
- 把全退款当有效购买或计入无订单账户。

依据：W03/实操工程/materials/w03/04_本期统计确认邮件.md 本期统计选择；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03865、MSG-03866、MSG-03867、MSG-03868；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886；W03/实操工程/materials/w03/01_订单日报说明.md 有效订单数

## R04 · 整月限制
输入轨道：`model_with_fixed_materials`；状态：未执行。

要求查2026-08-10至2026-08-31（不含）的付费会员复购率，应直接计算、补问还是说明不支持？

固定材料：W03/实操工程/materials/w03/04_本期统计确认邮件.md

应观察：
- 说明本期六项付费月报仅支持完整自然月；不静默扩成整月。

拦截：
- 擅自改日期或返回不完整月的正式指标。

依据：W03/实操工程/materials/w03/04_本期统计确认邮件.md 查询范围限制；W03/实操工程/docs/w03/contract.md status

## R05 · 跨月去重
输入轨道：`model_with_fixed_materials`；状态：未执行。

人工情境：A在7月、8月各只有一笔有效订单。分别解释两个月的月内购买/复购人数；能否把两个月人数相加当成跨月唯一人数？

固定材料：W03/实操工程/materials/w03/03_会员运营周报.md

应观察：
- 各月购买人数1、复购人数0；不可合并两笔成为月内复购，也不可把1+1当跨月唯一2人。

拦截：
- 跨月凑两单或直接加去重人数。

依据：W03/实操工程/materials/w03/03_会员运营周报.md 月内购买会员数、月内复购会员数、月内复购率

## R06 · 分组与范围
输入轨道：`model_with_fixed_materials`；状态：未执行。

要求按成交门店或渠道拆8月付费会员复购率；另要求7、8月一起查。分别应如何回应？

固定材料：W03/实操工程/materials/w03/04_本期统计确认邮件.md

应观察：
- 付费六项不支持门店或渠道拆分；连续完整多月可按月分别列出，不能合并为一个总体人数/比率。

拦截：
- 任意按门店或渠道拆；多月率简单平均。

依据：W03/实操工程/materials/w03/04_本期统计确认邮件.md 六项指标及限制

## B01 · 订单分类
输入轨道：`model_with_fixed_materials`；状态：未执行。

人工订单：O1 paid实付1000退款200；O2 paid实付1000退款1000；O3 cancelled实付0退款0；O4 paid实付0退款0。分别判断支付订单与有效购买，并说明退款与优惠的区别。

固定材料：W03/实操工程/materials/w03/01_订单日报说明.md；W03/实操工程/materials/w03/05_数据字典.md

应观察：
- 支付订单O1、O2、O4；有效购买仅O1。
- 退款是支付后的累计退回，优惠为原价减实付；不能混减或用paid直接代替有效。

拦截：
- 全退/零净额/取消混入有效；将退款从优惠中抵扣。

依据：W03/实操工程/materials/w03/01_订单日报说明.md 支付、有效、退款、优惠；W03/实操工程/materials/w03/05_数据字典.md orders

## B02 · 退款归期
输入轨道：`model_with_fixed_materials`；状态：未执行。

一笔8月下单的paid订单在快照中已记录累计退款，但没有退款发生日期。能否核8月订单口径净销售额？能否据此统计9月退款现金流？

固定材料：W03/实操工程/materials/w03/01_订单日报说明.md；W03/实操工程/materials/w03/05_数据字典.md

应观察：
- 可以按8月原订单日期及快照累计退款算订单口径净额；不能推出9月退款现金流，需退款事件/时间数据。

拦截：
- 因为无退款日期阻止已定义净额；或把退款放到推测的退款月。

依据：W03/实操工程/materials/w03/01_订单日报说明.md 退款金额、净销售额；W03/实操工程/materials/w03/05_数据字典.md refund_cents

## B03 · 金额与件数
输入轨道：`model_with_fixed_materials`；状态：未执行。

人工订单原始quantity=3、paid=1000、refund=200且仍有效。有效订单商品件数计几件？能否从退款金额推出退了几件？购卡金额可否并入商品净额？

固定材料：W03/实操工程/materials/w03/01_订单日报说明.md；W03/实操工程/materials/w03/05_数据字典.md

应观察：
- 计原始3件；金额不足以推回退货件数；购卡实付不是商品订单收入。

拦截：
- 按金额比例折算2.4件或称净销量；加购卡收入。

依据：W03/实操工程/materials/w03/01_订单日报说明.md 有效订单商品件数；W03/实操工程/materials/w03/05_数据字典.md cards.card_paid_cents、orders.quantity

## B04 · 首购与窗口
输入轨道：`model_with_fixed_materials`；状态：未执行。

人工情境：同一账户全覆盖历史中最早订单取消；随后7月10日有有效订单O100、O101；8月又有有效订单O200。查8月观测期首单时应选哪笔？同日如何排序？这能叫终身首购吗？

固定材料：W03/实操工程/materials/w03/03_会员运营周报.md

应观察：
- 全覆盖有效单先按日期和订单号排序，首单O100属于7月；8月无首单，O200为后续单；不是终身首购。

拦截：
- 先筛8月后排序把O200当首单；选择取消订单；同日任意挑；声称终身。

依据：W03/实操工程/materials/w03/03_会员运营周报.md 观测期首购、首单与后续购买

## B05 · 零、未定义和越界
输入轨道：`model_with_fixed_materials`；状态：未执行。

请分别解释：覆盖内筛选无匹配订单的净额、覆盖内无购买账户月份的复购率、覆盖外月份的净额。金额13000分是否等于13000元？

固定材料：W03/实操工程/materials/w03/01_订单日报说明.md；W03/实操工程/materials/w03/02_财务邮件.md；W03/实操工程/materials/w03/03_会员运营周报.md；W03/实操工程/materials/w03/05_数据字典.md

应观察：
- 分别是可核的零净额、分母零的未定义、覆盖外不支持；13000分是130元，输出单位必须明确。

拦截：
- 统一填0；未定义变0；分/元混用。

依据：W03/实操工程/materials/w03/02_财务邮件.md 分母为零；W03/实操工程/materials/w03/03_会员运营周报.md 月内复购率；W03/实操工程/materials/w03/05_数据字典.md 覆盖、整数分；W03/实操工程/docs/w03/contract.md unsupported、units

## B06 · 维度与物理关系
输入轨道：`model_with_fixed_materials`；状态：未执行。

四张原始表各一行代表什么？关联键是什么？如果A归属甲店而O1成交乙店，两种门店统计如何区分？能否据此确定O1用了哪张卡？

固定材料：W03/实操工程/materials/w03/05_数据字典.md

应观察：
- members账户、cards卡、orders订单、stores门店；cards和orders均经member_id连账户；orders.store_id连成交店，members.home_store_id连归属店；缺订单到具体卡的键，不能指定某卡。

拦截：
- 账户当自然人；成交店等同归属店；捏造order.card_id。

依据：W03/实操工程/materials/w03/05_数据字典.md orders、members、stores、cards

## F01 · Excel用途
输入轨道：`model_only`；状态：未执行。

小林的个人Excel能否作为统一口径和交付数据直接使用？还能怎样辅助我们？

应观察：
- 不能直接作为统一统计/交付事实；可在核来源、字段和具体任务后辅助还原名单与执行记录，不一律禁止阅读。

拦截：
- 直接替代正式统计；或认为个人表完全不能参考。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03857、MSG-03858、MSG-03870

## F02 · 偏好与授权
输入轨道：`model_only`；状态：未执行。

小林更希望先支持优惠券活动，模型应如何记录？这是否改变本期查数阶段范围、授权助手发券或联系会员？

应观察：
- 记录个人优先偏好与痛点；未来支持需确认范围/条件；不等于已纳入本期或授权自动发券联系改记录。

拦截：
- 把偏好写成获批交付或自动执行授权；把助手权限限制写为小林本人无权。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03859、MSG-03860；W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03910、MSG-03911

## F03 · 实际流程与一般做法
输入轨道：`model_only`；状态：未执行。

已知小林描述活动的一般步骤，能否认定最近一次活动的名单条件、发放方式、负责同事和结果都已取得？应如何补核？

应观察：
- 不能；需选具体活动核名单来源/条件、执行与协作记录、反馈来源及结果；一般步骤不是已发生的完整实例。

拦截：
- 编出最近活动、阈值或闭环；把未知写成流程不存在。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03858、MSG-03860、MSG-03862

## F04 · 门店配合条件
输入轨道：`model_only`；状态：未执行。

助手已整理好活动信息，可否直接安排门店执行？还需明确什么，要求不清或影响考核时怎么办？

应观察：
- 明确适用范围、门店任务/工作量、现场问题责任、工作记录与考核影响；陈姐据明确安排配合，需澄清再安排；整理不等于执行获批。

拦截：
- 信息齐就视为人手、考核、执行已确认。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886、MSG-03887、MSG-03888、MSG-03890；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-d260d7d2-47a6-5778-9d7c-47fac88a497f-transcript.json MSG-01949、MSG-01953

## F05 · 局部链与完整闭环
输入轨道：`model_only`；状态：未执行。

模型确认小林协调、陈姐落实部分门店安排，是否证明策划—执行—分析—反馈—下一轮决策全链已打通？请给一个可核查的后续动作。

应观察：
- 不证明；分析接收者、反馈返回门店及下一轮决策仍缺记录。可对具体活动交接/分析/复盘记录找实际经手人核；不指定未确认人名。

拦截：
- 把局部交接写完整闭环，或未知即不存在。

依据：W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-d260d7d2-47a6-5778-9d7c-47fac88a497f-transcript.json MSG-01945、MSG-01949、MSG-01953；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03862

## F06 · 成效与活动多样性
输入轨道：`model_only`；状态：未执行。

小林觉得整理名单费力，是否已测得工时并证明这是复购下降原因？除优惠券活动，是否还有其他工作？

应观察：
- 未有工时测量或因果统计；还有权益说明与未购会员回访；效果、执行、建议采纳分别核。

拦截：
- 把感受写精确耗时/原因；把全部运营限于发券。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03856、MSG-03858、MSG-03860；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json MSG-01919、MSG-01921

## F07 · IT可做与未承诺
输入轨道：`model_only`；状态：未执行。

老周目前可配合哪些核查？开始前需说明什么？这是否意味着已获得生产访问、交付时间和真实数据？

应观察：
- 说明对象用途范围；配合取数条件、范围时间统计说明，列待补记录责任；没有生产权限/真实接入/固定交付或日期承诺。

拦截：
- 一律拒绝核查；或将配合写成已交付/批准接入。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json MSG-03873、MSG-03876、MSG-03877、MSG-03879、MSG-03881、MSG-03883

## F08 · 发放、核销与购买
输入轨道：`model_with_fixed_materials`；状态：未执行。

若取得某次优惠券发放记录，能否证明会员已核销、发生购买或复购提高？还需怎样核？

固定材料：W03/实操工程/materials/w03/07_客户内部沟通.md

应观察：
- 四种状态分开；需要核销与订单关联、范围时间、购买及比较依据，不能从发放直接推出效果。

拦截：
- 发放等于使用或促销导致改善。

依据：W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json MSG-01925；W03/实操工程/materials/w03/07_客户内部沟通.md 业务价值与验证边界；W03/实操工程/docs/w03/business_model.md §2、§4

## A01 · 阶段与责任
输入轨道：`model_only`；状态：未执行。

请说明本期阶段成果、客户和交付方分别准备什么，以及运营、IT、王经理参与核查的范围。

应观察：
- 本期合成测试内38项查询与独立核对；客户提供/确认清单、测试范围、口径、验收依据和留证；交付方查询/校验/追溯/责任草案；运营业务、IT字段覆盖、王经理统计与验收依据核查。会员筛选运营后续。

拦截：
- 写成生产上线、正式验收或已完成；漏掉独立核对。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03910、MSG-03911、MSG-03918、MSG-03919

## A02 · 核查与拍板
输入轨道：`model_only`；状态：未执行。

王经理认可总结且参与统计口径核查，可否写他最终验收、批准预算签约并授权上线？目前谁拍板？

应观察：
- 不能；只是核查意见；最终验收人、审批权限/授权额度与执行安排责任方尚待落实，不代指定。

拦截：
- 擅定王经理或沈总为最终验收批准人。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03930、MSG-03931、MSG-03932、MSG-03933

## A03 · 费用与结算
输入轨道：`model_only`；状态：未执行。

本期费用与结算条款现在可写哪些内容，哪些还不能写成约定？

应观察：
- 可列费用构成/计价依据以及拟与阶段成果记录对应；金额、节点划分、确认记录形式及付款安排待双方谈定。

拦截：
- 编金额比例或节点已获承诺。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03926、MSG-03927

## A04 · 范围变更
输入轨道：`model_only`；状态：未执行。

以后会员筛选出现超出书面支持范围的要求，应准备怎样的变更材料并由谁确认？

应观察：
- 书面说明内容、范围差异、费用责任影响；补依据后复核，具体批准权限另核；王经理只核查，不是自动批准。

拦截：
- 口头同意自动纳入；无依据加费或扩范围。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03924、MSG-03925

## A05 · 假设客户延期
输入轨道：`model_only`；状态：未执行。

以下是假设：客户迟交资料影响里程碑。项目组现在应留什么记录？继续工作、改排期和费用能否直接由王经理决定？

应观察：
- 留缺项、通知时间、实际影响、受影响/不受影响工作；执行安排方决定继续与排期；受影响排期费用双方书面确认再复核，未谈金额待定。

拦截：
- 写客户已经延期；自动顺延/加费；王经理决定执行安排。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03928、MSG-03929、MSG-03931

## A06 · 资料不足后的行动
输入轨道：`model_only`；状态：未执行。

范围草稿缺费用依据或责任不清时，王经理的核查流程是什么？是否代表项目整体永久否决？

应观察：
- 逐项记依据责任，待确认由业务补后复核；依据不足/费用不清暂缓财务确认，不是永久否决或已批准。

拦截：
- 无条件通过或扩大为永久停项。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03911、MSG-03922、MSG-03923

## E01 · 提问前提
输入轨道：`model_with_source_context`；状态：未执行。

阅读给定W02小林二访MSG-01918/01919及01921。“之前项目没人用”“多了三步”分别应如何记录与使用？

固定材料：W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json

应观察：
- “没人用”前提出自问题，原回答沿用，不算独立证实全面使用情况/原因；三步为个人感受非精确测量；保留原问答，核具体任务。

拦截：
- 把学员前提改写小林独立事实；删原问答或把感受精确化。

依据：W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json MSG-01918、MSG-01919、MSG-01921

## E02 · 经营假设
输入轨道：`model_only`；状态：未执行。

复购连续四季下滑、会员老化、三个月希望看到改善，应分别作为哪类信息？本期月报测试能证明什么？

应观察：
- 四季下降是角色报告未独立复算；老化为待验原因；三个月为期望；本期正确查询支持口径和查数，不能直接证明旧趋势原因或收益。

拦截：
- 把老化因果、收益或三个月承诺写为事实。

依据：W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-0d5ba288-a623-56f1-84ac-bec076880d43-transcript.json MSG-01719、MSG-01731、MSG-01739；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03856

## E03 · 不同统计总体
输入轨道：`model_only`；状态：未执行。

沈总说80万活跃，老周说120万系统全量，可否直接算活跃率、相减作沉睡人数或认定同口径矛盾？

应观察：
- 不可；先核来源、定义、时间、覆盖和去重，不能由两个不同总体直接推率/差值或矛盾。

拦截：
- 给出66.7%或40万作为业务结论。

依据：W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-0d5ba288-a623-56f1-84ac-bec076880d43-transcript.json MSG-01719；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-c4fe490a-ddae-5bcb-a51b-f44dd796b854-transcript.json MSG-01744

## E04 · 新规则与旧未知
输入轨道：`model_with_source_context`；状态：未执行。

小林、老周先说日期不掌握，陈姐随后在两类卡的提问限定下给出日期规则但没掌握文件/历史凭据。现在可以怎样更新模型，哪些继续待核？

固定材料：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json；W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json

应观察：
- 可在本期两类卡测试范围采用陈姐角色确认的日期规则；旧不掌握不是反规则冲突。文件、历史执行、生产普适性另待核，不能一律阻塞测试范围更新。

拦截：
- 继续把全部日期规则写未知；或写生产历史已验证/所有产品通用。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03849、MSG-03850；W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json MSG-03874、MSG-03875；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886、MSG-03889、MSG-03890

## E05 · 失效来源拒绝
输入轨道：`model_only`；状态：未执行。

某备忘声称每周一从CRM拉60天未购、排除员工并核勿扰名单。经来源核验，该说法只来自已作废W04会议5e112925-9605-5362-b908-1ef8849d9c5f，未获有效W03来源支持。应否加入当前模型？应保留什么状态？

应观察：
- 不作为W03事实、条件或缺口关闭依据；作废归档保留，真实名单条件待正确资料核实。

拦截：
- 混入当前事实或以曾在对话出现为依据。

依据：W03/实操工程/AGENTS.md 作废W04规则；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03858、MSG-03860、MSG-03862

## E06 · 提问限定与总结认可
输入轨道：`model_with_source_context`；状态：未执行。

对给定陈姐03885/03886、王经理03910/03911/03932/03933，分别说明提问提供的范围、角色新增答复和总结认可的边界。

固定材料：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json；W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json

应观察：
- 陈姐答复范围为两类卡本期月报；王经理讨论学员阶段草案并补四类说明；总结认可须连前文，不变成客户主动提出全部方案或正式批准。

拦截：
- 省略问句范围外推；把总结认可当签约批准。

依据：W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03885、MSG-03886；W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json MSG-03910、MSG-03911、MSG-03932、MSG-03933

## T01 · 正文与过程分离
输入轨道：`artifact_review`；状态：未执行。

审核候选业务模型及其修订说明：业务对象、关系、规则、流程与待核是否可直接阅读？证据取舍、导师调整、提问前提纠错和测试成绩分别放在哪里？

应观察：
- 模型正文讲业务；取舍/问答归属/过程和测试记录分置可追溯文件；允许必要业务来源注记，不强迫把审计过程放正文。

拦截：
- 正文写成长篇逐条取舍过程；删除审计记录；把导师代拟记本人独立完成。

依据：AGENTS.md 保留原话与学习记录边界；W03/W03 材料包/05_作业任务书.md 模型更新与验证

## T02 · 证据与字段审计
输入轨道：`artifact_review`；状态：未执行。

逐条抽查候选模型中所有新增“已确认”语句、引用和字段：能否回到完整问答或本期材料？是否把教师例子、推测字段或测试覆盖变成客户生产事实？

固定材料：W03/实操工程/materials/w03/01_订单日报说明.md；W03/实操工程/materials/w03/02_财务邮件.md；W03/实操工程/materials/w03/03_会员运营周报.md；W03/实操工程/materials/w03/04_本期统计确认邮件.md；W03/实操工程/materials/w03/05_数据字典.md；W03/实操工程/materials/w03/06_任务清单.md；W03/实操工程/materials/w03/07_客户内部沟通.md；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json；W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json；W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json

应观察：
- 所有新增采用有准确来源、范围与性质；无课堂/参考/作废来源污染；字典实际字段与建议属性分开；复核源片段而非仅检查文件存在。

拦截：
- 假引用、只看回答不看前提、无据字段、合成测试冒充生产。

依据：AGENTS.md 案例与来源；W03/实操工程/materials/w03/05_数据字典.md 数据接入层；W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json MSG-03875、MSG-03877

## T03 · 历史回归与版本
输入轨道：`artifact_review`；状态：未执行。

比较W02 v0.4和W03候选：哪些经营目标、关系、流程和权限须保留，哪些旧待核可据本周更新？怎样保存前后结果？

固定材料：W03/实操工程/docs/w03/business_model.md；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json；W03/实操工程/materials/w03/04_本期统计确认邮件.md

应观察：
- 保留业务目标、局部流程和权限；更新本期产品/日期/账户/月报选择等已得证据；原未知不能永远冻结，也不能扩成生产已核；保留原模型与旧评分，候选/设计/实际问答分版本。

拦截：
- 覆盖W02基线或倒改旧评分；只剩六项月报；新规则与旧未知自相矛盾。

依据：W03/实操工程/docs/w03/business_model.md §1至§7；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03848、MSG-03868；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886；W03/W03 材料包/05_作业任务书.md 模型更新

## REG01 · W02原题回归
输入轨道：`model_only`；状态：未执行。

青禾准备先给小林和陈姐提供会员运营支持，你会建议第一版交付什么、怎样接到实际工作，以及怎样判断有没有帮助？

应观察：
- 沿用旧题中有来源的经营目标、岗位/流程、证据和权限边界。
- 新增本期规则可在限定范围内修正旧未知；未给生产证据/筛选条件/效果的部分仍未知。
- 具体分项基准见legacy_invariants，更新取舍另留记录，不能按字面旧答案惩罚有据修订。

拦截：
- 丢失旧目标/权限；把候选当执行；抄旧未知阻塞有证据更新。

原题应保留的分项判断：
- 结合小林的需关注会员及每条建议依据，解释输出要减少原有整理核对；筛选规则、Excel语义仍未知，不声称已生成名单或省时。
- 结合陈姐的适用范围、参与门店、任务、答复责任和待核事项，区分信息整理与人员、工作量、执行和工作记录确认；具体答复人仍待核。
- 两类会员按活动范围分别核查，不预设要求不同；不将候选整理方案当已批准或已运行系统。
- 用陈姐前中后观察方向提出未来验证，区分期望、试用、实际效果；小林提效与复购结果分别验证，不声称反馈闭环已通。

依据：W03/实操工程/customer/w02/knowledge_cases_v0.3.json QH-KNOW-01；W03/实操工程/docs/w03/business_model.md §1至§7；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03848、MSG-03860、MSG-03868；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-0d5ba288-a623-56f1-84ac-bec076880d43-transcript.json MSG-01731、MSG-01739；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json MSG-01925

## REG02 · W02原题回归
输入轨道：`model_only`；状态：未执行。

结合青禾目前的情况，你建议第一阶段优先解决什么问题、形成什么阶段交付，供沈总判断下一步怎样推进？请说明理由。

应观察：
- 沿用旧题中有来源的经营目标、岗位/流程、证据和权限边界。
- 新增本期规则可在限定范围内修正旧未知；未给生产证据/筛选条件/效果的部分仍未知。
- 具体分项基准见legacy_invariants，更新取舍另留记录，不能按字面旧答案惩罚有据修订。

拦截：
- 丢失旧目标/权限；把候选当执行；抄旧未知阻塞有证据更新。

原题应保留的分项判断：
- 识别经营方向为复购止跌回升，首阶段优先验证复购下滑原因，先对齐会员范围和复购口径；会员老化是沈总优先检验的假设，不能当已知原因或排除其他待验证解释。
- 阶段讨论材料说明业务问题、覆盖范围、已有依据、待核项、需要谁配合和阶段结果如何观察；不只列通用进度表、上线功能或岗位工具。
- 范围应考虑两类会员、期间和渠道等必要边界；不把80万活跃与120万系统全量混用，不编造复购公式、数据可得性或分析结果。
- 结合已知参与范围说明协作，区分沈总定优先级及推动待决、小林运营、老周数据条件、陈姐门店实际情况；未知的最终定义人、分析责任、材料交付与日期继续待核，不擅自任命或许诺。
- 保留小林提效目标，将陈姐信息整理作为岗位支持候选，不宣告其为第一阶段目标或必建系统；详细设计、试点批准、实际执行与经营效果分开。
- 能根据取得了什么依据、排除了或保留了什么假设、缺口和后续验证安排说明阶段进展；具体观察办法只能作为建议，不伪造已取得数据、已验证原因、已批准试点或三个月量化承诺。

依据：W03/实操工程/customer/w02/knowledge_cases_v0.3.json QH-KNOW-02；W03/实操工程/docs/w03/business_model.md §1至§7；W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json MSG-03848、MSG-03860、MSG-03868；W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json MSG-03886；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-0d5ba288-a623-56f1-84ac-bec076880d43-transcript.json MSG-01731、MSG-01739；W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json MSG-01925

