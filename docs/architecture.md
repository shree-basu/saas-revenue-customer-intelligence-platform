# Architecture decision: Snowflake + dbt + Fabric

The fictional company already uses Snowflake as its warehouse and Microsoft tools for planning and executive reporting. Snowflake holds governed raw and certified analytical data; dbt is the single owner of transformation and metric datasets; Fabric Data Factory provides the Microsoft-side planning integration; selected certified marts are the only proposed mirroring boundary into OneLake and Power BI. This avoids duplicate SQL/DAX logic and raw-data sprawl in Fabric.

The local system substitutes immutable CSV batches, DuckDB and a dbt local target. It tests contract and transformation logic but does not prove Snowflake SQL performance, Fabric item validity, cloud IAM, capacity costs or deployed behaviour. No cloud profile is operational.

Source grains: one account current record; one subscription contract/version; one invoice; one account/product/day usage row; one support case; one month/region/segment sales target. Later models must document their own grains and reconciliation definitions before implementation.
