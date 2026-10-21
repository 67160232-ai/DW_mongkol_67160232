-- Coast Café: SQL submission Parts A-C
-- Data source: supplied synthetic CSV files.
-- Run .read 00_setup.sql before executing this file.

-- A1 SELECT / LIMIT
SELECT order_id, order_date, quantity, channel FROM orders LIMIT 10;

-- A2 WHERE / ORDER BY
SELECT order_id, order_date, customer_id, product_id, quantity, channel, status
FROM orders WHERE status='Completed' AND channel='ออนไลน์'
ORDER BY order_date DESC, order_id DESC LIMIT 10;

-- A3 GROUP BY / COUNT
SELECT category, COUNT(*) AS product_count
FROM products GROUP BY category ORDER BY product_count DESC, category;

-- A4 INNER JOIN
SELECT o.order_id, p.product_name, o.quantity, o.unit_price
FROM orders o INNER JOIN products p ON o.product_id=p.product_id
ORDER BY o.order_id;

-- A5 JOIN + SUM: net sales by province
SELECT c.province, ROUND(SUM(f.net_sales),2) AS total_sales
FROM fact_sales f INNER JOIN customers c ON f.customer_id=c.customer_id
GROUP BY c.province ORDER BY total_sales DESC;

-- A6 Aggregation: net sales by category
SELECT p.category, ROUND(SUM(f.net_sales),2) AS total_sales
FROM fact_sales f INNER JOIN products p ON f.product_id=p.product_id
GROUP BY p.category ORDER BY total_sales DESC;

-- A7 TOP-N: top five customers by net spend
SELECT c.customer_id,c.customer_name,ROUND(SUM(f.net_sales),2) AS total_spent
FROM fact_sales f INNER JOIN customers c ON f.customer_id=c.customer_id
GROUP BY c.customer_id,c.customer_name
ORDER BY total_spent DESC,c.customer_id LIMIT 5;

-- A8 HAVING: products with net sales above 2,000 baht
SELECT p.product_id,p.product_name,ROUND(SUM(f.net_sales),2) AS total_sales
FROM fact_sales f INNER JOIN products p ON f.product_id=p.product_id
GROUP BY p.product_id,p.product_name
HAVING SUM(f.net_sales)>2000 ORDER BY total_sales DESC;

-- B1 Star Schema: fact_sales is the central fact; source dimensions join by these keys:
-- customer: fact_sales.customer_id = customers.customer_id
-- product:  fact_sales.product_id = products.product_id
-- date dimension (proposed): fact_sales.order_date = dim_date.calendar_date
-- channel dimension (proposed): fact_sales.channel = dim_channel.channel_name
-- B1 note: dim_date and dim_channel are conceptual; create physical dimensions for a production star schema.

-- B2 Monthly sales Data Mart
CREATE OR REPLACE VIEW mart_monthly_sales AS
SELECT DATE_TRUNC('month', f.order_date)::DATE AS sales_month,
       p.category, f.channel, COUNT(*) AS order_lines,
       ROUND(SUM(f.net_sales),2) AS total_sales
FROM fact_sales f JOIN products p ON f.product_id=p.product_id
GROUP BY 1,2,3;
SELECT * FROM mart_monthly_sales ORDER BY sales_month, category, channel;

-- B3 Data Quality checks
SELECT COUNT(*) AS missing_customer_id
FROM orders WHERE customer_id IS NULL OR TRIM(customer_id)='';
SELECT COUNT(*) AS invalid_quantity
FROM orders WHERE TRY_CAST(quantity AS INTEGER) IS NULL OR TRY_CAST(quantity AS INTEGER)<=0;
SELECT COUNT(*) AS unknown_product_id
FROM orders o LEFT JOIN products p ON o.product_id=p.product_id
WHERE p.product_id IS NULL;

-- C1 Daily time series and 7-row moving average (rows are not necessarily calendar days)
WITH daily_sales AS (
  SELECT order_date, ROUND(SUM(net_sales),2) AS daily_sales
  FROM fact_sales GROUP BY order_date
)
SELECT order_date, daily_sales,
       ROUND(AVG(daily_sales) OVER (
         ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ),2) AS ma_7_rows
FROM daily_sales ORDER BY order_date;

-- C2 Customer features for segmentation
SELECT c.customer_id,
       MAX(f.order_date) AS last_order,
       COUNT(DISTINCT f.order_id) AS frequency,
       ROUND(SUM(f.net_sales),2) AS monetary
FROM customers c LEFT JOIN fact_sales f ON c.customer_id=f.customer_id
GROUP BY c.customer_id ORDER BY monetary DESC NULLS LAST;
