select
    trim(account_id) as account_id,
    trim(account_name) as account_name,
    upper(trim(segment)) as segment,
    upper(trim(industry)) as industry,
    upper(trim(region)) as region,
    upper(trim(country)) as country,
    trim(sales_owner) as sales_owner,
    trim(customer_success_manager) as customer_success_manager,
    upper(trim(account_status)) as account_status,
    try_cast(created_at as timestamp) as created_at,
    try_cast(updated_at as timestamp) as updated_at
from {{ source('raw', 'accounts') }}
