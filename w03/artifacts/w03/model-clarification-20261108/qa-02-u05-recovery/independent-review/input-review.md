# QA-02 U05独立技术补测门禁

**批准一个新的隔离U05原生运行，最多1run、按既定策略最多2次HTTP尝试。** `status=approved_for_execution`，`approved/approved_for_execution/run_allowed=true`；103项检查全部通过，`failed_checks=[]`。签前0调用。

QA01已固定5pass、U05因length后network无完整答案不可判。首个公开部分JSON和两attempt完整保留；本次不是workflow resume，不对可评分语义/格式失败挑样。完整messages与原失败run逐字相同，不发送部分答案、纠错、期望或其他control。model/prompt/问题/材料/预期/严格JSON解析器及运行策略保持。

原生要求初始max_tokens小于retry_max_tokens；直接16384会引入更大的扩容策略，所以本轮保持8192→16384、180→240，不修改框架。即使再次失败也停止，不追加其他恢复。本批准独立于旧门禁，不回写旧失败；新增run/HTTP单列计数，结果全量留存。
