# Snowflake production target — static design only

No file in this directory is invoked by CI, Python, dbt local, or a GitHub workflow. The SQL uses fictional `SAAS_EXAMPLE_*` identifiers. It is design material for future security/cost review, not an install script, and has never been submitted to Snowflake.

`00_cost_guardrails.sql` describes a suspended X-Small transformation warehouse and an example resource monitor. If an operator later executes it in a real account, creating/using cloud resources can incur charges; a resource monitor is not a zero-cost guarantee. `01_governed_database_and_roles.sql` separates raw-read/dbt-transform rights from certified-mart-only Fabric consumption. `02_session_observability.sql` shows query tags and a session timeout. An operator would need to supply real accounts, owners, ingestion grants, and explicit approval; this repository supplies none.

Local CI checks for known unsafe defaults and file presence. It does not prove Snowflake SQL execution, permissions, cost behaviour, or adapter compatibility. See [design notes](../docs/snowflake-design.md).
