select account_id, product_id, usage_date
from {{ ref('stg_product_usage_daily') }}
group by account_id, product_id, usage_date
having count(*) > 1
