-- One support case per case_id; open cases have no closed date.
select
    md5(s.case_id) as case_key,
    s.case_id,
    s.account_id,
    a.account_key,
    d.date_key as opened_date_key,
    s.opened_at,
    s.closed_at,
    s.severity,
    s.category,
    s.status,
    s.sla_breached,
    s.resolution_minutes,
    s.updated_at
from {{ ref('stg_support_cases') }} as s
left join {{ ref('dim_account') }} as a on s.account_id = a.account_id
left join {{ ref('dim_date') }} as d on cast(s.opened_at as date) = d.calendar_date
