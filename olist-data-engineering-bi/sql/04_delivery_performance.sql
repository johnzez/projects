
SELECT

    COUNT(*) AS delivered_orders,

    COUNT(delivery_days) AS orders_with_delivery_dates,

    ROUND(
        AVG(delivery_days),
        2
    ) AS avg_delivery_days,

    SUM(
        CASE
            WHEN delivered_late = TRUE THEN 1
            ELSE 0
        END
    ) AS late_deliveries,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN delivered_late = TRUE THEN 1
                ELSE 0
            END
        ) / NULLIF(COUNT(delivered_late), 0),
        2
    ) AS late_delivery_percentage

FROM fact_orders

WHERE order_status = 'delivered';
