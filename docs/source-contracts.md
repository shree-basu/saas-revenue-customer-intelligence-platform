# Source and staging contract

All data is synthetic. One immutable delivery is identified by `(business_date, batch_id)`. The version-2 manifest binds the exact nine relative CSV paths, column order, row counts and SHA-256 hashes. `_SUCCESS` indicates a completed generator write; it is not an external-service acknowledgement. A repeat generator call cannot overwrite an existing delivery. Tampering, missing/extra files, duplicates, orphan references, invalid domains/dates or invalid nonnegative numeric values abort local landing. Corrected data must arrive as a **new batch ID**, never by editing an existing batch.

| Source | Grain | Natural key |
| --- | --- | --- |
| accounts | Current CRM account in batch | `account_id` |
| subscriptions | Contract/version record | `subscription_id` |
| subscription_monthly_states | Subscription state at the first of each contiguous month | `subscription_id, state_month` |
| invoices | Invoice | `invoice_id` |
| product_usage_daily | Account/product/day | `account_id, product_id, usage_date` |
| support_cases | Ticket | `case_id` |
| sales_targets | Month/region/segment | `target_month, region, segment` |
| products | Product reference | `product_id` |
| plans | Plan reference | `plan_id` |

Every subscription has at least two contiguous monthly observations ending in the delivery business month. Its latest identity, frequency, quantity, contract value, currency and status must match `subscriptions`; an absent month, duplicate state or inconsistent current row fails landing. Historical rows in this feed are billing states, not account SCD2 history. The normal synthetic feed includes new, expansion, contraction, churn and flat examples.

This contract accepts **USD only**; cross-currency revenue calculations require an explicit FX policy later. Monetary fields require nonnegative values with at most two fractional digits; integer measures must be nonnegative integers. Domain/reference checks happen before landing; dbt repeats key relationship, uniqueness and accepted-value tests on raw/staging tables. Invalid deliveries remain on local disk for diagnosis, but there is no automatic quarantine table or cloud alert yet. Staging normalizes names/types; the intermediate model calculates subscription MRR, while health scores and revenue marts remain future work.

The `late-correction` and `account-correction` scenarios are valid **new immutable batches** for local replay/history tests. The loader atomically replaces raw tables only after contract validation and refuses an account revision older than the previously landed revision (or changed fields with an unchanged `updated_at`). An unrecognized added CSV column fails the versioned source contract; it is not silently ingested.
