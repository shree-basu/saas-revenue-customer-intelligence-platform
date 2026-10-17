-- Sparse conformed calendar: only source-observed business dates, not every date in a range.
with observed_dates as (
    select invoice_date as calendar_date from {{ ref('stg_invoices') }}
    union select due_date from {{ ref('stg_invoices') }}
    union select paid_date from {{ ref('stg_invoices') }}
    union select usage_date from {{ ref('stg_product_usage_daily') }}
    union select cast(opened_at as date) from {{ ref('stg_support_cases') }}
    union select cast(closed_at as date) from {{ ref('stg_support_cases') }}
    union select subscription_start_date from {{ ref('stg_subscriptions') }}
    union select subscription_end_date from {{ ref('stg_subscriptions') }}
    union select renewal_date from {{ ref('stg_subscriptions') }}
    union select target_month from {{ ref('stg_sales_targets') }}
    union select state_month from {{ ref('stg_subscription_monthly_states') }}
)
select
    cast(extract(year from calendar_date) * 10000
        + extract(month from calendar_date) * 100
        + extract(day from calendar_date) as integer) as date_key,
    calendar_date,
    cast(extract(year from calendar_date) as integer) as calendar_year,
    cast(extract(month from calendar_date) as integer) as calendar_month,
    cast(extract(day from calendar_date) as integer) as day_of_month,
    cast(extract(quarter from calendar_date) as integer) as calendar_quarter
from observed_dates
where calendar_date is not null
