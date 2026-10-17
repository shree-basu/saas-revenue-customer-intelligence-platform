select
    trim(invoice_id) as invoice_id,
    trim(account_id) as account_id,
    trim(subscription_id) as subscription_id,
    try_cast(invoice_date as date) as invoice_date,
    try_cast(due_date as date) as due_date,
    try_cast(amount as decimal(18, 2)) as amount,
    upper(trim(currency)) as currency,
    upper(trim(payment_status)) as payment_status,
    try_cast(nullif(trim(paid_date), '') as date) as paid_date,
    try_cast(updated_at as timestamp) as updated_at
from {{ source('raw', 'invoices') }}
