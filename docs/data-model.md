# Dimensional core contract

`dim_account` is **one current row per account_id** from the validated CRM batch. Its deterministic MD5 key is a stable identifier for the natural key, not an SCD2 version key. `snap_account_history` separately records observed CRM account versions with `dbt_valid_from`/`dbt_valid_to`. It is not joined into the current facts, so historical as-of account classification remains unsupported. `dim_product` is one row per product_id with the same key policy. `dim_date` is one row per **observed** non-null business date; it is a sparse calendar and must not be used to infer that absent dates were processed. Its integer key is YYYYMMDD.

Day 3 facts join these current dimensions. Thus their account attributes are **current-state classifications**, not as-of-event historical attributes. The Day-5 account snapshot supplies separate validity intervals, but as-of joins are still future work. Do not present current-state joins as historical SCD2 analytics.

| Fact | Grain | Natural key | Important boundary |
| --- | --- | --- | --- |
| `fct_invoices` | One billing invoice | `invoice_id` | Amount is USD billed, not MRR or recognized revenue; invoice account must match subscription account. |
| `fct_product_usage_daily` | Account/product/usage date | `(account_id, product_id, usage_date)` | Measures are observed daily counts, not monthly sums. |
| `fct_support_cases` | One support case | `case_id` | Open cases have null closed date and resolution minutes. |
| `fct_subscription_movements` | One subscription/observed month after its first baseline month | `(subscription_id, state_month)` | Signed operational USD MRR change, not invoice revenue; source is validated monthly billing state. |

Fact keys derive deterministically from validated natural keys. Dimension/date joins are left joins so missing references stay visible and fail dbt not-null/relationship checks. Fact-to-staging row counts are reconciled, and invoice/subscription account consistency is tested. Invoice, usage and support facts now use merge-based incremental upserts over every row in the latest validated delivery; the current-state dimensions and movement fact remain full-refresh tables. Historical as-of classification is not yet implemented.
