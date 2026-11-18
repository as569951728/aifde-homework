WITH valid_orders AS (
  SELECT member_id, ordered_at, paid_cents, refund_cents
  FROM {{ ref('orders') }}
  WHERE status = 'paid' AND paid_cents - refund_cents > 0
),
monthly AS (
  SELECT member_id,
         CAST(date_trunc('month', ordered_at) AS DATE) AS month_start,
         COUNT(*) AS valid_order_count,
         SUM(paid_cents - refund_cents) AS net_sales_cents
  FROM valid_orders
  GROUP BY 1, 2
)
SELECT member_id || '|' || CAST(month_start AS VARCHAR) AS member_month_key,
       member_id, month_start, valid_order_count, net_sales_cents,
       CASE WHEN valid_order_count >= 1 THEN 1 ELSE 0 END AS buyer_flag,
       CASE WHEN valid_order_count >= 2 THEN 1 ELSE 0 END AS repeat_buyer_flag
FROM monthly