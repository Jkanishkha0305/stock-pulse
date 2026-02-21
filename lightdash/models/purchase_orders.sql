select
    po_id,
    sku,
    supplier_id,
    quantity_ordered,
    ordered_at,
    predicted_arrival,
    actual_arrival,
    status,
    agent_reasoning,
    prediction_error,
    case
        when actual_arrival is not null and predicted_arrival is not null
        then (actual_arrival::date - predicted_arrival::date)
        else null
    end as arrival_delta_days,
    -- Chart 4: Lead time predicted vs actual (days from order to arrival)
    case
        when ordered_at is not null and predicted_arrival is not null
        then (predicted_arrival::date - (ordered_at::date))
        else null
    end as predicted_lead_days,
    case
        when ordered_at is not null and actual_arrival is not null
        then (actual_arrival::date - (ordered_at::date))
        else null
    end as actual_lead_days
from public.purchase_orders
