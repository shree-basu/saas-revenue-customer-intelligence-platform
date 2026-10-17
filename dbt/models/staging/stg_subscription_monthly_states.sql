select
    trim(subscription_id) as subscription_id,
    trim(account_id) as account_id,
    trim(product_id) as product_id,
    try_cast(state_month as date) as state_month,
    upper(trim(billing_frequency)) as billing_frequency,
    try_cast(quantity as integer) as quantity,
    try_cast(contract_value as decimal(18, 2)) as contract_value,
    upper(trim(currency)) as currency,
    upper(trim(subscription_status)) as subscription_status,
    try_cast(updated_at as timestamp) as updated_at
from {{ source('raw', 'subscription_monthly_states') }}
