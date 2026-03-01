-- 1. Seed the Main Dataset
-- This tells StreamForge that a dataset named 'retail_events' exists.
-- It maps to the 'raw' bucket in MinIO under the 'retail' folder.
INSERT INTO datasets (name, storage_location)
VALUES (
    'retail_events', 
    's3a://raw/retail/'
) ON CONFLICT (name) DO NOTHING;

-- 2. Seed Initial Features (SQL Logic)
-- These allow the UI to immediately show analytics once data starts flowing.

-- Feature: Total Revenue by Country
INSERT INTO features (name, dataset_id, sql_definition)
SELECT 
    'revenue_by_country', 
    id, 
    'SELECT country, SUM(price * quantity) as total_revenue FROM retail_events GROUP BY country ORDER BY total_revenue DESC'
FROM datasets WHERE name = 'retail_events';

-- Feature: Top 10 Customers by Spend
INSERT INTO features (name, dataset_id, sql_definition)
SELECT 
    'top_customers_spend', 
    id, 
    'SELECT customer_id, SUM(price * quantity) as total_spend FROM retail_events WHERE customer_id IS NOT NULL GROUP BY customer_id ORDER BY total_spend DESC LIMIT 10'
FROM datasets WHERE name = 'retail_events';

-- Feature: Daily Order Count
INSERT INTO features (name, dataset_id, sql_definition)
SELECT 
    'daily_order_volume', 
    id, 
    'SELECT date_trunc(''day'', invoice_date) as day, count(distinct invoice) as order_count FROM retail_events GROUP BY 1 ORDER BY 1 ASC'
FROM datasets WHERE name = 'retail_events';