select
    trim(product_id) as product_id,
    trim(product_name) as product_name,
    upper(trim(product_family)) as product_family,
    case when lower(trim(active)) = 'true' then true else false end as is_active
from {{ source('raw', 'products') }}
