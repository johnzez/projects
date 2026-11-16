
SELECT
    d.year,
    d.month,
    d.month_name,

    COUNT(DISTINCT f.order_id) AS total_orders,

    COUNT(*) AS total_items_sold,

    ROUND(SUM(f.price), 2) AS product_sales,

    ROUND(SUM(f.freight_value), 2) AS total_freight,

    ROUND(
        SUM(f.price) / COUNT(DISTINCT f.order_id),
        2
    ) AS avg_product_sales_per_order

FROM fact_order_items f

INNER JOIN dim_date d
    ON f.purchase_date_key = d.date_key

WHERE f.order_status = 'delivered'

GROUP BY
    d.year,
    d.month,
    d.month_name

ORDER BY
    d.year,
    d.month;
