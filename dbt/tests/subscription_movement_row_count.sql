with expected as (
    select count(*) - count(distinct subscription_id) as rows_expected
    from {{ ref('int_subscription_monthly_mrr') }}
), actual as (
    select count(*) as rows_actual from {{ ref('fct_subscription_movements') }}
)
select rows_expected, rows_actual
from expected cross join actual
where rows_expected <> rows_actual
