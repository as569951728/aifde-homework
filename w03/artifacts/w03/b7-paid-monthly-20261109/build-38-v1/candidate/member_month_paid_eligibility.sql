with member_months as (
  select distinct member_id, month_start
  from {{ ref('monthly_member_order_summary') }}
),
elig as (
  select mm.member_id, mm.month_start,
         case when exists (
           select 1
           from {{ ref('cards') }} c
           where c.member_id = mm.member_id
             and c.card_type in ('悦享年卡', '家庭季卡')
             and c.valid_from <= (mm.month_start + interval '1 month' - interval '1 day')::date
             and (mm.month_start + interval '1 month' - interval '1 day')::date < c.valid_until
             and (c.ended_at is null or (mm.month_start + interval '1 month' - interval '1 day')::date < c.ended_at)
         ) then true else false end as is_paid_eligible
  from member_months mm
)
select member_id, month_start, is_paid_eligible from elig