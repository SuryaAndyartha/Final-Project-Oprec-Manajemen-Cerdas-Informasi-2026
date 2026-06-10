SELECT
    c.customer_state AS "Customer State",

    round(
        avg(
            dateDiff(
                'hour',
                o.order_purchase_timestamp,
                o.order_delivered_customer_date
            )
        ) / 24,
        2
    ) AS "Average Delivery Time (Days)",

    round(avg(op.freight_value), 2) AS "Average Freight Cost",

    count() AS "Total Orders"

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

ORDER BY "Average Delivery Time (Days)" DESC;
