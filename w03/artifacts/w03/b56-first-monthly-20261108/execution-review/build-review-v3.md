# B5＋B6 实际构建独立审核 v3

结论：**批准本版本 merge/load**。`approved_for_merge_load=true`，`failed_checks=[]`。仅批准当前32项库进入4套冻结数据加载与后续47题验证，不是最终问数或语义解释验收。

独立复审了原始response、catalog、YAML、SQL、来源、维度路径与粒度；32目标完整，0未决，五类框架检查通过。所有引用再次按原文连续片段核对，v2的Markdown标记改写问题已不存在。旧24项定义与比率依赖无新偏移。

B5四项首/后单指标共用全覆盖有效订单序列，按账户分组、日期和订单号排序；条件聚合正确排除未命中键或贡献0。注册保持独立注册日期。B6账户月组合粒度逐列声明，>=1、>=2、同月分母与full_month_only限制正确。

**原H03已实际复验通过**：在execution-review的v3项目副本执行1次确定性原生查询（模型API 0次），仍用原题意图、原冻结期望、原judge。M00005的三项首单指标为0，M00007后续单数为0；SQL和完整响应已保存。v1/v2原失败未改。

机械检查19/19；22+21分片与原43题逐对象一致。自然语言47题及新13题完整解释尚未执行审核。

## 限制与措辞注意
order_sequence contains valid orders, not all original rows. Groups represented only by invalid orders in combined queries have not been tested; approval does not certify such absent subgroup zero handling.
monthly fact has only purchasing account-months. A single ungrouped empty month is supported by engine zero handling, but grouped zero-month completion is not verified or claimed.
B5 store/channel paths now structurally reachable, but no channel/store reranking runtime case in frozen13; graph reachability is not execution coverage.
first_buyer_count constraint uses abbreviated 按 member_id 排序; actual source and SQL unambiguously mean partition by account then ordered_at,order_id. Answer review must use complete definition and not repeat this abbreviation as the sort keys.
Only deterministic H03 executed here. Planned47 natural-language tests,13 new full answers, prior regressions,4 dataset loads and scale validation remain separate gates.

真实产物、诊断与冻结输入哈希见 build-review-v3.json。
