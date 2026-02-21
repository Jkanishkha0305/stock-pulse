-- Chart 1: Inventory Level Timeline (one line per SKU, last 30 days)
-- Estimated stock at end of each day = current_stock + sales after that day - deliveries after that day
with date_spine as (
    select generate_series(
        (current_date - interval '30 days')::date,
        current_date,
        '1 day'::interval
    )::date as stock_date
),
sku_list as (
    select distinct sku from public.products
),
daily_stock as (
    select
        d.stock_date,
        s.sku,
        p.name,
        p.current_stock
            + coalesce(sales_after.sum_sold, 0)
            - coalesce(delivered_after.sum_delivered, 0) as estimated_stock
    from date_spine d
    cross join sku_list s
    join public.products p on p.sku = s.sku
    left join lateral (
        select sum(s2.units_sold) as sum_sold
        from public.sales s2
        where s2.sku = s.sku and s2.date > d.stock_date
    ) sales_after on true
    left join lateral (
        select sum(po.quantity_ordered) as sum_delivered
        from public.purchase_orders po
        where po.sku = s.sku
          and (
              (po.actual_arrival is not null and po.actual_arrival > d.stock_date)
              or (po.actual_arrival is null and po.predicted_arrival is not null and po.predicted_arrival > d.stock_date)
          )
    ) delivered_after on true
)
select
    stock_date,
    sku,
    name,
    greatest(0, round(estimated_stock::numeric, 0)) as stock_level
from daily_stock
order by stock_date, sku;
