-- Run this in Supabase SQL Editor if tables do not exist yet.
-- Adjust types as needed for your project.

create table if not exists products (
  sku text primary key,
  name text not null,
  category text,
  current_stock int default 0,
  reorder_point int default 0,
  safety_stock int default 0,
  unit_cost numeric default 0,
  shelf_life_days int default 0
);

create table if not exists sales (
  sale_id uuid primary key default gen_random_uuid(),
  sku text references products(sku),
  date date not null,
  units_sold int default 0,
  velocity_7day_avg numeric default 0
);

create table if not exists suppliers (
  supplier_id text primary key,
  name text not null,
  sku text,
  predicted_lead_days int default 7,
  actual_lead_days int default 7,
  reliability_score int default 0,
  notes text
);

create table if not exists purchase_orders (
  po_id text primary key,
  sku text,
  supplier_id text,
  quantity_ordered int default 0,
  ordered_at timestamptz,
  predicted_arrival date,
  actual_arrival date,
  status text default 'pending',
  agent_reasoning text,
  prediction_error int
);

create table if not exists agent_cycles (
  id uuid primary key default gen_random_uuid(),
  cycle_index int not null,
  accuracy numeric default 0,
  timestamp timestamptz default now()
);

-- Optional: seed 5 products
insert into products (sku, name, category, current_stock, reorder_point, safety_stock, unit_cost, shelf_life_days)
values
  ('SKU-001', 'Fresh Whole Milk', 'Dairy', 420, 300, 150, 0.85, 7),
  ('SKU-002', 'Heinz Baked Beans', 'Grocery', 240, 200, 80, 1.20, 365),
  ('SKU-003', 'Paracetamol 500mg', 'Pharmacy', 85, 100, 50, 0.35, 730),
  ('SKU-004', 'Pumpkin Soup', 'Grocery', 45, 80, 40, 2.10, 365),
  ('SKU-005', 'Energy Drinks', 'Beverages', 280, 200, 60, 1.50, 180)
on conflict (sku) do nothing;
