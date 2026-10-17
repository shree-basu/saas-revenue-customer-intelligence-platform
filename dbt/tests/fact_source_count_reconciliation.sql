with actual as (
    select 'invoices' as entity, count(*) as row_count from {{ ref('fct_invoices') }}
    union all select 'usage', count(*) from {{ ref('fct_product_usage_daily') }}
    union all select 'support', count(*) from {{ ref('fct_support_cases') }}
), expected as (
    select 'invoices' as entity, count(*) as row_count from {{ ref('stg_invoices') }}
    union all select 'usage', count(*) from {{ ref('stg_product_usage_daily') }}
    union all select 'support', count(*) from {{ ref('stg_support_cases') }}
)
select actual.entity, actual.row_count as actual_rows, expected.row_count as expected_rows
from actual join expected on actual.entity = expected.entity
where actual.row_count <> expected.row_count
