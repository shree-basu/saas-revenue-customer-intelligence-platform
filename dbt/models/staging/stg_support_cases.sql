select
    trim(case_id) as case_id,
    trim(account_id) as account_id,
    try_cast(opened_at as timestamp) as opened_at,
    try_cast(nullif(trim(closed_at), '') as timestamp) as closed_at,
    upper(trim(severity)) as severity,
    upper(trim(category)) as category,
    upper(trim(status)) as status,
    case when lower(trim(sla_breached)) = 'true' then true else false end as sla_breached,
    try_cast(nullif(trim(resolution_minutes), '') as integer) as resolution_minutes,
    try_cast(updated_at as timestamp) as updated_at
from {{ source('raw', 'support_cases') }}
