
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,

    COUNT(DISTINCT f.order_id) AS total_orders,

    COUNT(*) AS items_sold,

    ROUND(SUM(f.price), 2) AS product_sales,

    ROUND(SUM(f.freight_value), 2) AS freight_value

FROM fact_order_items f

INNER JOIN dim_sellers s
    ON f.seller_id = s.seller_id

WHERE f.order_status = 'delivered'

GROUP BY
    s.seller_id,
    s.seller_city,
    s.seller_state

ORDER BY
    product_sales DESC


