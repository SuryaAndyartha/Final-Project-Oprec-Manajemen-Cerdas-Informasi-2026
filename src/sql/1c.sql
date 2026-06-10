SELECT
    count() AS total_orders,

    countIf(
        order_delivered_customer_date
        <= order_estimated_delivery_date
    ) AS on_time_orders,

    countIf(
        order_delivered_customer_date
        > order_estimated_delivery_date
    ) AS late_orders

FROM groceria.orders

WHERE order_status = 'delivered'
AND order_delivered_customer_date IS NOT NULL
AND order_estimated_delivery_date IS NOT NULL;
