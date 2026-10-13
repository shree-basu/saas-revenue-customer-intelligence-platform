-- Latest month only: current account attributes are not historical.
with latest_month as (
    select max(state_month) as reporting_month
    from {{ ref('int_subscription_monthly_mrr') }}
), actual as (
    select s.state_month as reporting_month, a.region, a.segment,
        cast(sum(s.mrr_usd) * 12 as decimal(18, 2)) as actual_arr_usd
    from {{ ref('int_subscription_monthly_mrr') }} as s
    inner join latest_month as lm on s.state_month = lm.reporting_month
    inner join {{ ref('dim_account') }} as a on s.account_id = a.account_id
    group by s.state_month, a.region, a.segment
), targets as (
    select t.target_month as reporting_month, t.region, t.segment,
        t.arr_target as target_arr_usd, t.new_arr_target as target_new_arr_usd
    from {{ ref('stg_sales_targets') }} as t
    inner join latest_month as lm on t.target_month = lm.reporting_month
)
select coalesce(a.reporting_month, t.reporting_month) as reporting_month,
    coalesce(a.region, t.region) as region,
    coalesce(a.segment, t.segment) as segment,
    a.actual_arr_usd, t.target_arr_usd, t.target_new_arr_usd,
    case when t.target_arr_usd > 0 and a.actual_arr_usd is not null
        then cast(100 * a.actual_arr_usd / t.target_arr_usd as decimal(18, 4))
    end as arr_attainment_pct,
    case
        when t.reporting_month is null then 'MISSING_TARGET'
        when a.reporting_month is null then 'MISSING_ACTUAL'
        else 'MATCHED'
    end as comparison_status
from actual as a
full outer join targets as t on a.reporting_month = t.reporting_month
    and a.region = t.region and a.segment = t.segment
