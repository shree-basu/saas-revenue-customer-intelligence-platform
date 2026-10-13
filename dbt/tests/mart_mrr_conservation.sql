with source_month as (
    select state_month, sum(mrr_usd) as source_mrr_usd
    from {{ ref('int_subscription_monthly_mrr') }}
    group by state_month
)
select w.reporting_month
from {{ ref('mart_mrr_waterfall') }} as w
left join source_month as s on w.reporting_month = s.state_month
where w.opening_mrr_usd + w.new_mrr_usd + w.expansion_mrr_usd
    + w.contraction_mrr_usd + w.churn_mrr_usd <> w.closing_mrr_usd
    or w.closing_mrr_usd <> s.source_mrr_usd
    or s.state_month is null
