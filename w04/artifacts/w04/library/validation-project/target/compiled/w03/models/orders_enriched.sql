with valid_orders as (
  select order_id, member_id, ordered_at
  from "data"."main"."orders"
  where status = 'paid' and paid_cents - refund_cents > 0
),
ranked as (
  select order_id,
         row_number() over (partition by member_id order by ordered_at, order_id) as valid_order_seq
  from valid_orders
),
flags as (
  select order_id, valid_order_seq,
         case when valid_order_seq = 1 then true else false end as is_first_valid_order,
         case when valid_order_seq >= 2 then true else false end as is_repeat_valid_order
  from ranked
)
select o.order_id, o.member_id, o.store_id, o.ordered_at, o.status, o.gross_cents, o.paid_cents, o.refund_cents, o.quantity, o.channel,
       o.paid_cents - o.refund_cents as net_sales_cents,
       f.valid_order_seq,
       coalesce(f.is_first_valid_order, false) as is_first_valid_order,
       coalesce(f.is_repeat_valid_order, false) as is_repeat_valid_order
from "data"."main"."orders" o
left join flags f on o.order_id = f.order_id