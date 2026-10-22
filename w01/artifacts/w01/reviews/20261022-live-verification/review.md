# W01 正式真实验证核对（2026-10-22）

结论：用户运行 verify_product.py --live 后，11 项全部通过，三份正式技术 JSON 已生成。助手核对了 schema、结果内容、引用与哈希，没有代跑本轮模型验证。

| 产物 | 当前状态 |
| --- | --- |
| environment_check.json | 已生成；8 项 pass，evaluation 为 skipped |
| model_baseline.json | 已生成；deepseek-flash，live；9 条带 trace 的检查记录，failures 为空 |
| runtime_evidence.json | 已生成；11 项 passed=true，12 份引用证据哈希吻合 |

11 项为：缺日期澄清、退款解释、明确日期分析、缺覆盖、只读拒绝、HTTP 标签动作、重复执行幂等、撤销、文字确认日期、按钮确认日期、拒绝后换目标。最后一个多轮场景还核对了待确认草案阻止直接换目标。

独立检查：消费结果与此前 CSV 独立核算一致；M001 的退款解释正确；幂等重放保持同一动作和版本，撤销后 inactive 且版本递增；各多轮场景保持同一任务。三份 JSON 通过对应 schema，12 个证据 SHA256 全部吻合，基线与嵌套轮次的 trace 引用可定位。总 trace 包含 63 个 span、26 次模型调用，其中 13 次保存了 HTTP 尝试信息且均为 200；另外 13 次交互场景调用经过 CountedModel 封装，只保留调用和用量记录，attempts 为空，不能把它们也说成已逐条核实 HTTP 200。源码确认此封装未转发 call_summary 所读取的元数据；原始证据保留，不补写缺失字段。待确认时换目标的拦截会产生一条 ERROR agent.run，这是预期拒绝测试，不应误报为模型故障。

人工阅读意见：召回建议仍需业务复核，短信/APP/站内渠道、商品品类与咨询记录等不能从教学样例推定客户已经具备；没有因此将标准产品记为已接入客户触达系统或承诺召回效果。单批 11/11 不表示多轮稳定性或业务适配全面通过。

本目录保存三份技术 JSON 和 evidence 的本轮快照，source-hashes.json 标记本地实现/评估配置版本，sha256.json 记录快照完整性；正式入口文件继续保留在 artifacts/w01 根目录。环境 evaluation 后续会据真实评估报告更新，本快照保留更新前状态。

下一步：同一已配置模型的终端，进入 evals 运行课程锁定的 Promptfoo 0.122.2，完成当前 7 个场景。评估后先核对 7/7、模型一致、断言内容及临时 trace 归档，再执行 finalize_evaluation.py。汇总脚本最低只检查 3 条，助手不能用这个宽松条件替代实际 7 场景验收。

截至本次，Promptfoo 尚未运行，环境未达到 9/9；product_fit_gap.json、正式访谈与 project_assessment.md 仍待完成，没有执行最终全作业预检或提交。
