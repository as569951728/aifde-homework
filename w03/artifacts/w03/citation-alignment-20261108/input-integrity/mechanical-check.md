# 六题冻结输入机械核验

**机械输入核验通过；尚无执行批准。** JSON中approved仅用于mechanical_input_integrity_only，execution_approved=false，failed_checks为空。

- 检查 332 项通过；6题=4原题+2控制。
- 最终question的UTF-8内容与Stage5逐题完全相同；fixture和材料已包含在冻结问题内，未拼新内容。
- 原题元信息、原期望、6个控制元信息及批准绑定逐字保留；expected不发送，工具列表为空。
- 正文保留11月8日澄清候选；唯一变化为root提供的候选回答提示。知识配置只改新隔离路径。
- 旧目录/评审/保护快照共270个文件hash未变，12保护项全部一致。
- 原runner/auditor原字节复制；check-only通过，模型调用0、钥匙串读取0。未初始化工程，未读取.env或密钥。
- 每题仅一次新run，确认length可按原策略扩一次；本轮语义/格式/网络失败留档，不另恢复或抽样。

必须由新鲜独立来源评审完成candidate及完整输入审查后，在qa-01/gate_acceptance.json签发执行门禁。该门禁需绑定runner、manifest、preflight及input-review的文件hash；本核验不能替代该批准。

runner SHA256：a594b197a85587c26b0686d21c93d9e7bfb421edc13c12827930176d223040d8
manifest SHA256：d454e804c858176ce642796fd60c8c01788b06d6a343a2d9ad2446023f475cd8
preflight SHA256：149b5801ec9e7cad9460da8ea3a3d5fa127fd1deeaa63ce284d7dfc5cd41f325
