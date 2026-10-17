# Global SaaS Revenue & Customer Intelligence Platform

**Status: ten-day local reference implementation complete; awaiting A1 review.** This is a synthetic, cloud-free analytics-engineering reference, not a deployed service or a claim of production operation.

## Business problem

A global B2B SaaS company needs consistent answers for recurring revenue, renewals, customer usage, support pressure, overdue invoices and sales-target attainment. Finance, Revenue Operations and Customer Success must share definitions rather than independently rebuild them in dashboards.

## Target architecture

Snowflake is the governed enterprise warehouse. dbt owns transformations, tests and certified business marts inside that warehouse. Microsoft Fabric Data Factory is the proposed integration route for Microsoft-side planning data. Only certified marts cross to Fabric Snowflake Mirroring/OneLake; a Power BI semantic model provides context-dependent measures. Fabric and Power BI do not reimplement foundational dbt business rules.

```mermaid
flowchart LR
  CRM[CRM / subscriptions / billing / usage / support] --> RAW[Snowflake raw — target only]
  PLAN[Microsoft-side sales targets] --> FDF[Fabric Data Factory — target only] --> RAW
  RAW --> DBT[dbt staging → core → certified marts — target]
  DBT --> SF[Snowflake consumers]
  DBT --> MIRROR[Fabric Snowflake Mirroring / OneLake — target only]
  MIRROR --> PBI[Power BI semantic model — inert TMDL design only]
  LOCAL[Synthetic immutable batches] --> DUCK[DuckDB local reference]
  DUCK --> LDBT[dbt local target]
```

The local DuckDB path is the executable proof; it cannot establish Snowflake or Fabric runtime behaviour. A real mirror can incur Snowflake compute and Fabric capacity costs, so no mirror is configured here.

## Evidence boundary

| Category | Current position |
| --- | --- |
| Implemented and locally tested | Deterministic synthetic source contracts, nine validated staging models, current dimensions, merge-based invoice/usage/support facts, account-history snapshot, monthly MRR and movement facts, customer/renewal marts, MRR/retention/ARR-vs-target marts, replay/backfill/schema-gate checks, an enforced local mart contract, unit/reconciliation tests and a local end-to-end correction/replay demonstration. |
| Statically specified | Snowflake governance/diagnostic SQL; inert Fabric DataPipeline/MirroredDatabase definitions; empty-import TMDL semantic model with DAX measure definitions and offline structural checks. No real connection or cloud execution. |
| Production target, not deployed | Snowflake warehouse, Fabric Data Factory, Mirroring/OneLake and Power BI Service. |
| Not evidenced | Real customers, Snowflake/Fabric/Power BI execution, DAX engine evaluation, scale, cloud cost, SLA, performance or service-side security enforcement. |

See [architecture](docs/architecture.md), [safety](docs/safety.md), [semantic-model scope](docs/semantic-model.md), [operations runbook](docs/runbook.md) and the [10-day roadmap](docs/10-day-roadmap.md). No CV claim of a completed production platform is justified.

## Local run

Use the hash-locked `requirements.lock` in a local virtual environment. Then generate and validate a synthetic batch; the landing step refuses a failed contract:

```text
python -m data.generate_saas_batch --business-date 2026-10-09 --batch-id demo-1 --seed 17 --accounts 12 --scenario normal --output-root data/input
python -m local.landing --delivery data/input/business_date=2026-10-09/batch_id=demo-1 --database dbt/target/saas.duckdb
dbt build --project-dir dbt --profiles-dir dbt --target local
```

The `snowflake_static` profile contains deliberately fake identifiers. Do not run it or substitute real credentials. For the full local correction/replay path, run `python -m scripts.run_local_demo` and follow the [runbook](docs/runbook.md). Day 2 completed staging and source DQ, plus [static Snowflake design examples](snowflake/README.md). Day 3 added the [dimensional core](docs/data-model.md). Day 4 added the [subscription MRR and movement contract](docs/revenue-contract.md). Day 5 added [incremental replay and account-history evidence](docs/incremental-processing.md). Day 6 added [customer decision marts](docs/customer-marts.md) and [local metric contracts](docs/metric-contracts.md). Day 7 added [dbt governance](docs/dbt-governance.md) and an [unmeasured Snowflake optimization decision record](docs/snowflake-optimization.md). Day 8 added [inert Fabric item definitions and integration contracts](docs/fabric-design.md), **not** a running ingest or mirror. Day 9 added [inert TMDL and DAX definitions](docs/semantic-model.md), **not** a published semantic model. See the [source contract](docs/source-contracts.md). No historical as-of fact join is claimed.
