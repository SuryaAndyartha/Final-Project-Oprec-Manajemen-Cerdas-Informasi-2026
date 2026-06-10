SELECT
    toStartOfMonth(order_purchase_timestamp) AS "Month",

    round(
        avg(
            dateDiff(
                'day',
                order_purchase_timestamp,
                order_delivered_customer_date
            )
        ),
        2
    ) AS "Average Delivery Time (Days)"

FROM groceria.orders

WHERE order_status = 'delivered'
  AND order_purchase_timestamp IS NOT NULL
  AND order_delivered_customer_date IS NOT NULL

GROUP BY "Month"

ORDER BY "Month";

