-- ============================================================
-- OLIST BUSINESS KPI LAYER
-- Only delivered/completed orders count toward revenue KPIs
-- unless explicitly stated otherwise (canceled/unavailable excluded).
-- ============================================================

-- 1. Total GMV (Gross Merchandise Value) and order volume, by status
SELECT
    order_status,
    COUNT(DISTINCT o.order_id) AS num_orders,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS gmv,
    ROUND(AVG(oi.price), 2) AS avg_item_price
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY order_status
ORDER BY gmv DESC;

-- 2. Delivery performance: % delivered late vs on-time (delivered orders only)
SELECT
    ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_late,
    ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date <= order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_on_time,
    COUNT(*) AS delivered_orders
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;

-- 3. Review score distribution and correlation with delivery lateness
SELECT
    CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 'Late' ELSE 'On-time' END AS delivery_status,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(*) AS num_orders
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY delivery_status;

-- 4. Seller concentration: revenue share of top 10% sellers (platform dependency risk)
WITH seller_rev AS (
    SELECT seller_id, SUM(price) AS revenue
    FROM order_items
    GROUP BY seller_id
),
ranked AS (
    SELECT *, NTILE(10) OVER (ORDER BY revenue DESC) AS decile
    FROM seller_rev
)
SELECT
    decile,
    COUNT(*) AS num_sellers,
    ROUND(SUM(revenue), 2) AS decile_revenue,
    ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM seller_rev), 2) AS pct_of_total_revenue
FROM ranked
GROUP BY decile
ORDER BY decile;

-- 5. Top product categories by revenue (English names)
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    COUNT(DISTINCT oi.order_id) AS num_orders,
    ROUND(SUM(oi.price), 2) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name
GROUP BY category
ORDER BY revenue DESC
LIMIT 10;

-- 6. Monthly GMV trend (growth trajectory)
SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS month,
    COUNT(DISTINCT o.order_id) AS num_orders,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS gmv
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY month
ORDER BY month;
