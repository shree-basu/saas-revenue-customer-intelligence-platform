with ordered as (
    select
        account_id,
        dbt_valid_from,
        dbt_valid_to,
        lead(dbt_valid_from) over (
            partition by account_id order by dbt_valid_from
        ) as next_valid_from
    from {{ ref('snap_account_history') }}
)
select account_id, dbt_valid_from
from ordered
where (dbt_valid_to is not null and dbt_valid_to <= dbt_valid_from)
   or (next_valid_from is not null and dbt_valid_to <> next_valid_from)
   or (next_valid_from is null and dbt_valid_to is not null)
