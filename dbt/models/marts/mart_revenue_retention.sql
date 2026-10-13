-- Zero opening MRR makes dollar retention undefined, not zero or 100%.
select reporting_month, opening_mrr_usd, closing_mrr_usd,
    new_mrr_usd, expansion_mrr_usd, contraction_mrr_usd, churn_mrr_usd,
    case when opening_mrr_usd > 0 then cast(
        100 * (opening_mrr_usd + contraction_mrr_usd + churn_mrr_usd)
        / opening_mrr_usd as decimal(18, 4)) end as gross_revenue_retention_pct,
    case when opening_mrr_usd > 0 then cast(
        100 * (opening_mrr_usd + expansion_mrr_usd + contraction_mrr_usd + churn_mrr_usd)
        / opening_mrr_usd as decimal(18, 4)) end as net_revenue_retention_pct
from {{ ref('mart_mrr_waterfall') }}
