-- One currently active subscription renewing within the next 90 days, inclusive.
with as_of_date as (
    select max(usage_date) as reporting_date
    from {{ ref('fct_product_usage_daily') }}
), latest_month as (
    select max(state_month) as state_month
    from {{ ref('int_subscription_monthly_mrr') }}
), latest_mrr as (
    select s.subscription_id, s.mrr_usd
    from {{ ref('int_subscription_monthly_mrr') }} as s
    cross join latest_month as lm
    where s.state_month = lm.state_month
)
select d.reporting_date, s.subscription_id, s.account_id, a.account_key,
    a.account_name, a.region, a.segment, s.product_id,
    s.renewal_date, s.renewal_date - d.reporting_date as days_until_renewal,
    m.mrr_usd as current_mrr_usd,
    cast(m.mrr_usd * 12 as decimal(18, 2)) as renewal_arr_usd
from {{ ref('stg_subscriptions') }} as s
cross join as_of_date as d
inner join latest_mrr as m on s.subscription_id = m.subscription_id
left join {{ ref('dim_account') }} as a on s.account_id = a.account_id
where s.subscription_status = 'ACTIVE'
    and m.mrr_usd > 0
    and s.renewal_date between d.reporting_date and d.reporting_date + 90
