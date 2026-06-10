SELECT
    oi.seller_id AS "Seller ID",

    count(DISTINCT o.order_id) AS "Total Delivered Orders",

    count(
        DISTINCT CASE
            WHEN o.order_delivered_customer_date >
                 o.order_estimated_delivery_date
            THEN o.order_id
        END
    ) AS "Late Deliveries",

    round(
        100.0 *
        count(
            DISTINCT CASE
                WHEN o.order_delivered_customer_date >
                     o.order_estimated_delivery_date
                THEN o.order_id
            END
        )
        / count(DISTINCT o.order_id),
        2
    ) AS "Late Delivery Rate (%)"

FROM groceria.order_items oi

JOIN groceria.orders o
    ON oi.order_id = o.order_id

WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL

GROUP BY oi.seller_id

HAVING count(DISTINCT o.order_id) >= 100

ORDER BY "Late Delivery Rate (%)" DESC

LIMIT 20;
