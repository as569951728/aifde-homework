# 指标修订

## 本次修订的指标 ID 清单

**修订 6 项**（仅 `catalog.json` 的 `constraints` 与 `sources` 纯追加，指标 ID、`metrics.yml`、全部 `.sql` 均未动）：

| # | 指标 ID | 名称 |
| --- | --- | --- |
| 1 | `monthly_paid_buyer_count` | 月末付费会员购买人数 |
| 2 | `monthly_paid_order_count` | 月末付费会员有效订单数 |
| 3 | `monthly_paid_sales_cents` | 月末付费会员净销售额 |
| 4 | `monthly_paid_repeat_buyer_count` | 月末付费会员复购人数 |
| 5 | `monthly_paid_repeat_rate` | 月末付费会员复购率 |
| 6 | `monthly_paid_avg_order_value` | 月末付费会员订单均额 |

**其余 32 项核对后无修订**：订单状态映射（已完成／已支付／部分退款→paid、全额退款→paid、已取消→cancelled，保留原 `ord_stat`）与 W03 measures 一致；新增会员用 `join_dt`、stat=0 不计有效会员、员工卡不进付费与免费口径（陈姐 MSG-05290、05357）均与现有定义一致；9 项月度指标"全门店、全渠道"措辞保留——该口径本周获门店侧背书（陈姐 MSG-05365"先别急着把哪一种排除掉"、05367 认可）；`orders` 语义模型 `channel` 维度已具备拆分能力，未启用为默认（报数粒度待核，见第三章）。

## 逐项修订前与修订后定义

> 六项均为**追加一条 constraint**（原 constraints 逐字保留）并追加访谈出处；以下列出追加内容。

| 指标 ID | 修订前 | 修订后（追加） |
| --- | --- | --- |
| `monthly_paid_buyer_count` | constraints 1 条（资格判定＋全渠道全门店）；sources 2 条 | 追加 constraint："付费会员口径只约束本期总部运营月报，不等于全部在售卡的范围；正式卡产品规则文件经门店与运营两侧确认不存在，本期卡种范围按导出实际取值推断并标注（陈姐 MSG-05359、小林 MSG-05370、05372）。" 追加 sources：`interviews/xiao-lin-2.md`、`interviews/chen-jie-2.md` 各一条 |
| `monthly_paid_order_count` | 同上结构 | 同上追加（同一条 constraint 与两条 sources） |
| `monthly_paid_sales_cents` | 同上结构 | 同上追加（同一条 constraint 与两条 sources） |
| `monthly_paid_repeat_buyer_count` | 同上结构 | 同上追加（同一条 constraint 与两条 sources） |
| `monthly_paid_repeat_rate` | constraints 1 条（分子分母＋全渠道全门店）；sources 1 条 | 追加 constraint："适用范围承分子分母的付费会员口径：只约束本期总部运营月报，不等于全部在售卡的范围（小林 MSG-05372、05374）。" 追加 source：`interviews/xiao-lin-2.md` 一条 |
| `monthly_paid_avg_order_value` | 同上结构 | 同上追加（同 `monthly_paid_repeat_rate`） |

**改动范围校验（可复现）**：改动前后对比确认——仅上述 6 项变化，且为 constraints 与 sources 的纯追加；其余 32 项序列化后逐字节一致；ID 集合与顺序不变（备份：`.bak-catalog-第9步前-20261112.json`，校验脚本断言全部通过）。

## 修订依据、来源、原因及适用范围

- **依据与来源**：小林 MSG-05372"月报只算悦享年卡和家庭季卡，这个口径只约束月报，不等于全部在售卡的范围"、MSG-05374（重申）；陈姐 MSG-05359"门店办卡、退卡没有我这边能确认的《卡产品规则》或《权益说明》这类正式文件"；小林 MSG-05370"我手头没有可给的卡产品配置清单或权益说明……你报告里写'未取得'是合适的"。逐字原文见 `artifacts/w04/interviews/xiao-lin-2.md`、`chen-jie-2.md`。
- **原因**：W03 该口径由运营确定（MSG-03848、03854），本周小林明确其**适用边界只到月报**——不外推为全部在售卡范围；同时"正式规则文件"从"尚未取得"改为"门店与运营两侧确认不存在"，措辞需如实反映（不写"已取得"，也不写"待访谈再核"——访谈额度已尽）。
- **涉及模型修订的互引**：本表六项对应 `model_changes.md` 第二章"§3 规则 1（月报产品范围）"与"§5 未决表第 1 行"两行；模型 §1 统计范围段与本章"适用范围"互引。
- **适用范围**：6 项付费月报与 3 项非付费月度指标（`monthly_buyer_count`、`monthly_repeat_buyer_count`、`monthly_repeat_rate`）共 9 项，本期均按**全门店、全渠道合计**实现；`channel` 维度已在 `orders` 语义模型中，拆分能力具备、未启用为默认；月报实际报数粒度（一个总数／分门店／分渠道）与三渠道归属未取得业务确认（小林 MSG-05374、05376；陈姐 MSG-05363、05365），保守方向（不排除任何渠道）已获门店侧背书（陈姐 MSG-05365、05367）。
- **运行验证**：38 项指标在修订后的库上于新项目 `project-c` 实跑（2026-08-01 ～ 2026-09-01），结果见 `artifacts/w04/metrics_run.json`：**38 项全部 `status=ok`，`run_metrics.py` 打印 `38 []`**；`project-c/validation.json` 为 `{"passed": true, "failures": []}`。抽查复核：`order_count`=8,869、`paid_order_count`=7,421、`valid_order_count`=6,845、`payment_cents`=85,274,970、`net_sales_cents`=75,816,374，与清洗后 CSV 独立直算逐项一致；`monthly_paid_buyer_count`=493、`monthly_paid_sales_cents`=8,601,918、`monthly_paid_repeat_rate`=0.2333。

涉及业务模型修订时引用 model_changes.md 对应条目，核对指标定义与 business_model.md 是否一致；可引用诊断报告的已有证据。
