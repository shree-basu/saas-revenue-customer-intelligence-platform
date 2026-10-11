select i.invoice_id
from {{ ref('fct_invoices') }} as i
join {{ ref('stg_subscriptions') }} as s on i.subscription_id = s.subscription_id
where i.account_id <> s.account_id
