---
id: delivery_time
name: Average delivery time
aliases: [delivery time, lead time, days to deliver, shipping time]
category: operations
unit: days
direction: lower_is_better
data_availability: full
related: [on_time_delivery_rate, freight_share, review_score]
---

# Average delivery time

## Definition
How many days pass on average between the purchase and the delivery to the customer.

## Formula
```
Delivery time = avg(order_delivered_customer_date − order_purchase_timestamp), in days,
over delivered orders
```
- **Delivered orders**: status `delivered` with a non-null `order_delivered_customer_date`

## Calculation on Olist data
```sql
SELECT round(avg(extract(epoch FROM o.order_delivered_customer_date - o.order_purchase_timestamp)
                 / 86400)::numeric, 1) AS avg_delivery_days,
       round(percentile_cont(0.5) WITHIN GROUP (
                 ORDER BY extract(epoch FROM o.order_delivered_customer_date - o.order_purchase_timestamp)
                          / 86400)::numeric, 1) AS median_delivery_days
FROM olist.orders AS o
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL;
```
Split into stages with `order_approved_at` (payment approval) and
`order_delivered_carrier_date` (handover to the carrier) to see where time is lost.

## Interpretation
Compare by `customers.customer_state`: distance from the seller dominates delivery time.

## Pitfalls
- A long tail of very slow deliveries pulls the mean up; report the median too.
