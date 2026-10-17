-- One account/product/usage date; zero values remain valid observations.
{{ config(materialized='incremental', unique_key='usage_key', incremental_strategy='merge', on_schema_change='fail') }}
select
    md5(u.account_id || '|' || u.product_id || '|' || cast(u.usage_date as varchar)) as usage_key,
    u.account_id,
    a.account_key,
    u.product_id,
    p.product_key,
    d.date_key as usage_date_key,
    u.usage_date,
    u.active_users,
    u.licensed_users,
    u.sessions,
    u.api_calls,
    u.failed_requests,
    u.usage_minutes,
    u.updated_at
from {{ ref('stg_product_usage_daily') }} as u
left join {{ ref('dim_account') }} as a on u.account_id = a.account_id
left join {{ ref('dim_product') }} as p on u.product_id = p.product_id
left join {{ ref('dim_date') }} as d on u.usage_date = d.calendar_date
