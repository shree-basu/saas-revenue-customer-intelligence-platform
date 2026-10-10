select
    trim(account_id) as account_id,
    trim(product_id) as product_id,
    try_cast(usage_date as date) as usage_date,
    try_cast(active_users as integer) as active_users,
    try_cast(licensed_users as integer) as licensed_users,
    try_cast(sessions as integer) as sessions,
    try_cast(api_calls as integer) as api_calls,
    try_cast(failed_requests as integer) as failed_requests,
    try_cast(usage_minutes as integer) as usage_minutes,
    try_cast(updated_at as timestamp) as updated_at
from {{ source('raw', 'product_usage_daily') }}
