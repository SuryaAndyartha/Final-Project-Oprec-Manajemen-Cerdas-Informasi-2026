WITH delivery_data AS
(
    SELECT
        CASE
            WHEN order_delivered_customer_date <= order_estimated_delivery_date
                THEN 'On Time'
            ELSE 'Late'
        END AS delivery_status,

        dateDiff('hour', order_purchase_timestamp, order_approved_at) / 24.0 AS payment_days,
        dateDiff('hour', order_approved_at, order_delivered_carrier_date) / 24.0 AS seller_days,
        dateDiff('hour', order_delivered_carrier_date, order_delivered_customer_date) / 24.0 AS logistics_days

    FROM groceria.orders
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp IS NOT NULL
      AND order_approved_at IS NOT NULL
      AND order_delivered_carrier_date IS NOT NULL
      AND order_delivered_customer_date IS NOT NULL
)

SELECT
    'Payment Approval' AS stage,
    round(avgIf(payment_days, delivery_status = 'On Time'), 2) AS "On-Time Days",
    round(avgIf(payment_days, delivery_status = 'Late'), 2) AS "Late Days"
FROM delivery_data

UNION ALL

SELECT
    'Seller Processing',
    round(avgIf(seller_days, delivery_status = 'On Time'), 2),
    round(avgIf(seller_days, delivery_status = 'Late'), 2)
FROM delivery_data

UNION ALL

SELECT
    'Delivery to Customer',
    round(avgIf(logistics_days, delivery_status = 'On Time'), 2),
    round(avgIf(logistics_days, delivery_status = 'Late'), 2)
FROM delivery_data;
