select target_month, region, segment
from {{ ref('stg_sales_targets') }}
group by target_month, region, segment
having count(*) > 1
