
  
  create view "data"."main"."monthly_paid_member_summary__dbt_tmp" as (
    with summary as (
  select member_id, month_start, valid_order_count, net_sales_cents
  from "data"."main"."monthly_member_order_summary"
),
elig as (
  select member_id, month_start, is_paid_eligible
  from "data"."main"."member_month_paid_eligibility"
)
select s.member_id, s.month_start, s.valid_order_count, s.net_sales_cents, e.is_paid_eligible
from summary s
join elig e using (member_id, month_start)
  );
