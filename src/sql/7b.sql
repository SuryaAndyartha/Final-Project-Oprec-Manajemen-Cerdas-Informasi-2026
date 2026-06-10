SELECT
    CASE
        WHEN p.product_weight_g < 500 THEN '< 0.5 kg'
        WHEN p.product_weight_g < 1000 THEN '0.5 - 1 kg'
        WHEN p.product_weight_g < 5000 THEN '1 - 5 kg'
        ELSE '> 5 kg'
    END AS "Product Weight Category",

    round(
        avg(
            dateDiff(
                'hour',
                o.order_purchase_timestamp,
                o.order_delivered_customer_date
            ) / 24.0
        ),
        2
    ) AS "Average Delivery Time (Days)",

    count(*) AS "Total Items Sold"

FROM groceria.order_items oi

JOIN groceria.orders o
    ON oi.order_id = o.order_id

JOIN groceria.products p
    ON oi.product_id = p.product_id

WHERE o.order_status = 'delivered'

GROUP BY "Product Weight Category"

ORDER BY "Average Delivery Time (Days)" DESC;
