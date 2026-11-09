# 结构化日期协议与离线检查器审核

时间（UTC）：2026-11-06T16:15:00.006681+00:00

结论：**协议可用于隔离12题；离线检查器70/70验证符合预期。尚未读取本批真实输出，不能记为模型问答通过。**

- 外层仍为课程唯一answer字符串；提示只增加栏目和格式，没有独立公式、具体日期、卡产品答案或消息ID。
- 机器精确解析Markdown“是/否”，不猜数字、前缀或日期关键词。card_type没有回写字段，归属依靠冻结fixture与原生request，未冒称检查了该输出字段。
- 独立核每个日期字段、三条件、计划/综合区间、端点、结论，并交叉核输出自身是否一致。错区间即使最终无效仍对，也失败。
- 70个离线检查：29合成正例（原24+2手列常量锚点+展示变化/相等截止），39故意破坏负例，2个文字语义边界例。正例不是待测oracle自造自验，也不是真实模型答复。
- 2个文本故意错误例仅machine-pass，必须再做语义失败判定；检查器full_answer_pass恒null。来源与范围续文及依据不靠关键词代替审查。

检查器SHA-256：`f035a2c54a069a6d47f896be1abfaf3f4590d25c510c64623547292469486aee`
自测脚本SHA-256：`8fff9f883c7743e9fe4ead65c4f518c18bb394ea513a33edb10a1eb6b81f9760`
被审提示SHA-256：`f803ecc68db3e6205d08fbfaec63d4aa0b34736201475f2e3607393fd9eeb811`

## 接口

`from check_date_answer import check_answer; result = check_answer(actual_answer, fixture)`

自测：`.venv/bin/python artifacts/w03/date-consistency-qa-20261107/independent-review/test_date_answer_checker.py`
单题记录：`.venv/bin/python artifacts/w03/date-consistency-qa-20261107/independent-review/check_date_answer.py OUTPUT_RECORD.json`

CLI退出0仅表示machine_pass，任何完整答案仍需独立来源和语义审核。只使用stdlib，无网络/模型调用，不改原答复。

## 执行边界

- 每题一次，记录全部HTTP attempts；不按语义失败重抽样。
- 逐request核实际模型输入没有checker/预期/独立参考或其他题。
- 原始answer保留，checker结果另存。
- 完整语义与来源独立审核后才给最终结论。
- 原R1/R2失败及本批失败不改判，不外推未跑分支。

当前离线自测报告SHA-256：`dfebe6bcd6fbbbd7b541bf9d97683b35453ef1fe4703f11d9250bf590cbd3cd0`。该报告是主Agent复跑同一源码后的文件，判定仍70/70。
