-- Current account state only. Historical SCD2 rows are a separate Day-5 snapshot.
select
    md5(account_id) as account_key,
    account_id,
    account_name,
    segment,
    industry,
    region,
    country,
    sales_owner,
    customer_success_manager,
    account_status,
    created_at,
    updated_at
from {{ ref('stg_accounts') }}
