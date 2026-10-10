# Source and staging contract

All Day-1/2 data is synthetic. One immutable delivery is identified by `(business_date, batch_id)`. The manifest binds the exact eight relative CSV paths, column order, row counts and SHA-256 hashes. `_SUCCESS` indicates a completed generator write; it is not an external-service acknowledgement. A repeat generator call cannot overwrite an existing delivery. Tampering, missing/extra files, duplicates, orphan references, invalid domains/dates or invalid nonnegative numeric values abort local landing. Corrected data must arrive as a **new batch ID**, never by editing an existing batch.

| Source | Grain | Natural key |
| --- | --- | --- |
| accounts | Current CRM account in batch | `account_id` |
| subscriptions | Contract/version record | `subscription_id` |
| invoices | Invoice | `invoice_id` |
| product_usage_daily | Account/product/day | `account_id, product_id, usage_date` |
| support_cases | Ticket | `case_id` |
| sales_targets | Month/region/segment | `target_month, region, segment` |
| products | Product reference | `product_id` |
| plans | Plan reference | `plan_id` |

This initial contract accepts **USD only**; cross-currency revenue calculations require an explicit FX policy later. Monetary fields require nonnegative values with at most two fractional digits; integer measures must be nonnegative integers. Domain/reference checks happen before landing; dbt repeats key relationship, uniqueness and accepted-value tests on raw/staging tables. Invalid deliveries remain on local disk for diagnosis, but there is no automatic quarantine table or cloud alert yet. Staging normalizes names/types only; it does not calculate MRR, churn or health scores.
