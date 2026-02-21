-- Chart 5: Seasonal velocity patterns (velocity per SKU per month)
-- One line per SKU; Paracetamol spikes in Oct, Pumpkin Soup flat then spike in autumn
select
    date_trunc('month', date::date)::date as sale_month,
    sku,
    avg(velocity_7day_avg) as velocity_avg,
    sum(units_sold) as units_sold_total
from public.sales
group by date_trunc('month', date::date), sku
order by sale_month, sku;
