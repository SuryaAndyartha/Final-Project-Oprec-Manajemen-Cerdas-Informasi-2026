SELECT
    o.order_id AS "Order ID",
    r.review_score AS "Review Score",
    CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
        THEN 'On Time'
        ELSE 'Late'
    END AS "Delivery Status"

FROM groceria.orders o
JOIN groceria.order_reviews r
    ON o.order_id = r.order_id

WHERE o.order_status = 'delivered'
  AND r.review_score IS NOT NULL;
