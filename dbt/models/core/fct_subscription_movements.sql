-- One subscription/observed month after its first baseline month.
with ordered as (
    select
        subscription_id,
        account_id,
        product_id,
        state_month,
        mrr_usd,
        lag(mrr_usd) over (
            partition by subscription_id order by state_month
        ) as prior_mrr_usd
    from {{ ref('int_subscription_monthly_mrr') }}
), classified as (
    select
        *,
        case
            when prior_mrr_usd = 0 and mrr_usd > 0 then 'NEW'
            when prior_mrr_usd > 0 and mrr_usd = 0 then 'CHURN'
            when mrr_usd > prior_mrr_usd then 'EXPANSION'
            when mrr_usd < prior_mrr_usd then 'CONTRACTION'
            else 'FLAT'
        end as movement_type
    from ordered
    where prior_mrr_usd is not null
)
select
    md5(c.subscription_id || '|' || cast(c.state_month as varchar)) as movement_key,
    c.subscription_id,
    c.account_id,
    a.account_key,
    c.product_id,
    p.product_key,
    c.state_month,
    d.date_key as state_month_key,
    c.prior_mrr_usd,
    c.mrr_usd as ending_mrr_usd,
    c.movement_type,
    cast(
        case
            when c.movement_type = 'NEW' then c.mrr_usd
            when c.movement_type = 'CHURN' then -c.prior_mrr_usd
            when c.movement_type in ('EXPANSION', 'CONTRACTION') then c.mrr_usd - c.prior_mrr_usd
            else 0
        end as decimal(18, 2)
    ) as movement_mrr_usd
from classified as c
left join {{ ref('dim_account') }} as a on c.account_id = a.account_id
left join {{ ref('dim_product') }} as p on c.product_id = p.product_id
left join {{ ref('dim_date') }} as d on c.state_month = d.calendar_date
