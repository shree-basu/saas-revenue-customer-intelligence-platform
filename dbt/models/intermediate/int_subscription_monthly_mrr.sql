-- Contract value is for the whole subscription, not a per-seat price.
-- USD-only; fixed-point HALF_AWAY_FROM_ZERO to cents in both local and target SQL.
select
    subscription_id,
    account_id,
    product_id,
    state_month,
    billing_frequency,
    quantity,
    contract_value,
    currency,
    subscription_status,
    cast(
        case
            when subscription_status <> 'ACTIVE' then 0
            when billing_frequency = 'ANNUAL' then round(contract_value / 12, 2)
            else contract_value
        end as decimal(18, 2)
    ) as mrr_usd,
    updated_at
from {{ ref('stg_subscription_monthly_states') }}
