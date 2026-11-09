SELECT
  COALESCE(subq_12.member, subq_20.member, subq_28.member) AS member
  , MAX(subq_12.first_buyer_count) AS first_buyer_count
  , MAX(subq_12.first_order_sales_cents) AS first_order_sales_cents
  , MAX(subq_12.first_order_count) AS first_order_count
  , MAX(subq_20.repeat_order_count) AS repeat_order_count
  , MAX(subq_28.valid_order_count) AS valid_order_count
FROM (
  SELECT
    member
    , COUNT(DISTINCT first_buyer_count) AS first_buyer_count
    , SUM(first_order_sales_cents) AS first_order_sales_cents
    , SUM(first_order_count) AS first_order_count
  FROM (
    SELECT
      member_id AS member
      , member_id AS first_buyer_count
      , net_sales_cents AS first_order_sales_cents
      , CASE WHEN order_id IS NOT NULL THEN 1 ELSE 0 END AS first_order_count
    FROM "data"."main"."first_valid_orders" first_valid_orders_src_10000
    WHERE DATE_TRUNC('day', first_order_date) BETWEEN '2026-08-01' AND '2026-08-31'
  ) subq_8
  WHERE member in ('M00005','M00007')
  GROUP BY
    member
) subq_12
FULL OUTER JOIN (
  SELECT
    member
    , SUM(repeat_order_count) AS repeat_order_count
  FROM (
    SELECT
      member_id AS member
      , CASE WHEN order_id IS NOT NULL THEN 1 ELSE 0 END AS repeat_order_count
    FROM "data"."main"."repeat_valid_orders" repeat_valid_orders_src_10000
    WHERE DATE_TRUNC('day', ordered_at) BETWEEN '2026-08-01' AND '2026-08-31'
  ) subq_16
  WHERE member in ('M00005','M00007')
  GROUP BY
    member
) subq_20
ON
  subq_12.member = subq_20.member
FULL OUTER JOIN (
  SELECT
    member
    , SUM(valid_order_count) AS valid_order_count
  FROM (
    SELECT
      member_id AS member
      , CASE WHEN case when status = 'paid' and paid_cents - refund_cents > 0 then order_id else null end IS NOT NULL THEN 1 ELSE 0 END AS valid_order_count
    FROM "data"."main"."orders" orders_src_10000
    WHERE DATE_TRUNC('day', ordered_at) BETWEEN '2026-08-01' AND '2026-08-31'
  ) subq_24
  WHERE member in ('M00005','M00007')
  GROUP BY
    member
) subq_28
ON
  COALESCE(subq_12.member, subq_20.member) = subq_28.member
GROUP BY
  COALESCE(subq_12.member, subq_20.member, subq_28.member)
