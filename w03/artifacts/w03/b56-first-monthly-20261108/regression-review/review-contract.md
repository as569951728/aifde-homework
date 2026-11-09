# B1-B4 本轮回归独立审核判据

先读 materials/w03 原材料与 docs/w03/contract.md 后冻结。本文件形成时尚未读取本轮测试文件或实际结果。仅审核本轮原33题 small 与1题旧B2人工边界，旧分不继承。

- Compare expected and actual status, metric IDs/order-insensitive sets, exact half-open time range, dimensions and all AND filters.
- Compare all dimensions, every value, exact counts, meaningful numeric tolerances, nulls, units; reject missing, extra and duplicate groups.
- Review each actual SQL for appropriate order grain, predicates, window, filter, dimension joins, no fanout, independent ratio numerator and denominator aggregated before division, null on zero denominator.
- All B1-B4 orders use ordered_at. Shanghai dates and inclusive start/exclusive end apply. Coverage outside is clarify/unsupported/error as frozen expected specifies, never zero.
- Data and catalog version/hash must match the actual execution project and loaded cumulative library. Expected business semantics cannot be regenerated from actual or candidate SQL.
- Each full answer must faithfully describe scope, endpoints, filters, amounts and conversions (cents/100 for yuan), proportions, accounts vs people, refund inclusion, and data limitations. Merely correct headline numbers do not pass explanation review.
- Independent expected results may be reused from prior frozen tests after verifying correspondence. New version hashes are metadata binding only; no numeric or intent changes.
- Numeric and explanation pass counts must be separate. A numerical pass with materially false scope or date explanation remains explanation failure. SQL is audited separately.
- Historical B34 native numeric 34/34 and explanation 32/34 are history only; original B3-U01 valid-order refund-buyer wording and B1-Z01 inclusive June30 wording failures remain preserved; do not inherit old scores.
- No new model API calls, no source model/Skill/judge/data edits; write only this regression-review directory. Audit only 33 small regression plus one B2 fixture.

具体24项公式与原材料哈希见 review-contract.json。
