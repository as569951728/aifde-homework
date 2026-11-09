# 静态校准终包核验

结论：**通过；汇总准确，无实质问题。** 本结论仅核终包计数、版本和保全，不重复三组业务语义审查，不代表新模型问答通过或正式采用。

- 三组覆盖56、15、14项，共85个唯一ID：82道问答判据、3项正文检查。各复审状态、检查项、正文结论和候选hash对应。
- 候选预期6题、12处JSON patch可按原值完整回放；F07/A02/E06为判据澄清，R03/F08为引用修正，A03为已采用的可选精度改善。
- 正文仅MSG-01731一处半句替换，其余逐字不变。MA-N02/03/04为未应用的非阻断建议。F08仍引用冻结5fb4正文，§2/3/5与63513新候选完全一致。
- 253个旧文件、27个来源与12个保护文件hash均匹配。旧proposal按已保护的前轮快照核对未改，旧workflow仍awaiting_apply；正式v0.4、提示和Skill不变。
- 六份接续的before/after hash匹配；新增停点、旧latest改history以外历史保留。学习笔记另新增标题后一个空行，无内容删改。
- 本轮新运行、课程模型API、指标查询均为0；新候选真实问答覆盖为0。旧3/6和U05/U01语义失败、P01格式失败保留，不跨版本继承通过数。

机械核验84项通过，细节见[mechanical-check.json](mechanical-check.json)。初次核验的两处检查边界误报另保留：旧proposal通过被保护的前轮快照绑定；学习笔记纯空行新增不构成历史改写。受审文件未因此修改。

## 最终封包允许范围

仅可修改`completion.json`已有`status`，并新增以下审核引用字段：`final_review`、`final_review_sha256`、`aggregate_review`、`aggregate_review_path`、`aggregate_review_sha256`、`aggregate_review_status`。含义只能是结束pending并记录本审核。

其他计数、候选hash、既有报告/覆盖/接续hash、旧成绩、next_step及正式采用状态保持逐值不变。progress当前状态无需修改。root应另存最终completion与[受审快照](reviewed-completion.json)的字段差异和最终hash；本批准不允许更改报告、接续、判据、评审或历史评分。

本次0 API、未读密钥，仅写aggregate-review目录。
