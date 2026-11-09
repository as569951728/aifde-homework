# W03实际首稿独立正文审核（review-01）

**结论：需修订，T01、T02、T03均未通过本版静态审核；目前不应把draft-01视为可直接采用的已通过草稿。** 五节结构、双目标、账户/卡/资格与日期主规则已实质改善。剩余问题均可按现有来源修复，`human_decisions=[]`，无需新增访谈或让用户重复选择。

审核对象是实际`draft-01`的完整正文、notes、summary、diff和proposal，不以先前反馈文本或设计建议代替成品。proposal/body哈希与主Agent交付一致，导出文本逐项与proposal一致；正式模型及notes仍等于proposal的base_hashes。

- proposal：`03418b1a56aa00a53dcfba300e5c1456b67919161ecae2b68252a514273fd548`
- 正文：`94ad8ace10d1580429bce05a5860ea3ffdd923e996eb759897157ccedbacf19f`
- 原生5组共有20项收到反馈；proposal列18项用于正文或notes承接，另外2项只记来源。

## 优先修正

先修业务含义：未知回流与门店安排状态、券流程作用域、原因判断及动作主体；随后落实正文迁出和统计范围分层，再修引用及关键旧知识遗漏。无需重写全部模型或扩测试。

## R01 · P1 · 流程表出现未经证明的回流与安排状态，并把券流程套到全部工作

位置：business_model.md:54–56。

**实际内容：** 54行“日常会员运营”同时列权益说明、回访，却统一接“发放与使用反馈”；55行写“门店依据同一套有效期规则逐卡核对…但完整门店任务尚未安排”；56行写“反馈汇入下一轮安排”。

**问题与影响：** 03862只说明优惠券活动的一般做法；03888是本期门店可协助核对的内容和条件，不能变成所有活动的固定步骤或现实任务未安排。反馈整理/已有任务反馈触发不证明处理结果实际汇入下一轮，且同一行又把衔接留未知。

**原始依据：**

- [L](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)，MSG-03862：“拿我经手的会员优惠券活动来说”限定流程类型；具体哪次及筛选条件不能确认。
- [C](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json)，MSG-03888：“门店能协助核对的是”及“我才好安排门店配合”是能力/条件，非已执行或确定未安排。
- [HC2](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-d260d7d2-47a6-5778-9d7c-47fac88a497f-transcript.json)，MSG-01945、01953：反馈后的处理答复或调整安排及返回门店方式不掌握。
- [HL2](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json)，MSG-01913：“这次要做什么”来自未做完任务和反馈；这是一般方式，不是实例闭环。

**最小修法：** 先列三种工作类型；通用步骤写准备/协作/跟进/反馈，另用券活动例说明发放与使用。删“完整门店任务尚未安排”，本期逐卡核对能力放核查记录。56行产出改为“整理后的反馈与未核问题；是否及怎样进入下一轮安排待核”。保留原来有来源的小林—陈姐局部交接。

**验证/逆例：** 静态重读U04/F03–F05所要求的范围：权益说明不得被解释成发券；提供整理结果不得推出已回流/已排期/确无安排。

## R02 · P1 · 将不确定判断改为否定意见，且notes再次混淆动作主体与审批概念

位置：business_model.md:60；notes_update.md:27；notes_update.md:30。

**实际内容：** “她…也不认为这是复购下滑的原因”；“小林不会单独定人群、自动发券、联系会员或改记录（MSG-03860）”；“审批流程…均未定”。

**问题与影响：** 不能说明原因不等于认为不是原因；03860禁止的是助手自动动作，不能把小林本人限制成不能改记录。03931已提公司内部审批流程，只说本次审批安排/具体权限未定，不能改成流程本身未定。

**原始依据：**

- [L](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)，MSG-03856：“我没量过工时，也不能说它就是复购下滑的原因”。
- [L](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)，MSG-03860、03862：03860为“我不会让助手自动发券、联系会员或改记录”；03862另说明她不单独定人群等。
- [W](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-92c91632-4b0e-5a7a-bd7d-55214f68ee39-transcript.json)，MSG-03931：“得由公司内部按审批流程定”与“审批安排还没定”。

**最小修法：** 60行改为“未量化工时，也不能据此认定复购下滑原因”。notes27分开写“人群/方案需业务确认；不让助手自动发券、联系会员或改记录”，不要将不同句的主体合并。notes30将“审批流程”收准为“本期审批安排与具体审批权限”，保留公司有内部流程的原话边界。

**验证/逆例：** 问“是否已排除重复整理为原因”应答未得依据；问“小林不能改业务记录吗”不得从助手限制推出；问“公司没有审批流程吗”不得肯定。

## R03 · P1 · 已定的正文迁移尚未落实，summary/notes却称已迁出

位置：business_model.md:7、11、13、17–29、34–35、48、57、68、75；notes_update.md:15–17；summary.md:1。

**实际内容：** 正文仍有试点批准/验收未落实、权限批准、暂停接入、数据/日期承诺、测试验收、具体查询月份/核对证据；同时保留“保留理由/高重要”“学员建模选择”、载体取舍及“无购买参与者也应能被观察”的设计要求。summary称FDE验收及阶段框架/取舍理由不进正文。

**问题与影响：** 用户已定业务正文只留青禾业务知识，FDE接入、交付/验收/批准和维护过程应分流。个人Excel本身确已迁出，不能因此声称整体迁移完成。真实业务角色和门店条件仍应保留，不能全部删除。

**原始依据：**

- [USER](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w03/model-input-preflight-20261106/user_decisions.json)，excel_disposition、delivery_disposition：个人载体不入正文；FDE项目费用/延期/交付/验收批准等进入SOW/记录，保留真实业务工作。
- [OLD](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/docs/w03/business_model.md)，26、28、30、52–53、65行：旧稿候选/设计/个人载体和接入事项是待迁移基线，不是新稿必须继承的业务事实。

**最小修法：** 正文保留复购目标、三个月期望与业务未量化边界，迁出项目批准/验收/接入承诺。数据协作只留理解业务范围/字段/记录的业务角色，不留FDE交付及审批状态。移68行查询执行待办和75行接入批准；历史业务状态能否还原单独保留。对象表保留必要来源，移“保留理由/高重要”与学员取舍；34–35行只留必要实际业务用途/未知，把设计目标迁notes。随后重写summary的迁移完成陈述，使其与实际草稿一致。

**验证/逆例：** T01/T03逐段查：不得以换名保留FDE或个人载体；也不得删掉真实名单用途、角色动作和门店前置条件。

## R04 · P1 · 退款排除条件和统计范围被压缩到含混表达，分层仍不完整

位置：business_model.md:41、43；notes_update.md:20–23。

**实际内容：** 43行“有效购买与退款归属…退款按原订单日期归属，取消与全额退款不计”；41行仍把“本期月报取月末”附在通用权益端点规则中。notes23把完整月/全渠道/全门店、分子分母、退款/首单/字段SQL混成一串“其余本月继承项”。

**问题与影响：** “全退不计”只针对有效购买；全退paid订单仍计支付订单和退款订单/退款金额，不能在退款归属句中无对象排除。月末选择及退款归期应有指标层单一落点；完整月/全渠道等不能泛化到全部38项或全部通用报表。

**原始依据：**

- [D1](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/01_订单日报说明.md)，11、15、23、35–43行：支付包括后来全退；有效订单排除全退；退款订单含部分及全部退款；退款额为paid订单累计。
- [D2](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/02_财务邮件.md)，5行：取消、全额退款不计有效购买，退款按原订单日期归属。
- [D3](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/03_会员运营周报.md)，9、13–37行：注册/观测期指标和月内三项不同；三项月内指标明确整月/全门店。
- [D4](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/04_本期统计确认邮件.md)，5、9、13–33行：六项付费月报限定完整月、全渠道/全门店、月末资格与整月购买。

**最小修法：** 43行仅写“有效购买沿用第2节，取消和全额退款不计入有效购买”；退款归期迁指标承接。41行保留按指定日判定，改简短指向具体指标口径而非把月末并入端点规则。notes23分三类：六项付费月报按04；三项普通月内指标按03；其余通用指标按01–03各自定义，不统一加月度/付费过滤。无须抄38项公式，但明确归期/首单/零分母各依什么定义。

**验证/逆例：** 全退paid单的支付/退款统计仍纳入、有效购买排除；普通订单日期窗口不因notes被强制改成整月；R01–R07/B01–B06仍沿各题指定材料。这里只作静态审查，未实际运行。

## R05 · P2 · 修正不存在的消息标识、角色错挂和不能支持断言的引用，并收准审查人数说明

位置：business_model.md:19–24、28、39；summary.md:1；proposal.json:claim_ids/human_reviews。

**实际内容：** 39行“MS丛-03854”是损坏标识；28行将MSG-01648列在“陈姐、老周”后；23行将门店关系归于01932与无明确定位的核查记录；20行购卡金额属性/收入区别没有给字典直接来源。summary写五组“18项原生已审ID”。

**问题与影响：** 损坏ID与真实ID但支持范围不符应区别处理。01932真实存在但回答是渠道及对应字段不掌握，不证明成交/归属门店关系；01648真实但角色是小林。五组human_reviews含20个不同原生ID，claim_ids是18个实际采用/承接ID，两个计数不能混成18项已审。

**原始依据：**

- [HL1](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-d70b1629-b176-53d1-8357-f195328c0193-transcript.json)，MSG-01648；role_id=ROLE-LIN：券发放/核销区分由小林说明。
- [HZ2](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-14af3b0b-9103-56ac-97bb-eb35cd50832d-transcript.json)，MSG-01932：有线上/门店渠道；具体关联字段无可确认说明。
- [D5](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)，12–13、28–31、45–55行：账户/门店关系、卡属性和购卡款语义的直接来源。
- [L](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)，MSG-03848、03854：产品范围/资格；不提供完整物理属性表。

**最小修法：** 纠正MS丛为MSG，01648归小林；字典直接支持对象/门店/卡属性，旧访谈只支持其确实说明的范围，不用未知回答给新关系背书。当前属性/历史缺项明确写“本期资料未提供变更历史”，不是公司无历史。summary改为“五组20项收到主导师依据既有独立审查录入的反馈，其中18项用于正文或notes承接”；这次实际正文独立审查结论另记，不暗示5组新反馈逐组独立通过。

**验证/逆例：** 核每一出处存在且主体/断言匹配；复核20 reviewed、18 included、2 only-source/deferred。不得只做字符串存在检查。

## R06 · P2 · 恢复被删掉的关键业务输入、使用目的与既有观察条件

位置：business_model.md:54、58、60；model.diff:原v0.4第30、36、49、51、61–62行的删除部分。

**实际内容：** 日常流程输入列变成活动类型枚举，原“未完任务与反馈”触发消失；模型保留岗位负担但未再说明关注会员/建议依据及核对漏重的具体用途；导购已有注册指标和陈姐明确的前/中/后观察条件也只剩笼统考核未知。

**问题与影响：** 这些是已获来源的业务工作与使用判断，不是个人Excel或FDE验收条款。将导师阶段建议迁出不应一并丢掉陈姐自己的观察方式。双目标仍在，但缺少实际输入和判断用途会使正文更接近规则目录。

**原始依据：**

- [HL2](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-4abeb711-5ac6-500b-a2e7-ad7a131a85d7-transcript.json)，MSG-01913、01925：任务触发为未完任务/反馈；希望关注会员和建议依据，减少原有整理核对。
- [L](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)，MSG-03866–03870：查数用于核名单与口径、找遗漏/重复，非已生成营销人群。
- [HC1](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-33120509-3939-5d6c-81f1-3959fed49789-transcript.json)，MSG-01685：已知导购有会员注册指标，完整构成/口径未知。
- [HC2](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-d260d7d2-47a6-5778-9d7c-47fac88a497f-transcript.json)，MSG-01951、01953：希望开始时清楚、执行中少来回确认、结束后重复问题减少；尚未实际试验。

**最小修法：** 用少量句子恢复：未完任务/反馈是通用触发，类型单列；关注会员及建议依据、问数查漏重是期望用途；统计人群、待审核候选、实际执行人群不同；导购已有注册指标但完整口径未知；门店信息整理的观察条件来自陈姐，未测量效果。无需恢复整个旧候选支持表或导师设计段。

**验证/逆例：** U01/U04及REG01–REG02静态覆盖检查；问“提效具体看什么”能回答有来源观察，但不得称已节省工时；月报账户数不得自动成为已批准触达名单。

## R07 · P2 · 未决表仍把本期已知关系与历史/生产未知捆在一起

位置：business_model.md:20–21、66–67、71、75。

**实际内容：** 71行将“会员—订单—优惠／活动追踪的关联、历史资格还原、自然人统一”一起写为“字段与关联待样例核”；67行未限定生产/历史却再问空终止填写一致性；20行称卡是“资格判断的唯一载体”，21行称其为“月报人群与名单口径的共同基础”。

**问题与影响：** 本期字典已给账户—订单、账户—卡关系，陈姐已给本期空值含义；真正缺的是优惠/活动追踪关系、生产历史证据等。宽泛未知可能重新阻断本期工作。卡资格是本期月报规则，活动筛选条件未确认，不能由此默认所有运营名单都共用这一资格条件。

**原始依据：**

- [D5](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/materials/w03/05_数据字典.md)，12–13、28–31、45–55行：本期关系已给定，不能继续整体待核。
- [C](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json)，MSG-03885–03890：本期两类卡端点/空值已有角色说明；缺具体文件与历史凭据。
- [Z](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json)，MSG-03873、03875：不掌握解释及测试不等生产的边界，不是相反规则。
- [L](/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程/artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json)，MSG-03848、03862：资格只约束本期月报；具体活动选人条件未确认。

**最小修法：** 71行拆为本期关系已知与“优惠/活动追踪关联、生产历史及自然人关系仍待核”；67行如保留明确为生产/历史填写与凭据核验，不重新打开本期空值解释。20–21行将“唯一/共同基础”收准为本期月报资格判断依据；活动名单按其独立业务条件确认。历史业务状态还原保留业务未知，接入权限按R03迁出。

**验证/逆例：** E04/T03静态核对：不能因生产凭据缺失拒绝本期规则起草；不能将月报资格推广成优惠券目标人群的必选条件。

## T01–T03逐项结果

| 项 | 结果 | 实际证据/位置与理由 | 问题 |
| --- | --- | --- | --- |
| T01-1 | pass | business_model.md:3–9、15、37、50、62；正文五节清楚，双目标仍在；本项通过不抵消下列实质错误。 | — |
| T01-2 | needs_revision | business_model.md:41、43; notes_update.md:23；统计选择及退款归期仍并入业务规则，notes作用域混写。 | R04 |
| T01-3 | needs_revision | business_model.md:48、57、68、75；Excel已迁出，但FDE接入/交付/批准/执行证据仍进正文。 | R03 |
| T01-4 | needs_revision | business_model.md:54–56、60；局部交接保留，但流程类型、触发和回流状态失真/遗漏。 | R01, R06 |
| T01-5 | needs_revision | business_model.md:17–35；保留理由、高重要、学员取舍及设计观察要求仍混取舍过程。 | R03 |
| T02-1 | pass | business_model.md:19–25、31–33；账户/卡/派生资格已拆，一对多、两类门店关系及不猜订单用卡已表达；需R05/R07收准来源及范围。 | — |
| T02-2 | pass | business_model.md:39–42、66；本期产品、同卡同时满足、日期端点、空值不无限和多卡去重语义正确；不将文件未知否定角色说明。 | — |
| T02-3 | needs_revision | business_model.md:25、43；第2节有效购买/快照/件数正确，但第3节退款压缩句可能扩大排除对象。 | R04 |
| T02-4 | needs_revision | business_model.md:20–21、67、71；已知本期关系和历史生产未知尚未拆清，活动名单范围也未收准。 | R07 |
| T02-5 | needs_revision | business_model.md:54–56；未知回流变实际输出，可协助核对变固定门店动作。 | R01 |
| T02-6 | needs_revision | business_model.md:23、28、39、60; notes_update.md:27、30；存在极性、主体/角色、审批词义、损坏ID与证据范围错配。 | R02, R05 |
| T03-1 | needs_revision | business_model.md:5–9、46、54、58、60; model.diff；双目标/80万120万/助手限制仍在，但真实触发、用途、注册指标及门店观察条件有回归遗漏。 | R06 |
| T03-2 | needs_revision | business_model.md:39–42、67、71；日期规则已进，旧关系未知仍有过宽保留。 | R07 |
| T03-3 | needs_revision | notes_update.md:13–17; business_model.md:48、57、68、75；旧购买时点与Excel迁出正确，FDE及维护过程未迁净；无须回填旧排除内容。 | R03 |
| T03-4 | needs_revision | summary.md:1; proposal.json:claim_ids/human_reviews/base_hashes；正式基线未变、proposal尚未apply/运行状态正确；summary未分20反馈与18使用及审核主体。 | R05 |

局部pass只说明对应内容已满足静态要求，不能抵消其他必要项。T02-1、T02-2确认核心对象与日期语义已有改善，不撤销；整体仍需修订。

## D01–D05落实状态

| 前轮设计问题 | 本稿状态 | 剩余修订 |
| --- | --- | --- |
| D01 | substantially_implemented_with_remaining_scope_and_citation_fixes | R05, R07 |
| D02 | partially_resolved | R04 |
| D03 | partially_resolved | R04, R07 |
| D04 | needs_revision | R01, R06 |
| D05 | needs_revision | R03 |

## 结论边界

本轮未编辑草稿、正式模型、notes、工作流或Skill；没有模型API调用、85题问答或38项指标执行。主Agent可依据这些源内可解决问题沿既有流程修订，保留首稿；收到新proposal与hash后只复核修订及相关回归。

来源库存与完整逐项结构见[review-01.json](review-01.json)。沿用前轮source-first判据，针对本稿疑点回读原MD和消息；没有重新遍历全部48文件，也没有将父Agent观察当作独立事实来源。

## 审阅副本可读性（低优先，不影响语义结论）

N01（P3）：正文77行的`interview_notes.md`相对链接在`draft-01`目录下没有对应文件，当前审阅副本不能直接打开；正式`docs/w03/interview_notes.md`存在。可给审阅副本补清楚的导航或说明正式落点，不要为草稿预览永久改坏正式文档的相对路径。
