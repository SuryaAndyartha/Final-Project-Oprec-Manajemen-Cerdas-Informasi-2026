SELECT
    c.customer_state AS "Customer State",
    round(avg(oi.freight_value), 2) AS "Average Freight Cost",
    count(*) AS "Total Items Shipped"
FROM groceria.order_items oi
JOIN groceria.orders o
    ON oi.order_id = o.order_id
JOIN groceria.customers c
    ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
HAVING count(*) >= 100
ORDER BY "Average Freight Cost" DESC;
