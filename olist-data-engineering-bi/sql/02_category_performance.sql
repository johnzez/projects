
SELECT
    p.product_category_english AS product_category,

    COUNT(DISTINCT f.order_id) AS total_orders,

    COUNT(*) AS items_sold,

    ROUND(SUM(f.price), 2) AS product_sales,

    ROUND(AVG(f.price), 2) AS avg_item_price

FROM fact_order_items f

INNER JOIN dim_products p
    ON f.product_id = p.product_id

WHERE f.order_status = 'delivered'

GROUP BY
    p.product_category_english

ORDER BY
    product_sales DESC


