WITH valid_orders AS (
  SELECT *,
         paid_cents - refund_cents AS net_sales_cents
  FROM "data"."main"."orders"
  WHERE status = 'paid' AND paid_cents - refund_cents > 0
),
ranked AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY ordered_at, order_id) AS rn
  FROM valid_orders
)
SELECT order_id, member_id, ordered_at, net_sales_cents
FROM ranked
WHERE rn >= 2