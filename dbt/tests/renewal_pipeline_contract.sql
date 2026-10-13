select subscription_id
from {{ ref('mart_renewal_pipeline') }}
where days_until_renewal not between 0 and 90
    or renewal_arr_usd <= 0
