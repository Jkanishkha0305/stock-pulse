-- Uses latest velocity from sales when products.daily_velocity is missing
with p as (
    select * from public.products
),
velocity as (
    select distinct on (sku)
        sku,
        velocity_7day_avg as daily_velocity
    from public.sales
    order by sku, date desc
)
select
    p.sku,
    p.name,
    p.category,
    p.current_stock,
    p.reorder_point,
    p.safety_stock,
    p.unit_cost,
    p.shelf_life_days,
    coalesce(v.daily_velocity, 0) as daily_velocity,
    case
        when coalesce(v.daily_velocity, 0) <= 0 then 'OK'
        when p.current_stock::float / nullif(v.daily_velocity, 0) <= 2  then 'CRITICAL'
        when p.current_stock::float / nullif(v.daily_velocity, 0) <= 7  then 'LOW'
        else 'OK'
    end as stock_status,
    round((p.current_stock::float / nullif(coalesce(v.daily_velocity, 0), 0))::numeric, 1) as days_remaining,
    case
        when coalesce(v.daily_velocity, 0) <= 0 then 'Green'
        when p.current_stock::float / nullif(v.daily_velocity, 0) >= 14 then 'Green'
        when p.current_stock::float / nullif(v.daily_velocity, 0) >= 7  then 'Amber'
        else 'Red'
    end as days_remaining_status
from p
left join velocity v on v.sku = p.sku
