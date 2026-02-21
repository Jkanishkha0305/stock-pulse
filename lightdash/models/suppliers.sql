select
    supplier_id as id,
    name,
    sku,
    predicted_lead_days,
    actual_lead_days,
    reliability_score,
    notes
from public.suppliers
