# FDE 课程作业：青禾优选

学员：陈昭文。W01、W02原提交保留，W03在独立目录中接续业务模型更新、指标构建与校验、Agent接入验证和阶段范围确认。

## W04：把原始数据接进标准产品，跑通第一个 demo

1. [数据诊断报告（六章，含工作账与 CRM 对照）](w04/docs/w04/data_diagnosis.md)
2. [业务模型（本周按访谈修订 8 处）](w04/docs/w04/business_model.md)、[模型修订记录](w04/docs/w04/model_changes.md)、[指标修订记录](w04/docs/w04/metric_changes.md)
3. [清洗规则（9 条）](w04/artifacts/w04/cleaning_rules.yaml)、[剖析报告](w04/artifacts/w04/profile_report.json)、[适配与对账报告](w04/artifacts/w04/adapter_test_report.json)
4. [适配器实现](w04/customer/w04/solution.py)、[单元测试 16 个全过](w04/customer/w04/unittest_run.txt)
5. [38 项指标在导入库上的实际运行结果](w04/artifacts/w04/metrics_run.json)
6. [demo 方案](w04/docs/w04/demo_plan.md)、[两次运行与调优前后对照](w04/artifacts/w04/demo_run.json)
7. [六场角色访谈原始导出](w04/artifacts/w04/interviews/)、[自动预检结果（80 项全过）](w04/artifacts/w04/precheck-v1.json)
8. [打包 zip（130 个文件，解压约 2.8 MB）](w04/w04-submit.zip)

本周完成：167,749 笔订单全量导入，对账四类等式成立（源表 168,253 ＝ 入库 167,749 ＋ 隔离 168 ＋ 去重 336）；9 条清洗规则由适配器执行；38 项指标在重新导入的项目上实跑 38/38 通过、ID 未变；业务模型按六场访谈修订 8 处，指标库仅动 6 项且为纯追加；demo 两条链路实跑，调优只改一处（回答提示词），同一问题重跑后数字未变。

**已知未决，不声称验收通过：** ①卡产品正式规则文件经门店与运营两侧确认不存在，卡种范围按导出实际取值推断并标注；②在售/停售清单、月报实际报数粒度、小程序与商城归属口径、券核销记录位置四项待核，三方访谈额度已尽，属终局待核；③门店老收银系统另有未导出消费，任何总量类结论只限新 CRM 导出范围，未导出规模不做估算；④复购率算法归属待项目组确认。以上均不构成验收通过或业务效果声明。

自动预检 80 项全部通过（工程内与解压后各一次），另有 5 项转人工评审；预检通过不代表课程验收通过。

## W03：把客户口径接入运营 Agent（2026-11-18订正）

[当前作业阅读入口](w03/README.md) · [SOW v0.3](w03/docs/w03/sow.md) · [指标核定与最终逐题解释](w03/docs/w03/metric_decisions.md)

本次小样本55/55、正式规模15/15，覆盖38项；最终原生解释53/55，两条问题和导师订正稿分别保留。原51条解释已按定稿轮重核为50/51，不沿用早期46/51，也不把规模复判冒充原正式报告。

构建方法已泛化为v0.1.6，真实生成38项候选并通过10组确定性核对；冻结定稿库仍保留原v0.1.5生成版本。模型历史apply未完成、王经理更新说明未发送，均如实记录。本次为作业订正发布，不代表客户验收或业务效果通过。

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
