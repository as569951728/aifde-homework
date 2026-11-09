# 日期边界问答：先看原材料的独立判据

记录时间（UTC）：2026-11-06T15:35:24.216231+00:00

本判据在读取作者预期、draft-03 候选、实际回答及主 Agent 判读之前形成。仅读取两份指定材料、三份有效 W3 原访谈及 DY/DQ 题设。记忆索引不作为本轮判定证据。

## 判据

- **C01** 只就本期总部运营月报纳入悦享年卡、家庭季卡；等级和购卡支付金额不能替代卡类型及有效状态。 来源：lin:MSG-03848, lin:MSG-03854。
- **C02** 指定判定日 d 的卡日期有效性要求 valid_from <= d < valid_until，且 ended_at 为空或 d < ended_at。生效当天有效，计划结束当天无效，提前终止当天起无效。所有条件是合取；任一不满足即无效。 来源：chen:MSG-03886, chen:MSG-03888, chen:MSG-03890。
- **C03** ended_at 为空仅表示该记录没有提前终止，仍须检查生效及计划结束日期，不表示无限有效。 来源：chen:MSG-03886, chen:MSG-03890。
- **C04** 按题设 decision_date 检查历史状态，不能使用运行日、当前状态或自行替换为月底；本组是单卡日期情境问答。涉及真正月报资格时才按自然月月末筛账户。 来源：chen:MSG-03886, statistics_email, questions。
- **C05** 晚于计划结束的 ended_at 不延长计划有效期；有未来提前终止日期也不能使尚未生效的卡提前有效。可以提示数据质量，但不得借异常拒绝题设可确定的日期判断。 来源：chen:MSG-03886, test_dictionary, questions。
- **C06** 日期边界和空值口述来源是陈姐门店执行；小林确认卡范围和账户规则，但未确认日期端点；老周未确认日期与空值，不得写成 IT 已验证。 来源：chen:MSG-03886, chen:MSG-03890, lin:MSG-03850, zhou:MSG-03873, zhou:MSG-03875, zhou:MSG-03877。
- **C07** 测试字典定义字段、日期粒度、时区和覆盖，不能独立确认业务日期端点。测试集为干净合成数据，不等于真实 CRM 或生产核验。 来源：test_dictionary, zhou:MSG-03875, zhou:MSG-03877, zhou:MSG-03883。
- **C08** 正式规则说明、办理记录和历史执行凭据仍待向运营小林核对；这不抹除已有陈姐口述规则在本题人工构造情境中的推导能力。回答可下情境结论，同时不能冒称正式材料或生产规则已确认。 来源：chen:MSG-03886, chen:MSG-03890, zhou:MSG-03883。
- **C09** 本题不能把单卡有效自动升级成账户当月购买人数、月报数值、生产交付或验收通过。若扩展到账户，有一张范围内有效卡即合资格且按账户去重；购买人数另需当月有效购买。 来源：lin:MSG-03854, lin:MSG-03868, statistics_email。
- **C10** 完整阅读回答：检查结论、每个题设日期条件及其合取逻辑、历史日、不新增规则和来源范围。符号公式与准确自然语言等价；不按固定关键词机械判分。未重复非必要背景但无错误外推可列非阻断建议；核心条件遗漏、归因升级、错误拒答或实质自相矛盾是问题。 来源：questions, chen:MSG-03886, test_dictionary。

## 独立推导的 24 题结果

| 题号 | 卡类型 | 判定日 | 应有效 | 开始条件 | 计划结束条件 | 提前终止条件 |
|---|---|---|---|---|---|---|
| DY01 | 悦享年卡 | 2025-08-19 | 否 | False | True | True |
| DY02 | 悦享年卡 | 2025-08-20 | 是 | True | True | True |
| DY03 | 悦享年卡 | 2025-08-21 | 是 | True | True | True |
| DY04 | 悦享年卡 | 2026-08-19 | 是 | True | True | True |
| DY05 | 悦享年卡 | 2026-08-20 | 否 | True | False | True |
| DY06 | 悦享年卡 | 2026-08-21 | 否 | True | False | True |
| DY07 | 悦享年卡 | 2026-08-14 | 是 | True | True | True |
| DY08 | 悦享年卡 | 2026-08-15 | 否 | True | True | False |
| DY09 | 悦享年卡 | 2026-08-16 | 否 | True | True | False |
| DY10 | 悦享年卡 | 2026-08-20 | 否 | True | False | True |
| DY11 | 悦享年卡 | 2026-08-10 | 是 | True | True | True |
| DY12 | 悦享年卡 | 2025-08-19 | 否 | False | True | True |
| DQ01 | 家庭季卡 | 2026-05-19 | 否 | False | True | True |
| DQ02 | 家庭季卡 | 2026-05-20 | 是 | True | True | True |
| DQ03 | 家庭季卡 | 2026-05-21 | 是 | True | True | True |
| DQ04 | 家庭季卡 | 2026-08-19 | 是 | True | True | True |
| DQ05 | 家庭季卡 | 2026-08-20 | 否 | True | False | True |
| DQ06 | 家庭季卡 | 2026-08-21 | 否 | True | False | True |
| DQ07 | 家庭季卡 | 2026-08-14 | 是 | True | True | True |
| DQ08 | 家庭季卡 | 2026-08-15 | 否 | True | True | False |
| DQ09 | 家庭季卡 | 2026-08-16 | 否 | True | True | False |
| DQ10 | 家庭季卡 | 2026-08-20 | 否 | True | False | True |
| DQ11 | 家庭季卡 | 2026-08-10 | 是 | True | True | True |
| DQ12 | 家庭季卡 | 2026-05-19 | 否 | False | True | True |

DY/DQ10：即便提前终止日期晚于计划截止，计划截止仍独立约束。DY/DQ11：使用 8 月 10 日，不使用假定运行日 8 月 31 日。DY/DQ12：未来终止不能越过尚未生效的限制。

## 分级及证据边界

- pass：结论与完整条件正确，证据及情境范围无实质错误。
- pass_with_nonblocking_suggestion：核心正确，仅可读性、冗余或非必要背景表达可改进，不需要本人业务确认。
- fail：日期或合取条件错误/关键条件遗漏/用当前日替历史日/新增无依据规则/来源权限升级/以材料待补为由拒绝可推导情境。
- needs_business_decision：仅限原件无法解决的真实事实冲突或需真实业务取舍，本组题设本身没有发现此类事项。

本组 24 题为人工构造单卡日期知识问答；不构成查询执行、生产数据核验、38 指标通过、正式模型采纳或客户验收。

## 原件 SHA-256

- `statistics_email`：`materials/w03/04_本期统计确认邮件.md`
  - `c4f847fd90fd0765d37ad22f20d4a4eb0bab90f8543ae0f05d7a3cbee104c4be`
- `test_dictionary`：`materials/w03/05_数据字典.md`
  - `b4c905ae6d2f4c08e139c695a2868b66ee5047b2b8ea94d6eccba55aebb79c16`
- `chen`：`artifacts/w02/sources/W3-interview-c77a57a1-651d-5183-a601-e25cbe01df51-transcript.json`
  - `44782a4e3faf2e64dda977a14096cb2ef872b30082f5bab76685822fbbbd7308`
- `lin`：`artifacts/w02/sources/W3-interview-9e678773-8915-52e1-a1e6-939429340eab-transcript.json`
  - `4e0dda3d8653d67b4740345a3eeffc84f5eac6b81e03fa1a64572338b7b31f71`
- `zhou`：`artifacts/w02/sources/W3-interview-b079dbb8-d9ae-5c64-bbd4-3f68731c8feb-transcript.json`
  - `4d60b0499cfff1ce466183fa32c6c593956abe0513d1336ded239e4e53f3211c`
- `questions`：`artifacts/w03/model-input-preflight-20261106/effective_tests/model_questions.json`
  - `bc13834679927f7f1efba9fe00f2e7153e55fd5e28481e901c945c7cff2d7343`
