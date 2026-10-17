# Snowflake target design and evidence limit

Snowflake is the proposed governed warehouse; dbt will own transformation from RAW through STAGING and CORE to certified MARTS. The static examples use one X-Small transformation warehouse with `AUTO_RESUME=FALSE`, `INITIALLY_SUSPENDED=TRUE`, a 60-second auto-suspend, a 900-second statement timeout and an assigned resource monitor. In a real enterprise, ingestion and BI workloads should be isolated with separately approved warehouses and monitors; none are created here.

The resource monitor has an illustrative 10-credit monthly quota, warning at 80% and immediate suspension at 100%. These controls limit risk **after deployment**; they do not eliminate credit consumption or guarantee a hard currency cap. Snowflake notes that resource monitors require assignment to a warehouse and that creating one requires ACCOUNTADMIN. A real deployment would require role, ownership, managed-access and budget review.

The illustrative dbt role can read RAW and create models in STAGING/CORE/MARTS. The illustrative Fabric reader can read MARTS tables/views only. Future grants address newly created objects; managed-access schema grants must be administered by the owner or a role with grant authority. No user, service principal, network integration, secret or external connection is provisioned.

Query tags support future attribution; they are not monitoring evidence here. Model-level Snowflake performance, micro-partition pruning, clustering, warehouse sizing and actual cost remain unmeasured.

The SQL syntax was based on current official Snowflake references for [warehouses](https://docs.snowflake.com/en/sql-reference/sql/create-warehouse), [resource monitors](https://docs.snowflake.com/en/sql-reference/sql/create-resource-monitor), [access control](https://docs.snowflake.com/en/user-guide/security-access-control-configure), and [session settings](https://docs.snowflake.com/en/sql-reference/sql/alter-session). Only local structural checks run; authenticated parsing or execution has not happened.
