# B5＋B6 实际构建独立审核 v1

结论：**不批准 merge/load**。`approved_for_merge_load=false`；`failed_checks` 1项阻断。

审核对象 build-v1，累计32指标、0未决；来源、维度、粒度、MetricFlow技术检查均通过。已逐项核对32项原始response、catalog、metrics与派生SQL。设计批准不构成本次语义通过。

## 已确证问题
B5-H03的两个账户在8月都有有效订单：M00005只有后续单，其首购数、首单金额与首单数应为0；M00007只有首单，其后续单数应为0。

冻结期望：`[['M00005', 0, 0, 0, 1, 1], ['M00007', 1, 3000, 1, 0, 1]]`
实际结果：`[['M00007', 1, 3000, 1, None, 1], ['M00005', None, None, None, 1, 1]]`

原因：首单和后续单分别先过滤成不同事实子集；原生FULL OUTER JOIN保留账户行，却将不存在的子集列留为NULL。生成指标没有补零机制，Engine仅对无分组加总补零，分组结果不能靠judge将NULL改成0。独立重新读原CSV核算，与冻结期望完全一致。

一次确定性原生查询已保存实际SQL与完整数值响应；没有模型API调用、没有自然语言回答。为保全生成物，查询在execution-review内的项目副本运行。最初脚本根路径导入错误发生在查询前，原日志保留；纠正后仅执行1次查询。

## 其他审查
B5有效单过滤、全覆盖排序、同日订单号裁决、原订单日期、首单净额和CRM账户去重符合来源。B6先按账户自然月汇总、>=2阈值、同月购买账户分母、比率依赖和full_month_only限制正确。旧24项定义与财务比率未见语义偏移；仍需实际回归。

## 保留边界
first/repeat semantic models expose account/home_store/tier/time, not original order store/channel. No store/channel filtering acceptance is claimed; planned13 only require account filtering and registration grouping.
monthly_member_orders only contains months with valid purchases. Frozen B6-Z01 is an ungrouped empty month and Engine additive normalization applies. Grouped queries including an empty month may omit that month; no native empty-month-group query was run. Design review already records no such candidate; not claimed covered.
Actual aggregation is member_id+month_start, serialized grain declares synthetic member_month_key. Primary uniqueness passed; explicit two-column grain_keys would better satisfy contract wording for composite grain.
No natural-language model query or answer generated in this review. Planned47 and new13 complete explanation audits remain pending.

## 后续
由构建输入/Skill生成独立新版本，正确表达已有分组内空子集的0；不得手改生成物、期望或judge。保留v1失败，先用同一H03复验，再申请merge/load。47题和新增13题完整解释均尚未通过。

机械证据检查 17/18；唯一失败为H03_grouped_zero。来源与产物哈希见 build-review-v1.json。
