-- STATIC REFERENCE ONLY. Do not execute. No Snowflake account is configured here.
-- An authorized future ACCOUNTADMIN would first review the credit quota and policies.
CREATE RESOURCE MONITOR IF NOT EXISTS SAAS_EXAMPLE_MONITOR WITH
    CREDIT_QUOTA = 10
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS ON 80 PERCENT DO NOTIFY
             ON 100 PERCENT DO SUSPEND_IMMEDIATE;

-- An authorized future administrator would create a dedicated transformation warehouse.
-- These settings reduce accidental use but cannot guarantee zero spend if executed.
CREATE WAREHOUSE IF NOT EXISTS SAAS_EXAMPLE_TRANSFORM_WH WITH
    WAREHOUSE_SIZE = XSMALL
    AUTO_SUSPEND = 60
    AUTO_RESUME = FALSE
    INITIALLY_SUSPENDED = TRUE
    RESOURCE_MONITOR = SAAS_EXAMPLE_MONITOR
    STATEMENT_TIMEOUT_IN_SECONDS = 900;
