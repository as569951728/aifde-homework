WITH months AS (
  SELECT DISTINCT
    CAST(date_trunc('month', date_day) AS DATE) AS month_start,
    CAST(last_day(date_trunc('month', date_day)) AS DATE) AS month_end
  FROM {{ ref('time_spine') }}
),
eligible AS (
  SELECT
    m.member_id,
    mo.month_start,
    mo.month_end
  FROM {{ ref('members') }} m
  CROSS JOIN months mo
  WHERE EXISTS (
    SELECT 1
    FROM {{ ref('cards') }} c
    WHERE c.member_id = m.member_id
      AND c.card_type IN ('悦享年卡', '家庭季卡')
      AND c.valid_from <= mo.month_end
      AND c.valid_until > mo.month_end
      AND (c.ended_at IS NULL OR c.ended_at > mo.month_end)
  )
),
order_monthly AS (
  SELECT
    o.member_id,
    CAST(date_trunc('month', o.ordered_at) AS DATE) AS month_start,
    COUNT(*) FILTER (
      WHERE o.status = 'paid'
        AND o.paid_cents - o.refund_cents > 0
    ) AS valid_order_count,
    COALESCE(SUM(
      CASE
        WHEN o.status = 'paid'
          AND o.paid_cents - o.refund_cents > 0
        THEN o.paid_cents - o.refund_cents
        ELSE 0
      END
    ), 0) AS net_sales_cents
  FROM {{ ref('orders') }} o
  GROUP BY 1, 2
)
SELECT
  e.member_id || '|' || CAST(e.month_start AS VARCHAR) AS member_month_key,
  e.member_id,
  e.month_start,
  e.month_end,
  COALESCE(om.valid_order_count, 0) AS valid_order_count,
  COALESCE(om.net_sales_cents, 0) AS net_sales_cents
FROM eligible e
LEFT JOIN order_monthly om
  ON e.member_id = om.member_id
 AND e.month_start = om.month_start