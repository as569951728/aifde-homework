
  
  create view "data"."main"."order_sequence__dbt_tmp" as (
    WITH valid_orders AS (
  SELECT
    o.*,
    ROW_NUMBER() OVER (PARTITION BY o.member_id ORDER BY o.ordered_at, o.order_id) AS valid_order_seq
  FROM "data"."main"."orders" o
  WHERE o.status = 'paid' AND o.paid_cents - o.refund_cents > 0
)
SELECT * FROM valid_orders
  );
