WITH orders AS (
    SELECT * FROM {{ ref('orders') }}
),
valid_ranked AS (
    SELECT o.*,
           ROW_NUMBER() OVER (PARTITION BY o.member_id ORDER BY o.ordered_at, o.order_id) AS valid_seq_all,
           ROW_NUMBER() OVER (PARTITION BY o.member_id, date_trunc('month', o.ordered_at) ORDER BY o.ordered_at, o.order_id) AS valid_seq_month
    FROM orders o
    WHERE o.status = 'paid' AND o.paid_cents - o.refund_cents > 0
),
order_base AS (
    SELECT o.*,
           CASE WHEN r.valid_seq_all = 1 THEN TRUE ELSE FALSE END AS is_first_valid_order,
           CASE WHEN r.valid_seq_all > 1 THEN TRUE ELSE FALSE END AS is_repeat_valid_order,
           CASE WHEN r.valid_seq_month > 1 THEN TRUE ELSE FALSE END AS is_monthly_repeat_order
    FROM orders o
    LEFT JOIN valid_ranked r ON o.order_id = r.order_id
),
month_ends AS (
    SELECT DISTINCT
           CAST(date_trunc('month', ordered_at) AS DATE) AS month_start,
           CAST(date_trunc('month', ordered_at) + INTERVAL 1 MONTH - INTERVAL 1 DAY AS DATE) AS month_end
    FROM orders
),
eligible AS (
    SELECT me.month_start, c.member_id
    FROM month_ends me
    JOIN {{ ref('cards') }} c
      ON c.card_type IN ('悦享年卡', '家庭季卡')
     AND c.valid_from <= me.month_end
     AND c.valid_until > me.month_end
     AND (c.ended_at IS NULL OR c.ended_at > me.month_end)
    GROUP BY me.month_start, c.member_id
)
SELECT b.*,
       CASE WHEN e.member_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_paid_eligible_month
FROM order_base b
LEFT JOIN eligible e
  ON b.member_id = e.member_id
 AND CAST(date_trunc('month', b.ordered_at) AS DATE) = e.month_start