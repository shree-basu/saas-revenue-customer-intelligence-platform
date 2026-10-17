# Certified local metric contracts

All amounts are synthetic USD. These marts are demonstrated in local DuckDB/dbt; cloud execution, booked revenue, invoicing recognition, real customer outcomes and forecast accuracy are **not** evidenced.

| Mart | Grain | Definition |
| --- | --- | --- |
| `mart_mrr_waterfall` | One observed movement month after baseline | Opening MRR + signed new + expansion + contraction + churn = closing MRR. Flat movement contributes zero. Closing reconciles to normalized monthly subscription MRR. |
| `mart_revenue_retention` | Same month | Gross retention = (opening + contraction + churn) / opening. Net retention adds expansion; both exclude new MRR. If opening is zero, percentage is NULL, not an invented 100%. |
| `mart_revenue_vs_target` | Latest observed month × current region × current segment | Actual ARR = monthly subscription MRR × 12; compares against synthetic planned ARR, not recognized revenue. Attainment = actual/target × 100, NULL for a missing/zero target or missing actual. Full outer join keeps unmatched planning or actual groups visible. |

Only the latest month uses current account region/segment; this does not assert historical as-of customer classification. The two-month synthetic source is enough to exercise movement arithmetic but not long-horizon cohort retention or trend claims. Date and currency domains remain those of the validated source contract.
