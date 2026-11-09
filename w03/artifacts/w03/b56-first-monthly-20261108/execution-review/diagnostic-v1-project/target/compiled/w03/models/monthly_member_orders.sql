WITH valid_orders AS (
  SELECT member_id, order_id, ordered_at, paid_cents - refund_cents AS net_sales_cents
  FROM "data"."main"."orders"
  WHERE status = 'paid' AND paid_cents - refund_cents > 0
),
monthly AS (
  SELECT member_id,
         CAST(DATE_TRUNC('month', ordered_at) AS DATE) AS month_start,
         COUNT(DISTINCT order_id) AS valid_order_count,
         SUM(net_sales_cents) AS net_sales_cents
  FROM valid_orders
  GROUP BY member_id, CAST(DATE_TRUNC('month', ordered_at) AS DATE)
)
SELECT member_id,
       month_start,
       member_id || '|' || CAST(month_start AS VARCHAR) AS member_month_key,
       valid_order_count,
       net_sales_cents
FROM monthly