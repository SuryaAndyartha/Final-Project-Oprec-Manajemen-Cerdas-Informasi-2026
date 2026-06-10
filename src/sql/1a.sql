SELECT
    round(
        avg(
            dateDiff(
                'hour',
                order_purchase_timestamp,
                order_delivered_customer_date
            )
        ) / 24,
        2
    ) AS avg_days,

    round(
        median(
            dateDiff(
                'hour',
                order_purchase_timestamp,
                order_delivered_customer_date
            )
        ) / 24,
        2
    ) AS median_days,

    round(
        quantile(0.9)(
            dateDiff(
                'hour',
                order_purchase_timestamp,
                order_delivered_customer_date
            )
        ) / 24,
        2
    ) AS p90_days

FROM groceria.orders

WHERE order_status = 'delivered'
  AND order_purchase_timestamp IS NOT NULL
  AND order_delivered_customer_date IS NOT NULL;
