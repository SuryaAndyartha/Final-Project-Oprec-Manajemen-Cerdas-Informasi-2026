SELECT
    round(
        countIf(
            order_delivered_customer_date
            <= order_estimated_delivery_date
        )
        * 100.0
        / count(),
        2
    ) AS on_time_rate,

    round(
        countIf(
            order_delivered_customer_date
            > order_estimated_delivery_date
        )
        * 100.0
        / count(),
        2
    ) AS late_rate

FROM groceria.orders

WHERE order_status = 'delivered'
AND order_delivered_customer_date IS NOT NULL
AND order_estimated_delivery_date IS NOT NULL;
