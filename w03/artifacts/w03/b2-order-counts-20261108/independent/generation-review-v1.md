# B2 累计12项生成物独立审查 v1

approved_to_load_and_query: true；failed_checks: []。被审生成物：build-v1，逐文件哈希见同名JSON。

七项订单数均从orders事实行计非空order_id，主键检查48行非空且唯一。orders接入SQL为原样select，未全局筛paid，未派生连接放大，因此按状态分组能保留取消行。paid只依状态；有效要求实付>退款；退款要求paid且退款>0；部分退两端严格；全退同时要求paid、实付>0和退款=实付。零实付paid不会落入有效、退款或全退。

B1原五项保持paid实付、paid退款、paid逐单实付减退款、paid原价、paid原价减实付；全退仍是paid，优惠不再扣退款。全部以ordered_at统计，数量count、金额cents，各项不要求完整月。全局scope明确账户、订单和金额各按自身量纲。

12项指标与目标、目录一一对应，无未决，无model_sql。目录12项连续引用逐条对照原材料，均准确支持各项定义；business_model_usage五段原文及用途已核，未用模型凭空冒充报表公式。输入材料、业务模型、Skill和冻结期望hash均一致。

维度、粒度、MetricFlow三报告通过；各12指标均有完整目标维度路径，成交门店与归属门店角色分开，全部外键无未匹配。结构可达不等于每维均实测。

可将同一生成库分别加载small及人工fixture项目，原生load再次核三报告及版本，运行既定small21题与fixture1题。运行后仍须完整SQL/答案解释复核；本结论不等于本批测试通过或客户验收。
