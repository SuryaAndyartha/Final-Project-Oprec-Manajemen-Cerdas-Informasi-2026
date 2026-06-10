SELECT
    oi.seller_id,

    count(DISTINCT o.order_id) AS total_orders,

    round(
        100.0 *
        count(
            DISTINCT CASE
                WHEN o.order_delivered_customer_date >
                     o.order_estimated_delivery_date
                THEN o.order_id
            END
        )
        / count(DISTINCT o.order_id),
        2
    ) AS late_delivery_rate

FROM groceria.order_items oi

JOIN groceria.orders o
    ON oi.order_id = o.order_id

WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL

GROUP BY oi.seller_id

HAVING total_orders >= 100;
