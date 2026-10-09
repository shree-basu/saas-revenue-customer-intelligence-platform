# Ten-day implementation roadmap

Two coherent commits per day; a third only for a real isolated correction. Never create streak-only commits. Stop after the stated day, and do not merge before A1's focused final review.

| Day | Commit A | Commit B |
| --- | --- | --- |
| 1 | Zero-cost foundation, architecture, safety, CI | Deterministic immutable source contracts and local dbt foundation |
| 2 | Complete staging and source DQ | Snowflake reference SQL for roles, grants, warehouses, monitor, tagging and cost controls; static validation only |
| 3 | Account history/SCD design, product and date dimensions | Invoice, usage and support facts with grains and referential tests |
| 4 | Subscription-state normalization and MRR contract | Movement fact for new, expansion, contraction and churn with conservation tests |
| 5 | Replay-safe incremental models and late updates | dbt snapshots/SCD2, schema-change and backfill tests |
| 6 | Customer 360, renewals and explainable health | MRR waterfall, retention and revenue-vs-target marts with reconciliation |
| 7 | Useful macros, contracts, singular/unit tests, freshness and exposures | Snowflake governance/optimization design without unmeasured claims |
| 8 | Official-format Fabric Data Pipeline static ingestion definition | Verified Mirroring definition if published, otherwise accurate contract |
| 9 | Official-format TMDL semantic model and relationships | Governed DAX measures and static validation |
| 10 | End-to-end local replay demo and operational runbook | Evidence/security/CI hardening, final PR and A1 handoff |

Day 2 starts by finishing all source staging models and source DQ. No future-day work is included in Day 1.
