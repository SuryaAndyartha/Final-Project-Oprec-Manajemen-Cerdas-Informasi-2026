SELECT
    1 AS sort_order,
    'Payment Approval' AS stage,
    round(
        avg(dateDiff('hour',
            order_purchase_timestamp,
            order_approved_at
        )) / 24,
        2
    ) AS avg_days
FROM groceria.orders
WHERE order_status = 'delivered'
  AND order_purchase_timestamp IS NOT NULL
  AND order_approved_at IS NOT NULL

UNION ALL

SELECT
    2 AS sort_order,
    'Seller Processing' AS stage,
    round(
        avg(dateDiff('hour',
            order_approved_at,
            order_delivered_carrier_date
        )) / 24,
        2
    ) AS avg_days
FROM groceria.orders
WHERE order_status = 'delivered'
  AND order_approved_at IS NOT NULL
  AND order_delivered_carrier_date IS NOT NULL

UNION ALL

SELECT
    3 AS sort_order,
    'Delivery to Customer' AS stage,
    round(
        avg(dateDiff('hour',
            order_delivered_carrier_date,
            order_delivered_customer_date
        )) / 24,
        2
    ) AS avg_days
FROM groceria.orders
WHERE order_status = 'delivered'
  AND order_delivered_carrier_date IS NOT NULL
  AND order_delivered_customer_date IS NOT NULL

ORDER BY sort_order;
