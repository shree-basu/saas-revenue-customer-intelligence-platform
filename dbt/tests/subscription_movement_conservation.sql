select subscription_id, state_month
from {{ ref('fct_subscription_movements') }}
where prior_mrr_usd + movement_mrr_usd <> ending_mrr_usd
   or (movement_type = 'NEW' and not (prior_mrr_usd = 0 and ending_mrr_usd > 0))
   or (movement_type = 'CHURN' and not (prior_mrr_usd > 0 and ending_mrr_usd = 0))
   or (movement_type = 'EXPANSION' and not (prior_mrr_usd > 0 and ending_mrr_usd > prior_mrr_usd))
   or (movement_type = 'CONTRACTION' and not (ending_mrr_usd > 0 and ending_mrr_usd < prior_mrr_usd))
   or (movement_type = 'FLAT' and prior_mrr_usd <> ending_mrr_usd)
