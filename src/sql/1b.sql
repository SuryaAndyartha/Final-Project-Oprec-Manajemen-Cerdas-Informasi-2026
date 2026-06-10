SELECT
    multiIf(
        delivery_days <= 5, '0-5 Days',
        delivery_days <= 10, '6-10 Days',
        delivery_days <= 15, '11-15 Days',
        delivery_days <= 20, '16-20 Days',
        delivery_days <= 25, '21-25 Days',
        '>25 Days'
    ) AS `Delivery Time`,

    count(*) AS `Total Orders`

FROM 
(
    SELECT
        dateDiff('day', order_purchase_timestamp, order_delivered_customer_date) AS delivery_days
    FROM groceria.orders
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp IS NOT NULL
      AND order_delivered_customer_date IS NOT NULL
) AS subquery

GROUP BY `Delivery Time`

ORDER BY 
    multiIf(
        `Delivery Time` = '0-5 Days', 1,
        `Delivery Time` = '6-10 Days', 2,
        `Delivery Time` = '11-15 Days', 3,
        `Delivery Time` = '16-20 Days', 4,
        `Delivery Time` = '21-25 Days', 5,
        6
    ) ASC;
