-- ============================================================
-- StockPulse — Run this in Supabase > SQL Editor
-- products, sales, suppliers, purchase_orders already exist.
-- Only need to create agent_cycles.
-- ============================================================

create table if not exists agent_cycles (
  id            bigserial primary key,
  cycle_index   integer not null,
  accuracy      numeric(5,1) not null,
  timestamp     timestamptz not null default now(),
  signals       jsonb,
  orders_placed integer default 0
);

alter table agent_cycles disable row level security;

-- Seed 6 historical cycles for the learning chart
insert into agent_cycles (cycle_index, accuracy, timestamp, orders_placed) values
  (1, 55, '2025-08-15T10:00:00Z', 2),
  (2, 58, '2025-09-20T10:00:00Z', 2),
  (3, 63, '2025-10-25T10:00:00Z', 2),
  (4, 71, '2025-11-28T10:00:00Z', 2),
  (5, 82, '2025-12-20T10:00:00Z', 2),
  (6, 88, '2026-01-30T10:00:00Z', 2)
on conflict do nothing;
