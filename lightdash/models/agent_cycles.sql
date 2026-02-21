select
    id,
    cycle_index,
    accuracy,
    timestamp,
    orders_placed,
    signals,
    signals -> 'weather' ->> 'temperature_c' as temperature_c,
    signals -> 'season' ->> 'season'          as season_name,
    signals -> 'season' ->> 'flu_season'       as flu_season
from public.agent_cycles
