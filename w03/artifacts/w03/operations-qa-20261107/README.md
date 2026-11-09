# 经营目标与运营协作模型问答核查

本批按既有七题 U01/U04/F03/F04/F05/F06/F09 验证。被测模型只收到冻结候选正文、沿用回答提示和当前问题；不附加原访谈、预期答案或别题。独立 Agent 先查有效原来源、写判据，再对照预期和真实结果。

- `input/manifest.json`：运行前冻结的题目、候选、提示及配置；原题与预期保持不变。
- `independent-review/source-first-criteria.*`：来源先行的独立判据。
- `independent-review/input-review.*`：运行前门禁，结构化状态、检查项与正文必须一致。
- `output/`、`run_index.json`、`actual_answers.md`：一次实际运行的原答与原生记录链接；失败也保留。
- `protocol_audit.json`：实际请求与冻结输入核对，不代替语义判读。
- `independent-review/review.*`：独立完整回答评审。
- `结果速览.md`、`completion.json`、`execution_ledger.json`：本批结论与累计覆盖（运行及评审完成后生成）。

不执行正式模型 apply、Skill 替换或指标数值查询；既往 DQ10/P09/B05 原答失败继续保留。测试数据正确、模型回答通过、业务执行与验收分别取证。导师操作与 Agent 评审不计为本人独立作答或客户批准。
