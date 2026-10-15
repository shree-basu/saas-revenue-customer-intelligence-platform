# Local operations and recovery runbook

This runbook is for synthetic DuckDB/dbt execution only. It does not authorize or describe a cloud deployment. Never run the `snowflake_static` profile, import Fabric items, connect Power BI to a workspace, or replace zero connection sentinels without a separate cost/security decision.

## Reproducible local replay

From the repository root, install `requirements.lock` into a local virtual environment, then run `python -m scripts.run_local_demo`. The demonstration creates isolated temporary deliveries and a DuckDB file, builds local dbt models, applies a late correction, and rebuilds the same delivery. It asserts customer count, changed invoice value/date, absence of duplicate invoice keys, MRR conservation, and identical replay results. Temporary data is removed when the process ends. It cannot establish scale, cloud runtime, SLA, service governance, or dashboard behavior.

## A failed batch

1. Keep the immutable delivery and manifest unchanged; inspect the validation error and source row, not only dbt output.
2. Do not bypass the contract, alter the manifest/hash in place, or publish a partially tested mart.
3. Correct the producer and create a **new batch ID**. Validate all nine source entities before local landing.
4. The loader's raw-table replacement is transactional. If it fails, the previous raw state remains. Re-run `dbt build --project-dir dbt --profiles-dir dbt --target local` only after a validated load.
5. For a correction or retry, compare row counts, natural-key uniqueness, MRR conservation and relevant customer/renewal marts. The local demo and test suite cover selected examples, not all possible input histories.

## Backfill and account history

Preserve the original deliveries. Rebuild into a **new** local DuckDB file and process them in account `updated_at` order. The snapshot captures only observed revisions; it cannot reconstruct versions that were never delivered. Deletion/tombstone and arbitrary retroactive movement recomputation are outside the current contract. Do not overwrite an existing published delivery to make a replay appear successful. See [incremental-processing boundaries](incremental-processing.md).

## Operational handoff to a real service

Before any paid environment, separately approve billing, tenant/workspace ownership, credentials and least-privilege access, data classification, source connection, reconciliation/refresh SLA, row-level access, capacity sizing and rollback. None is present in this repo. Stop if an unexpected cloud credential, connection, deploy action or chargeable service appears.
