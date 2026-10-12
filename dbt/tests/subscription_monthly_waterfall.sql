with monthly as (
    select
        state_month,
        sum(prior_mrr_usd) as opening_mrr_usd,
        sum(ending_mrr_usd) as closing_mrr_usd,
        sum(case when movement_type = 'NEW' then movement_mrr_usd else 0 end) as new_mrr_usd,
        sum(case when movement_type = 'EXPANSION' then movement_mrr_usd else 0 end) as expansion_mrr_usd,
        sum(case when movement_type = 'CONTRACTION' then movement_mrr_usd else 0 end) as contraction_mrr_usd,
        sum(case when movement_type = 'CHURN' then movement_mrr_usd else 0 end) as churn_mrr_usd
    from {{ ref('fct_subscription_movements') }}
    group by state_month
)
select state_month
from monthly
where opening_mrr_usd + new_mrr_usd + expansion_mrr_usd
    + contraction_mrr_usd + churn_mrr_usd <> closing_mrr_usd
