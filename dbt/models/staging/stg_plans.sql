select
    trim(plan_id) as plan_id,
    trim(plan_name) as plan_name,
    upper(trim(billing_frequency)) as billing_frequency,
    case when lower(trim(active)) = 'true' then true else false end as is_active
from {{ source('raw', 'plans') }}
