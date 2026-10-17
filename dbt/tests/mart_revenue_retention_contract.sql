select reporting_month
from {{ ref('mart_revenue_retention') }}
where (opening_mrr_usd = 0 and (
    gross_revenue_retention_pct is not null or net_revenue_retention_pct is not null
)) or (opening_mrr_usd > 0 and (
    gross_revenue_retention_pct is null or net_revenue_retention_pct is null
))
