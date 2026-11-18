WITH valid_orders AS (
  SELECT member_id, ordered_at, paid_cents, refund_cents
  FROM {{ ref('orders') }}
  WHERE status = 'paid' AND paid_cents - refund_cents > 0
),
member_month AS (
  SELECT member_id,
         CAST(date_trunc('month', ordered_at) AS DATE) AS month_start,
         CAST(date_trunc('month', ordered_at) + INTERVAL '1 month' - INTERVAL '1 day' AS DATE) AS month_end,
         COUNT(*) AS valid_order_count,
         SUM(paid_cents - refund_cents) AS net_sales_cents
  FROM valid_orders
  GROUP BY 1, 2, 3
)
SELECT mm.member_id || '|' || CAST(mm.month_start AS VARCHAR) AS member_month_key,
       mm.member_id, mm.month_start, mm.valid_order_count, mm.net_sales_cents,
       CASE WHEN mm.valid_order_count >= 1 THEN 1 ELSE 0 END AS buyer_flag,
       CASE WHEN mm.valid_order_count >= 2 THEN 1 ELSE 0 END AS repeat_buyer_flag
FROM member_month mm
WHERE EXISTS (
  SELECT 1
  FROM {{ ref('cards') }} c
  WHERE c.member_id = mm.member_id
    AND c.card_type IN ('悦享年卡', '家庭季卡')
    AND c.valid_from <= mm.month_end
    AND c.valid_until > mm.month_end
    AND (c.ended_at IS NULL OR c.ended_at > mm.month_end)
)