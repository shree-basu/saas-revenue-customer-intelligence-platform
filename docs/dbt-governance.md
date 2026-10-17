# dbt governance boundary

The `safe_ratio` macro centralizes NULL-on-zero denominator behavior. Its only consumers are retention and target-attainment percentages; it does not hide missing source rows. The `mart_mrr_waterfall` table has an enforced column/type contract in the local dbt target, alongside uniqueness and reconciliation tests. This does not prove that the same DDL has been run in Snowflake.

The unit test covers a 100 USD opening-MRR month with 20 new, 10 expansion, -5 contraction and -10 churn: GRR is 85%, NRR is 95%. A zero-opening month has NULL retention. Singular tests enforce waterfall conservation and current-batch source-date coherence. The latter compares source dates to the latest observed usage date in this immutable synthetic delivery; it is **not** a production wall-clock freshness SLA. Real source freshness would require an ingest/load timestamp and an operational schedule, neither of which this local example claims.

The dbt exposure named `proposed_executive_saas_semantic_model` traces intended dependencies for a future Fabric/Power BI model. It is explicitly planned, not proof that any dashboard or semantic model has been created.
