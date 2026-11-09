WITH paid_orders AS (
  SELECT
    member_id,
    CAST(date_trunc('month', ordered_at) AS DATE) AS month_start,
    paid_cents - refund_cents AS net_cents
  FROM {{ ref('orders') }}
  WHERE status = 'paid'
),
monthly AS (
  SELECT
    member_id,
    month_start,
    SUM(net_cents) AS net_receipts_cents
  FROM paid_orders
  GROUP BY member_id, month_start
),
flagged AS (
  SELECT
    member_id,
    month_start,
    net_receipts_cents,
    CASE WHEN net_receipts_cents >= 10000 THEN 1 ELSE 0 END AS large_buyer_flag
  FROM monthly
)
SELECT
  row_number() OVER (ORDER BY member_id, month_start) AS monthly_member_row_id,
  member_id,
  month_start,
  net_receipts_cents,
  large_buyer_flag
FROM flagged