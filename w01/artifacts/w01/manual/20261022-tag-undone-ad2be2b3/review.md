# 撤销标签核对（2026-10-22）

结论：用户点击撤销后，同一个动作已变为 undone，M001 的 recall_review 标签不再生效。

| 核对项 | 撤销前 | 撤销后 |
| --- | --- | --- |
| 本地动作账本 | applied | undone |
| 样例标签系统动作 | applied | undone |
| 标签 active | 1 | 0 |
| 标签 version | 1 | 2 |
| 标签/动作记录数 | 各 1 条 | 仍各 1 条 |

动作 ID：ad2be2b3-8cdc-4d0e-8440-3e11c3090b14；session：0a243436-77f9-463a-af1a-2ca6eff67bc6。目标和草案 hash 未变。标签恢复为动作执行前的 inactive 状态；历史动作行保留，动作的原执行版本仍为 1，标签当前版本为 2，两者用途不同。

实际账本结果 label_active=false、label_version=2，与标签库一致。撤销前归档哈希已复核，11 项检查和当前只读快照分别保存于 review.json、database-check.json，并附 SHA256。

网页 /api/undo 直接操作账本和本地标签 API，不调用模型、不保存新 Agent run JSON。最新 runs 文件仍是确认执行时的 completed，不能据此认定撤销失败。本次没有伪造 run/trace，也未由助手重复撤销。

下一步：新任务、勾选样例标签动作模式，生成 M001/recall_review 草案后点击“拒绝”，验证拒绝是否终止该草案且没有实际标签写入。之后再验证同一任务换目标；重复请求幂等等留待专门验证。完整基线、评估和正式作业仍待完成。
