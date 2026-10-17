with latest_month as (
    select max(state_month) as reporting_month
    from {{ ref('int_subscription_monthly_mrr') }}
), actual as (
    select cast(sum(s.mrr_usd) * 12 as decimal(18, 2)) as arr_usd
    from {{ ref('int_subscription_monthly_mrr') }} as s
    inner join latest_month as lm on s.state_month = lm.reporting_month
), target as (
    select sum(t.arr_target) as target_arr_usd
    from {{ ref('stg_sales_targets') }} as t
    inner join latest_month as lm on t.target_month = lm.reporting_month
), mart as (
    select sum(actual_arr_usd) as arr_usd, sum(target_arr_usd) as target_arr_usd,
        count(*) - count(distinct cast(reporting_month as varchar) || '|' || region || '|' || segment)
            as duplicate_grain
    from {{ ref('mart_revenue_vs_target') }}
)
select 1
from actual cross join target cross join mart
where actual.arr_usd <> mart.arr_usd
    or target.target_arr_usd <> mart.target_arr_usd
    or mart.duplicate_grain <> 0
