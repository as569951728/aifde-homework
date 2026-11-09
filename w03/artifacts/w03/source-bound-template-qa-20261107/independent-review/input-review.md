# 冻结输入独立门禁

结论：通过，可按已审计划运行一次12题。

候选模型/提示与input精确一致；原题、fixture、预期、原12个case对象、runner、answer_protocol和checker未变。清单及受保护文件哈希全部匹配；配置仅改本批快照路径。selection文件仅改离线selection_reason，不入模型，不能误称整文件字节未变。

模型messages仅包含已审候选、提示、课程GUARD和单题fixture，无独立期望。未调用模型或读取实际输出；实际请求与完整答案仍需运行后审核。
