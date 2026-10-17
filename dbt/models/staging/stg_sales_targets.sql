select
    try_cast(target_month as date) as target_month,
    upper(trim(region)) as region,
    upper(trim(segment)) as segment,
    try_cast(arr_target as decimal(18, 2)) as arr_target,
    try_cast(new_arr_target as decimal(18, 2)) as new_arr_target,
    try_cast(renewal_target as decimal(18, 2)) as renewal_target,
    try_cast(updated_at as timestamp) as updated_at
from {{ source('raw', 'sales_targets') }}
