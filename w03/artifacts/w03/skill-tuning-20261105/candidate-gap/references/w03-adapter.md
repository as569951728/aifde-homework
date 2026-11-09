# W03 使用范围

工作根目录为 `W03/实操工程`（相对 AIFDE 仓库根目录）。读取 `customer/w03/targets.json` 的目标目录并选定本次目标、`docs/w03/business_model.md`、`docs/w03/interview_notes.md`、`materials/w03` 对应客户材料与字典，必要时检查 `data` 下小样本；先核实际路径，不整体发送规模 CSV。

当前 W02 v0.4 是接续起点；其未知与本期已给资料逐项比较。课程参考问答不作为本人访谈来源。原始四表是数据接入层，不能把字段当成已经完成的业务语义。

结果沿 `docs/w03/interview_notes.md` 的“缺口清单”保存。试用、方法评测输出放在 `artifacts/w03` 的独立方法验证目录，不能记成本人已完成作业。业务规则与报表统计选择的去向分别是业务模型和指标定义；不在找缺口时直接生成 38 项指标。

任务书第 4 步规定本周王经理必访，即使某项指标已无规则缺口也不能取消；可核阶段交付、验收依据与责任，不必重复问材料已明确的公式。本期是否已访以本人记录为准。

取得本人新访谈后，才把实际导出配置到 `customer/w02/extraction.json`，再按 `customer/w02/workflow.json` 使用维护 Skill。sources 为空的当前工作流不得启动；找缺口不需要解除这个保护。不得 resume W02 未采用草稿或直接 apply 旧提案。

准备索引：在工程目录用 `.venv/bin/python ../学习工具/fde-gap-review/scripts/prepare_scope.py --catalog customer/w03/targets.json --target 所选ID --material 对应材料.md 字典.md --output artifacts/w03/本轮目录/scope.json`。材料仍需保留全文；没有标题精确匹配时回看任务与原文，不据标题索引自行补定义。只接受来源明确的目录名称，不把索引当业务核定。
