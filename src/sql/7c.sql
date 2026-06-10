SELECT
    ct.product_category_name_english AS "Product Category",

    count(*) AS "Total Items Sold",

    countIf(
        o.order_delivered_customer_date >
        o.order_estimated_delivery_date
    ) AS "Late Deliveries",

    round(
        100.0 *
        countIf(
            o.order_delivered_customer_date >
            o.order_estimated_delivery_date
        )
        / count(*),
        2
    ) AS "Late Delivery Rate (%)"

FROM groceria.order_items oi

JOIN groceria.orders o
    ON oi.order_id = o.order_id

JOIN groceria.products p
    ON oi.product_id = p.product_id

LEFT JOIN groceria.category_translation ct
    ON p.product_category_name = ct.product_category_name

WHERE o.order_status = 'delivered'

GROUP BY ct.product_category_name_english

HAVING count(*) >= 100

ORDER BY "Late Delivery Rate (%)" DESC

LIMIT 10;
