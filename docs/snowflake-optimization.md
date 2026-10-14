# Snowflake performance and governance decision record

This is a **review procedure**, not benchmark evidence. No Snowflake database, warehouse, query profile, credits, storage, or query history was created or measured. The diagnostic worksheet under `snowflake/sql/03_diagnostic_queries.sql` is static, read-only design material and is not called by CI.

## Pruning before clustering

Snowflake automatically stores table data in micro-partitions and can prune them using metadata. Unlike BigQuery, this project does **not** declare manual date partitions. The default decision for the small synthetic invoice, usage, movement, and mart tables is **no clustering key**. In a future real deployment, capture representative predicates, query profiles, partition-scanned/total ratios, scan time and clustering depth on large tables. Consider a date-oriented clustering expression only if selective date filters dominate and poor pruning persists. Compare before/after elapsed time and credit cost over the same workload, including automatic reclustering compute and storage churn. A high-cardinality account identifier is not an automatic cluster key. Do not turn on Search Optimization or materialized views without a measured workload case.

## Workload and compute isolation

The existing example warehouse is a suspended X-Small **transformation** reference. An actual deployment would propose independently approved ingestion and BI compute only if concurrency or operational isolation justified them; it would not share an unrestricted transform role with dashboard readers. Compare query queue/overload time, runtime and spill before resizing or adding clusters. A warehouse monitor reduces risk but is not a currency hard cap. Auto-resume is deliberately false in the static example.

## Cost attribution and recovery

The static worksheet shows query-history and per-query compute-attribution views, filtered by example query tags. An authorized future operator would need separately granted monitoring access. Query-attributed credits exclude warehouse idle time and other possible charges; reconciliation would also require warehouse metering, storage, cloud-services, serverless and data-transfer review. No numerical saving is claimed. Time Travel can aid controlled recovery after erroneous writes, but retained history consumes storage. Zero-copy clones initially share micro-partitions; later writes or retention can add storage cost. Neither a clone nor a Time Travel recovery is created here. A real recovery runbook must specify retention, ownership, validation of restored rows and deletion of temporary objects.

The decision rules follow Snowflake's [micro-partition guidance](https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions), [clustering guidance](https://docs.snowflake.com/en/user-guide/tables-clustering-keys), [query-attribution limits](https://docs.snowflake.com/en/sql-reference/account-usage/query_attribution_history), and [storage/clone accounting](https://docs.snowflake.com/en/user-guide/cost-understanding-data-storage). Static review cannot prove runtime compatibility or performance.
