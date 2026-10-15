# Semantic model design (offline only)

`fabric/semantic/ExecutiveSaaS.SemanticModel` uses the published `definition.pbism` plus `definition/` TMDL layout. Its five Import partitions are deliberately empty local Power Query `#table` expressions. There is no Fabric workspace, OneLake binding, Snowflake connection, refresh schedule or publishing workflow. Importing it as-is would show **zero data**; it is not a deployed dashboard.

| TMDL table | Proposed certified mart | Grain |
| --- | --- | --- |
| Customers | `MART_CUSTOMER_360` | Current account |
| Renewals | `MART_RENEWAL_PIPELINE` | Active renewing subscription |
| MRRWaterfall | `MART_MRR_WATERFALL` | Observed movement month |
| Retention | `MART_REVENUE_RETENTION` | Same month |
| ARRTargets | `MART_REVENUE_VS_TARGET` | Latest month, region, segment |

The only relationship is `Customers.account_id` (one) to `Renewals.account_id` (many). Monetary marts stay disconnected to prevent an invalid account or date filter from silently changing their grain. Their measures must be evaluated in their own month/region/segment context. In a real approved deployment, replace the inert partitions with tested, narrowly scoped certified-mart bindings; verify source types, uniqueness, row-level access, refresh/reconciliation and cost before publishing. This design has **static structural checks only**, not TMDL deserialization in Power BI or service-side execution.

The DAX measure layer does not redefine dbt revenue arithmetic. Current MRR/ARR and renewal risk aggregate only their current-grain rows. Opening/closing MRR and retention return blank across multiple reporting months; these are non-additive balances and ratios. Retention values are stored as 0–100 percentages and displayed as numbers, not multiplied by 100 again. ARR attainment refuses incomplete target/actual groups and divides summed actual by summed target for the selected latest-month grouping. Measures do not imply a real report or tested DAX runtime.

Sources: [Microsoft semantic-model definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition), [TMDL overview](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview).
