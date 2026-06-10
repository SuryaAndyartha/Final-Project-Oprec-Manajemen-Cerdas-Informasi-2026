SELECT
    oi.seller_id AS "Seller ID",

    count(DISTINCT o.order_id) AS "Total Delivered Orders",

    round(
        avg(
            dateDiff(
                'hour',
                o.order_approved_at,
                o.order_delivered_carrier_date
            ) / 24.0
        ),
        2
    ) AS "Average Seller Processing Time (Days)"

FROM groceria.order_items oi

JOIN groceria.orders o
    ON oi.order_id = o.order_id

WHERE o.order_status = 'delivered'
  AND o.order_approved_at IS NOT NULL
  AND o.order_delivered_carrier_date IS NOT NULL

GROUP BY oi.seller_id

HAVING count(DISTINCT o.order_id) >= 100

ORDER BY "Average Seller Processing Time (Days)" DESC

LIMIT 20;
