SELECT
    c.customer_state AS "Customer State",

    count() AS "Total Orders",

    round(
        100.0 *
        avg(
            o.order_delivered_customer_date >
            o.order_estimated_delivery_date
        ),
        2
    ) AS "Late Delivery Rate (%)",

    round(avg(op.freight_value), 2) AS "Average Freight Cost"

FROM groceria.orders o

JOIN groceria.order_items op
    ON o.order_id = op.order_id

JOIN groceria.customers c
    ON o.customer_id = c.customer_id

WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
  AND o.order_delivered_customer_date IS NOT NULL
  AND op.freight_value IS NOT NULL

GROUP BY c.customer_state

ORDER BY "Late Delivery Rate (%)" DESC;
