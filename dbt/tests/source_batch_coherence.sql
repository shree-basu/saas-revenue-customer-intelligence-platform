-- Deterministic batch-relative recency; this is not a wall-clock source SLA.
with reporting as (
    select max(usage_date) as business_date
    from {{ ref('stg_product_usage_daily') }}
), source_dates as (
    select 'accounts' as entity, max(cast(updated_at as date)) as latest_date
    from {{ ref('stg_accounts') }}
    union all
    select 'subscriptions', max(cast(updated_at as date)) from {{ ref('stg_subscriptions') }}
    union all
    select 'invoices', max(cast(updated_at as date)) from {{ ref('stg_invoices') }}
    union all
    select 'usage', max(usage_date) from {{ ref('stg_product_usage_daily') }}
    union all
    select 'support', max(cast(updated_at as date)) from {{ ref('stg_support_cases') }}
    union all
    select 'targets', max(cast(updated_at as date)) from {{ ref('stg_sales_targets') }}
)
select entity, latest_date, reporting.business_date
from source_dates cross join reporting
where latest_date is null or reporting.business_date is null
    or latest_date <> reporting.business_date
