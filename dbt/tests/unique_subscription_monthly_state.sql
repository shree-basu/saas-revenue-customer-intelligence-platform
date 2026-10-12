select subscription_id, state_month
from {{ ref('int_subscription_monthly_mrr') }}
group by subscription_id, state_month
having count(*) > 1
