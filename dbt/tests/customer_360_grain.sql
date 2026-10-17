-- A customer mart must not drop or multiply current accounts.
select 1
where (select count(*) from {{ ref('mart_customer_360') }})
    <> (select count(*) from {{ ref('dim_account') }})
