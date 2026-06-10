SELECT
    round(
        avg(
            dateDiff(
                'day',
                order_delivered_customer_date,
                order_estimated_delivery_date
            )
        ),
        2
    ) AS avg_days_early
FROM groceria.orders
WHERE order_status = 'delivered';

