-- Chart 6: Stockouts avoided + value saved (single-number cards)
-- Replenishment orders this month = proxy for "stockouts avoided"; value = sum(quantity * unit_cost)
with po_this_month as (
    select
        po.sku,
        po.quantity_ordered,
        p.unit_cost
    from public.purchase_orders po
    left join public.products p on p.sku = po.sku
    where po.ordered_at >= date_trunc('month', current_date)
)
select
    count(*) as stockouts_avoided_this_month,
    round(coalesce(sum(quantity_ordered * coalesce(unit_cost, 0)), 0)::numeric, 2) as value_saved_gbp
from po_this_month;
