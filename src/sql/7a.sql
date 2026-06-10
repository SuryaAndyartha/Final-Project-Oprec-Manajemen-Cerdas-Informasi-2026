SELECT
    ct.product_category_name_english AS "Product Category",

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

LEFT JOIN groceria.category_translation ct
    ON p.product_category_name = ct.product_category_name

WHERE o.order_status = 'delivered'

GROUP BY ct.product_category_name_english

HAVING count(*) >= 100

ORDER BY "Average Delivery Time (Days)" DESC

LIMIT 10;
