-- One invoice per invoice_id. LEFT JOINs expose missing dimensions to tests.
{{ config(materialized='incremental', unique_key='invoice_id', incremental_strategy='merge', on_schema_change='fail') }}
select
    md5(i.invoice_id) as invoice_key,
    i.invoice_id,
    i.subscription_id,
    i.account_id,
    a.account_key,
    d.date_key as invoice_date_key,
    i.invoice_date,
    i.due_date,
    i.paid_date,
    i.amount,
    i.currency,
    i.payment_status,
    i.updated_at
from {{ ref('stg_invoices') }} as i
left join {{ ref('dim_account') }} as a on i.account_id = a.account_id
left join {{ ref('dim_date') }} as d on i.invoice_date = d.calendar_date
