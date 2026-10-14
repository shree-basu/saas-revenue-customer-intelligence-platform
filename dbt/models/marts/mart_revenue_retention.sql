-- Zero opening MRR makes dollar retention undefined, not zero or 100%.
select reporting_month, opening_mrr_usd, closing_mrr_usd,
    new_mrr_usd, expansion_mrr_usd, contraction_mrr_usd, churn_mrr_usd,
    cast(100 * {{ safe_ratio(
        'opening_mrr_usd + contraction_mrr_usd + churn_mrr_usd', 'opening_mrr_usd'
    ) }} as decimal(18, 4)) as gross_revenue_retention_pct,
    cast(100 * {{ safe_ratio(
        'opening_mrr_usd + expansion_mrr_usd + contraction_mrr_usd + churn_mrr_usd',
        'opening_mrr_usd'
    ) }} as decimal(18, 4)) as net_revenue_retention_pct
from {{ ref('mart_mrr_waterfall') }}
