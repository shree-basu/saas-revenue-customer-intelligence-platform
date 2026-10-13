# Current customer and renewal marts

`mart_customer_360` has one row per current account at the latest observed usage date. It combines account-level MRR from the latest subscription month with usage on that date, overdue invoices, and open support cases. Each source is aggregated to account grain before joining, preventing invoice/usage/case fan-out. Accounts with no observations remain visible.

Health is a transparent triage rule, **not** a trained risk score: no active MRR, missing licensed-user evidence, overdue invoices/high-severity open cases/under-50% license utilization, then healthy, in that precedence order. Open low-severity cases alone do not imply risk. The reporting date is data-derived; no wall-clock dependence.

`mart_renewal_pipeline` has one active subscription per row, due from the reporting date through 90 days later (inclusive). Its annualized current MRR is *renewal ARR at risk*, not recognized or booked revenue. Cancelled subscriptions and zero-MRR records are excluded. The synthetic batch contains both near-term and later renewals so these conditions can be exercised locally. Historical as-of customer attributes and real CRM forecasting are outside this reference scope.
