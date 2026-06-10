SELECT
    c.customer_state AS "Customer State",

    count() AS "Total Delivered Orders",

    countIf(
        o.order_delivered_customer_date >
        o.order_estimated_delivery_date
    ) AS "Late Deliveries",

    round(
        100.0 *
        countIf(
            o.order_delivered_customer_date >
            o.order_estimated_delivery_date
        ) / count(),
        2
    ) AS "Late Delivery Rate (%)"

FROM groceria.orders o

JOIN groceria.customers c
    ON o.customer_id = c.customer_id

WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL

GROUP BY c.customer_state

HAVING count() >= 100

ORDER BY "Late Delivery Rate (%)" DESC;
