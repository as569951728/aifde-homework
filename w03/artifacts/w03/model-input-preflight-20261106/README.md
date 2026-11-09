# 本轮模型输入准备与本人取舍

本人采纳原18组方向，明确个人Excel不进模型；FDE费用/结算/延期/变更/项目验收批准等交付事项放SOW与交付记录。业务模型仅保留青禾业务知识。

四份有效W03访谈已登记，原提取提示v2/维护Skill v3不变；八份指定MD逐字加入notes供维护核查，原文与访谈分开。离线inspect通过：4份、62条、1批，问答没有跨批切断。未启动工作流、未调用模型、未apply，正式模型仍v0.4。

- user_decisions.json：本人决定原话、采用及边界。
- configuration_change.json、inspect_stdout.json、input_checks.json：实际配置和离线检查。
- inspect_materials_preview.json：从实际文件重建的离线输入预览，不是模型已读证据。
- effective_tests/：按本人新边界生成的85例有效题目/判据及变更；原冻结不改。
- independent-review/：来源先行判据与冻结输入复审。首审 review.json 保留两项问题；最终状态见 [review-v2.md](independent-review/review-v2.md) 与 review-v2.json。

**独立复审已通过。** 首审发现的 U06 缺少用户建模约束输入、旧进度说明仍标“当前”两项问题已修复；v2 复审无新增问题，无需本人裁决。修复前输入和首审原报告保留。

下一小步由既有工作流提取候选业务知识，再按原问答审核；之后才形成模型提案。当前通过范围仅为输入准备与相应测试设计，85题尚未运行，新模型及38项指标尚未完成。

后续进度：已实际运行并完成候选审核，见[2026-11-06 提取与审核](../candidate-extraction-20261106/README.md)。本页及manifest是运行前冻结，不能继续视为最新执行状态。
