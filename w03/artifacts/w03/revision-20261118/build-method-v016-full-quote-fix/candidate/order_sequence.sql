WITH valid_orders AS (
  SELECT o.order_id, o.member_id, o.store_id, o.ordered_at, o.channel, o.status, o.quantity,
         o.paid_cents - o.refund_cents AS net_sales_cents,
         ROW_NUMBER() OVER (PARTITION BY o.member_id ORDER BY o.ordered_at, o.order_id) AS valid_order_seq
  FROM {{ ref('orders') }} o
  WHERE o.status = 'paid' AND o.paid_cents - o.refund_cents > 0
)
SELECT order_id, member_id, store_id, ordered_at, channel, status, quantity, net_sales_cents,
       valid_order_seq,
       CASE WHEN valid_order_seq = 1 THEN 1 ELSE 0 END AS is_first_valid,
       CASE WHEN valid_order_seq >= 2 THEN 1 ELSE 0 END AS is_repeat_valid
FROM valid_orders