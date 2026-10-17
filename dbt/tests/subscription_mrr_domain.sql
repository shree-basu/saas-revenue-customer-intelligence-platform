select subscription_id, state_month
from {{ ref('int_subscription_monthly_mrr') }}
where mrr_usd < 0
   or currency <> 'USD'
   or (subscription_status <> 'ACTIVE' and mrr_usd <> 0)
   or (subscription_status = 'ACTIVE' and mrr_usd <= 0)
