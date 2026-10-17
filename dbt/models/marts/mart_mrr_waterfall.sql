-- One observed movement month; initial baseline month has no movement.
select state_month as reporting_month,
    cast(sum(prior_mrr_usd) as decimal(18, 2)) as opening_mrr_usd,
    cast(sum(case when movement_type = 'NEW' then movement_mrr_usd else 0 end) as decimal(18, 2)) as new_mrr_usd,
    cast(sum(case when movement_type = 'EXPANSION' then movement_mrr_usd else 0 end) as decimal(18, 2)) as expansion_mrr_usd,
    cast(sum(case when movement_type = 'CONTRACTION' then movement_mrr_usd else 0 end) as decimal(18, 2)) as contraction_mrr_usd,
    cast(sum(case when movement_type = 'CHURN' then movement_mrr_usd else 0 end) as decimal(18, 2)) as churn_mrr_usd,
    cast(sum(ending_mrr_usd) as decimal(18, 2)) as closing_mrr_usd
from {{ ref('fct_subscription_movements') }}
group by state_month
