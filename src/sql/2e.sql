SELECT
    round(
        avg(
            dateDiff(
                'day',
                order_purchase_timestamp,
                order_estimated_delivery_date
            )
        ),
        2
    ) AS avg_estimated_days,

    round(
        avg(
            dateDiff(
                'day',
                order_purchase_timestamp,
                order_delivered_customer_date
            )
        ),
        2
    ) AS avg_actual_days
FROM groceria.orders
WHERE order_status = 'delivered';
