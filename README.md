# FDE 课程作业：青禾优选

学员：陈昭文。W01、W02原提交保留，W03在独立目录中接续业务模型更新、指标构建与校验、Agent接入验证和阶段范围确认。

## W03：把客户口径接入运营 Agent

1. [阶段范围稿 SOW v0.2（含客户四段核查反馈与未决事项）](w03/docs/w03/sow.md)
2. [访谈记录：多角色首访与第二轮 SOW 核查](w03/docs/w03/interview_notes.md)
3. [业务模型 v0.5](w03/docs/w03/business_model.md)、[本周变更与第 5 步四项核对](w03/docs/w03/model_changes.md)
4. [指标核对与测试登记](w03/docs/w03/指标核对与测试登记.md)、[指标库目录（38 项，逐项带来源与原文引文）](w03/artifacts/w03/library/catalog.json)
5. [测试报告](w03/artifacts/w03/metric_test_report.json)、[预检结果](w03/artifacts/w03/precheck.json)
6. [运营聊天入口真实问数留证（5 问）](w03/artifacts/w03/chat-verification/summary.json)
7. [业务模型测试记录索引](w03/docs/w03/业务模型测试记录索引.md)、[变更单 CR-01](w03/docs/w03/变更单-B7-C01.md)、[artifacts 目录导航](w03/artifacts/w03/README.md)

本周完成 38 项指标（32 项通用报表＋6 项月末付费会员月报）的定义、字段映射与来源追溯；小样本 51 个用例覆盖 38/38，数值、状态、意图、分组、单位全部通过；规模集 15 例，数值 13 例通过、越界拒绝 2 例按预期拒绝，期望由独立脚本直读 30 万行 CSV 算出；判定程序 9 类 10 个错误注入全部被拒，2 个控制组通过。自然语言解释逐条人工核查 51 条中 46 条通过，5 条存在表述缺陷，保留原始失败记录与纠正稿，未用修复覆盖原分。

**已知缺口与未决，不作验收通过声明：** ①「本月」等未指定月份的相对时间问法直接返回不支持、未先澄清，已列为验收缺口并出变更单 CR-01，是否纳入本期待客户方确认；②卡表若缺少会员卡记录，实现无法区分“数据缺失”与“确实无卡”，依赖客户保证卡表完整；③38 项清单待运营侧逐项书面确认；④费用构成已逐项列出，各项金额与计价依据待双方谈定。以上均不构成验收通过、复购提升或投资回报。

## W02：业务诊断与业务模型

1. [本周阅读入口、证据索引与人工复核](w02/docs/w02/interview_notes.md)
2. [青禾优选会员经营业务模型v0.3](w02/docs/w02/business_model.md)
3. [项目阶段目标：有／无业务模型实际回答](w02/artifacts/w02/knowledge_reviews/PAIR-f79da9eb58634930a604724f3c40b339/answers.md)
4. [小林、陈姐岗位支持：有／无业务模型实际回答](w02/artifacts/w02/knowledge_reviews/PAIR-498bac0718d74f4ead47a490b40fae6d/answers.md)
5. [课程预检记录](w02/artifacts/w02/submission_checks/20261030-v0.3/workspace-final.json)与[GAP-003迁移说明](w02/artifacts/w02/submission_checks/20261030-v0.3/fit_gap_migration.json)

已保留本人访谈、实际提取、Skill改版验证、人工取舍、旧模型及对照迭代。最后两组使用对照由导师执行；学员已确认模型修订及最终三项核心判读，原话为“认可这三点，按导师代拟、本人确认记录”。[最终判读与确认记录](w02/docs/w02/final_comparison_review.md)保留来源，不冒充学员独立运行或逐字原创。没有客户经营数据、实际试点、提效或复购改善结果；角色原话、学员选择与导师设计分开。

**GAP-003专项人工复核已完成：** 导师核对老师批改、原始问答、迁移去向及3份原证据后，认为迁移有依据、内容和证据未遗失，继续保留五项客户诉求。自动预检仍为needs_revision，仅D04/W1_IDS_MISSING，因为检查器只比较现行items的编号，不读取迁移说明。详见[人工复核及证据映射](w02/artifacts/w02/submission_checks/20261030-v0.3/gap003-manual-review.json)和[复核后预检](w02/artifacts/w02/submission_checks/20261030-v0.3/workspace-after-gap003-review.json)。原提示保留，九项机器人工队列仍pending；这是导师内容判断，不是教师验收或课程通过。

## W01：原提交版

[原提交固定版本与全部阅读入口](https://github.com/as569951728/aifde-homework/tree/cbdafbaffe5776bcc7082a28ed38b8a446bb6168)。W01目录原文保留；老师批改的接续修订放在W02，不覆盖原提交。W01已收到批改，W02的发布、课程表单提交和批改状态分别记录。

## 目录与复核说明

w02内部按课程任务书保持docs/w02、customer/w02、artifacts/w02和artifacts/w01/product_fit_gap.json。独立ZIP解压根目录直接是docs、customer、artifacts；仓库目录w02仅提供在线导航。

w03内部保持 docs/w03、customer/w03、artifacts/w03，并附带本期引用的 customer/w02 与 artifacts/w02/{runs,workflows,sources}；独立提交包解压根目录同为 docs、customer、artifacts。w03 不含未改动的完整工程和虚拟环境。

本周按任务书不附未改动的完整工程和虚拟环境。复核者使用W02课程工程中的tools/check_w02.py，将workspace指向w02目录；如需真实重跑，把本包对应目录放入独立W02课程工程并自行配置模型凭据。原运行保留实现快照，便于追溯；不使用W01检查器核W02。

本轮本地材料整理日期：2026-10-30，r3最终确认版。仓库上传不等于已向W02课程表单提交；W02具体课程页面及截止时间仍以班期通知为准。

W03 本轮材料整理日期：2026-11-09，SOW 已按客户第二轮四段核查意见修订至 v0.2。仓库上传不等于已向课程表单提交；W03 具体课程页面及截止时间仍以班期通知为准。
