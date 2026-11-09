# B1 build-v1 独立生成物审查

状态：approved_to_load_and_query；approved_to_load_and_query=true；failed_checks=0。

五个金额表达式均从 status=paid 订单行逐单贡献后求和；实付不扣退，退款取累计额，净额扣退，原价不扣退，优惠仅原价减实付。统计日为 ordered_at，一行一 order_id，未引入资格或多卡关联，未按正净额删全退。catalog 五项 unit=cents，未迁入整月限制；净额目录明确全退仍在 paid 行集合。

5 条指标来源均为材料01的连续原文，4 条模型使用引用均逐字存在于输入且用于对象/关系/维度；输入与当前模型、材料一致。成交店和归属店的实体路径区分正确；12 维度结构检查可达不等于全部行为实测。来源、粒度、维度、MetricFlow及总校验全部 passed，无 unresolved。

原冻结期望、Skill v0.1.2、judge 均未变；15 条测试原样采用。批准提升单个五指标库、重新加载检查后执行 15 条真实自然语言问题；这不是查询通过或客户验收结论。运行后须逐题核数值/完整意图/SQL与解释。
