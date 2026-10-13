select account_id
from {{ ref('snap_account_history') }}
where dbt_valid_to is null
group by account_id
having count(*) <> 1
