-- One current account per reporting date. Rules are explanatory, not predictive.
with as_of_date as (
    select max(usage_date) as reporting_date
    from {{ ref('fct_product_usage_daily') }}
), latest_month as (
    select max(state_month) as state_month
    from {{ ref('int_subscription_monthly_mrr') }}
), recurring as (
    select s.account_id, sum(s.mrr_usd) as current_mrr_usd,
        sum(case when s.mrr_usd > 0 then 1 else 0 end) as active_subscriptions
    from {{ ref('int_subscription_monthly_mrr') }} as s
    cross join latest_month as lm
    where s.state_month = lm.state_month
    group by s.account_id
), usage_rollup as (
    select u.account_id, sum(u.active_users) as active_users,
        sum(u.licensed_users) as licensed_users,
        sum(u.api_calls) as api_calls,
        sum(u.failed_requests) as failed_requests
    from {{ ref('fct_product_usage_daily') }} as u
    cross join as_of_date as d
    where u.usage_date = d.reporting_date
    group by u.account_id
), invoice_rollup as (
    select i.account_id,
        sum(case when i.payment_status <> 'PAID' and i.due_date < d.reporting_date
            then 1 else 0 end) as overdue_invoice_count,
        sum(case when i.payment_status <> 'PAID' and i.due_date < d.reporting_date
            then i.amount else 0 end) as overdue_amount_usd
    from {{ ref('fct_invoices') }} as i
    cross join as_of_date as d
    group by i.account_id
), support_rollup as (
    select s.account_id,
        sum(case when s.status <> 'CLOSED' then 1 else 0 end) as open_case_count,
        sum(case when s.status <> 'CLOSED' and s.severity in ('HIGH', 'CRITICAL')
            then 1 else 0 end) as open_high_severity_count
    from {{ ref('fct_support_cases') }} as s
    group by s.account_id
), joined as (
    select d.reporting_date, a.account_id, a.account_key, a.account_name,
        a.region, a.segment, a.account_status,
        coalesce(r.current_mrr_usd, 0) as current_mrr_usd,
        coalesce(r.active_subscriptions, 0) as active_subscriptions,
        coalesce(u.active_users, 0) as active_users,
        coalesce(u.licensed_users, 0) as licensed_users,
        coalesce(u.api_calls, 0) as api_calls,
        coalesce(u.failed_requests, 0) as failed_requests,
        coalesce(i.overdue_invoice_count, 0) as overdue_invoice_count,
        coalesce(i.overdue_amount_usd, 0) as overdue_amount_usd,
        coalesce(s.open_case_count, 0) as open_case_count,
        coalesce(s.open_high_severity_count, 0) as open_high_severity_count,
        case when coalesce(u.licensed_users, 0) > 0
            then cast(u.active_users as decimal(18, 4)) / u.licensed_users
        end as license_utilization
    from {{ ref('dim_account') }} as a
    cross join as_of_date as d
    left join recurring as r on a.account_id = r.account_id
    left join usage_rollup as u on a.account_id = u.account_id
    left join invoice_rollup as i on a.account_id = i.account_id
    left join support_rollup as s on a.account_id = s.account_id
)
select *,
    case
        when current_mrr_usd = 0 then 'NO_ACTIVE_SUBSCRIPTION'
        when licensed_users = 0 then 'INSUFFICIENT_USAGE_DATA'
        when overdue_invoice_count > 0 or open_high_severity_count > 0
            or license_utilization < 0.5 then 'AT_RISK'
        else 'HEALTHY'
    end as health_status
from joined
