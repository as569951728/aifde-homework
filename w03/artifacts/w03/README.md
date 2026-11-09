# artifacts/w03 目录说明

> 用途：本目录共 60 多个子目录，覆盖 W03 从环境验证到规模回归的全过程。交作业时整目录打包，评审第一次打开会缺少导航，这份文件说明每个目录是什么、能不能作为证据引用。
> 编写日期：2026-11-09。业务模型测试的汇总口径见 `docs/w03/业务模型测试记录索引.md`。

## 一、交付主证据（引用优先看这里）

| 目录 / 文件 | 是什么 | 能否引用 |
| --- | --- | --- |
| `library/` | 定稿指标库：38 项指标、`catalog.json`（逐项来源与原文引文）、各项检查结果、`provenance.json`（构建输入哈希） | 可，M2 主证据 |
| `test-small-v1/` | 小样本最终一轮 51 例：报告、逐例 trace、日志 | 可，M3 主证据 |
| `test-large-v1/` | 规模集 15 例：报告、trace、重绑后复判 | 可，M5 主证据 |
| `large-20261109/` | 规模集独立期望脚本 `large_expected.py` 与结果速览 | 可，证明期望独立算出 |
| `judge-checks/` | 判定程序自检：9 类 10 个错误注入全部被拒、2 个控制组通过 | 可，M4 主证据 |
| `chat-verification/` | 聊天入口 5 次真实问数的意图、SQL、结果、解释 | 可，M2 佐证 |
| `metric_test_report.json` | 从小样本最终轮复制的交付报告，被 `precheck.json` 引用 | 可 |

## 二、业务模型：从设计到 v0.5

| 目录 | 是什么 |
| --- | --- |
| `w02_revision_20261104/` | W02 v0.4 修订的参考根目录，不是 W03 新运行；`source` 相对它解析 |
| `model-understanding-design-20261106/` | 建模理解与首批题（U01/U02）设计、评审记录 |
| `business-model-design-review-20261106/` | 模型结构设计与独立评审、证据清单 |
| `model-validation-design-20261106/` | 验证用例设计评审记录 |
| `candidate-extraction-20261106/` | 候选业务知识提取；当时正式模型仍为 W02 v0.4，未 apply |
| `model-draft-20261106/` | 三版草稿；第三稿通过独立 Agent 的 T01–T03 正文静态审查 |
| `model-input-preflight-20261106/` | 模型输入准备与本人取舍（个人 Excel 不进模型等） |
| `model-update-impact-20261106/` | 模型更新预整理与影响评估，v3、18 组内容 |
| `model-clarification-20261108/` | U01 正文澄清与局部验证，5/6 通过 |
| `model-closeout-20261108/` | v0.5 保存与收尾复验（7 题：结构 7/7、语义 6/7） |

## 三、业务模型测试

汇总与口径（含「不许说」清单）见 `docs/w03/业务模型测试记录索引.md`，此处只列目录职责。

| 目录 | 是什么 |
| --- | --- |
| `full-test-design-20261106/` | 85 题测试集设计与覆盖评审（v2 为定稿版） |
| `independent-review-20261106/` | 出题与覆盖的独立评审 |
| `full-validation-20261107/` | 82 题全套执行 + 3 项正文检查，含 85 条执行账本与结果速览 |
| `answer-repair-20261107/` | 失败题修复：22 题 21 通过，U01 仍语义失败 |
| `citation-alignment-20261108/` | 引用校准 6 题：3 通过，候选未采用 |
| `source-semantics-audit-20261108/` | 82 道判据 + 3 项正文的静态校准，0 次新运行 |
| `qualification-qa-20261106` / `-r1` | 资格类 17 题：R0 11 通过、R1（隔离提示）17/17 |
| `date-boundary-qa-20261106` / `-r2` | 日期边界 24 题 + 8 题回归 |
| `date-consistency-qa-20261107` | 日期一致性 12 题，候选未采用 |
| `remaining-date-qa-20261107` | 剩余日期问法 12 题，12/12 |
| `basic-semantics-qa-20261107` / `-network-recovery` | 基础语义 6 题 5 通过；B04 网络故障同输入重跑 |
| `monthly-application-qa-20261107` | 月报应用 7 题，7/7（固定材料轨） |
| `operations-qa-20261107` | 运营问答 7 题：5 通过、1 语义、1 协议失败 |
| `context-application-qa-20261107` | 上下文应用 16 题，13 通过 |
| `evidence-goals-qa-20261107` | 证据边界与目标 5 题，2 通过 |
| `source-bound-template-qa-20261107` | 来源约束模板 12 题，11 通过 |
| `source-refined-qualification-qa-20261107` | 来源细化资格 17 题，16 通过 |

## 四、访谈

| 目录 | 是什么 |
| --- | --- |
| `interview-pasted/` | 按角色分目录的转贴原文（`wang-20261106`、`wang-20261109` 等） |
| `interview-exports/` | 导出核验台账、`source_audit.json` 与说明 |
| `interview-audit-20261106-{wang,chen,xiaolin,zhou}-w3/` | 四角色首访逐条审计与校验结果 |
| `interview-audit-20261109-wang-sow/` | 王经理第二轮 SOW 核查（04822—04840）审计 |
| `interview-preparation-20261106-zhou/` | 老周访谈前的准备与受保护文件快照 |
| `interview-phase-review-20261106/` | 访谈阶段整体复查 |
| `invalidated-interview-20261106/` | **作废**：误选 W04 小林访谈的记录。只用于解释状态修正，不作业务事实、模型输入或缺口关闭依据 |

## 五、指标库构建与分阶段测试

| 目录 | 是什么 |
| --- | --- |
| `net-sales-review-20261105/` | 净销售额的首个指标：数据检查、范围与来源边界复核 |
| `net-sales-first-20261108/` | 净销售额构建 v1→v2 与语义发现 |
| `metric-batch-plan-20261108/` | 指标分批构建计划与候选 v1/v2 |
| `b1-amounts-20261108/` | B1 金额类指标批次 |
| `b2-order-counts-20261108/` | B2 订单数类指标批次 |
| `b34-accounts-ratios-20261108/` | B3/B4 账户与比率类批次 |
| `b56-first-monthly-20261108/` | B5/B6 首购与付费月报批次（含 47 题执行审查） |
| `b7-paid-monthly-20261109/` | B7 付费月报 8 题，含卡表缺行受控实验 `q06-missing-card/` |
| `test-small-52-with-c01/` | 含 B7-C01 的 52 例版本，用于对照已知限制 |
| `test-known-limitations-v1/` | 已知限制专项回归 |

## 六、环境与过程（不作为交付证据）

| 目录 | 是什么 |
| --- | --- |
| `environment-smoke-20261104/` | 环境冒烟：梧桐样例问数、样例判定脚本、独立核对 |
| `skill-tuning-20261104/`、`skill-tuning-20261105/`、`model-skill-tuning-20261105/` | 构建 Skill 与问答提示的调优迭代记录 |
| `review-stage-validation-20261105/` | 评审阶段验证装置的冻结与验证 |
| `known-limitations/` | 已知限制与验收缺口的原始记录（B7-C01 等） |

## 七、引用时的三条规则

1. **只看目录名容易误判**：`*-qa-2026*` 是当时的批次结果，多数不是最终状态；最终状态看第一节的交付主证据。
2. **不跨目录加总**：批次之间是「发现问题—改提示—同批回归」的关系，题有重复，条件不同。
3. **作废目录不引用**：`invalidated-interview-20261106/` 与任何标 `candidate`／`未采用` 的候选，只能作为过程说明，不能当作结论。
