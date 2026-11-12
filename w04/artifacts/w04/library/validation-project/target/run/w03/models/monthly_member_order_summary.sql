
  
  create view "data"."main"."monthly_member_order_summary__dbt_tmp" as (
    with valid_orders as (
  select member_id, date_trunc('month', ordered_at)::date as month_start, paid_cents - refund_cents as net_sales_cents
  from "data"."main"."orders"
  where status = 'paid' and paid_cents - refund_cents > 0
)
select member_id, month_start, count(*) as valid_order_count, sum(net_sales_cents) as net_sales_cents
from valid_orders
group by member_id, month_start
  );
