select
    md5(product_id) as product_key,
    product_id,
    product_name,
    product_family,
    is_active
from {{ ref('stg_products') }}
