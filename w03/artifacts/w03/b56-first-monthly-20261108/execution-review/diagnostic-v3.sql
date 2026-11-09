SELECT
  COALESCE(subq_12.member, subq_20.member) AS member
  , MAX(subq_12.first_buyer_count) AS first_buyer_count
  , MAX(subq_12.first_order_sales_cents) AS first_order_sales_cents
  , MAX(subq_12.first_order_count) AS first_order_count
  , MAX(subq_12.repeat_order_count) AS repeat_order_count
  , MAX(subq_20.valid_order_count) AS valid_order_count
FROM (
  SELECT
    member
    , COUNT(DISTINCT first_buyer_count) AS first_buyer_count
    , SUM(first_order_sales_cents) AS first_order_sales_cents
    , SUM(first_order_count) AS first_order_count
    , SUM(repeat_order_count) AS repeat_order_count
  FROM (
    SELECT
      member_id AS member
      , CASE WHEN valid_order_seq = 1 THEN member_id END AS first_buyer_count
      , CASE WHEN valid_order_seq = 1 THEN paid_cents - refund_cents ELSE 0 END AS first_order_sales_cents
      , CASE WHEN valid_order_seq = 1 THEN 1 ELSE 0 END AS first_order_count
      , CASE WHEN valid_order_seq >= 2 THEN 1 ELSE 0 END AS repeat_order_count
    FROM "data"."main"."order_sequence" order_sequence_src_10000
    WHERE DATE_TRUNC('day', ordered_at) BETWEEN '2026-08-01' AND '2026-08-31'
  ) subq_8
  WHERE member in ('M00005','M00007')
  GROUP BY
    member
) subq_12
FULL OUTER JOIN (
  SELECT
    member
    , SUM(valid_order_count) AS valid_order_count
  FROM (
    SELECT
      member_id AS member
      , CASE WHEN status = 'paid' AND paid_cents - refund_cents > 0 THEN 1 ELSE 0 END AS valid_order_count
    FROM "data"."main"."orders" orders_src_10000
    WHERE DATE_TRUNC('day', ordered_at) BETWEEN '2026-08-01' AND '2026-08-31'
  ) subq_16
  WHERE member in ('M00005','M00007')
  GROUP BY
    member
) subq_20
ON
  subq_12.member = subq_20.member
GROUP BY
  COALESCE(subq_12.member, subq_20.member)
