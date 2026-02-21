-- Map DB columns date -> sale_date, units_sold -> quantity_sold for schema consistency
select
    sale_id as id,
    sku,
    units_sold as quantity_sold,
    date as sale_date,
    velocity_7day_avg,
    date_trunc('week', date::date) as sale_week,
    date_trunc('month', date::date) as sale_month
from public.sales
