-- StockPulse Schema
-- Run this in the Supabase SQL Editor before running simulate.py

CREATE TABLE IF NOT EXISTS products (
    sku               VARCHAR PRIMARY KEY,
    name              VARCHAR NOT NULL,
    category          VARCHAR NOT NULL,
    current_stock     INTEGER NOT NULL,
    reorder_point     INTEGER NOT NULL,
    safety_stock      INTEGER NOT NULL,
    unit_cost         DECIMAL NOT NULL,
    shelf_life_days   INTEGER,
    daily_velocity    DECIMAL
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku               VARCHAR REFERENCES products(sku),
    date              DATE NOT NULL,
    units_sold        INTEGER NOT NULL,
    velocity_7day_avg DECIMAL NOT NULL
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id         VARCHAR PRIMARY KEY,
    name                VARCHAR NOT NULL,
    sku                 VARCHAR REFERENCES products(sku),
    predicted_lead_days INTEGER NOT NULL,
    actual_lead_days    DECIMAL NOT NULL,
    reliability_score   INTEGER NOT NULL,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku                VARCHAR REFERENCES products(sku),
    supplier_id        VARCHAR REFERENCES suppliers(supplier_id),
    quantity_ordered   INTEGER NOT NULL,
    ordered_at         TIMESTAMP NOT NULL,
    predicted_arrival  DATE,
    actual_arrival     DATE,
    status             VARCHAR NOT NULL DEFAULT 'pending',
    agent_reasoning    TEXT,
    stockout_days      INTEGER DEFAULT 0,
    waste_units        INTEGER DEFAULT 0,
    prediction_error   INTEGER DEFAULT 0
);
