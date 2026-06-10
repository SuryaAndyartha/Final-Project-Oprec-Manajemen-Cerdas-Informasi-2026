SELECT
    toStartOfMonth(order_purchase_timestamp) AS "Month",

    round(
        countIf(
            order_delivered_customer_date
            <= order_estimated_delivery_date
        )
        * 100.0
        / count(),
        2
    ) AS "On-Time Delivery Rate (%)"

FROM groceria.orders

WHERE order_status = 'delivered'
  AND order_purchase_timestamp >= '2017-01-01'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL

GROUP BY "Month"

ORDER BY "Month";
