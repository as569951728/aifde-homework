WITH valid_orders AS (
  SELECT
    o.member_id,
    CAST(date_trunc('month', o.ordered_at) AS DATE) AS month_start,
    o.paid_cents - o.refund_cents AS net_sales_cents
  FROM "data"."main"."orders" o
  WHERE o.status = 'paid' AND o.paid_cents - o.refund_cents > 0
),
monthly AS (
  SELECT
    member_id,
    month_start,
    COUNT(*) AS valid_order_count,
    SUM(net_sales_cents) AS net_sales_cents
  FROM valid_orders
  GROUP BY member_id, month_start
)
SELECT
  member_id,
  month_start,
  member_id || '|' || CAST(month_start AS VARCHAR) AS member_month_key,
  valid_order_count,
  net_sales_cents
FROM monthly