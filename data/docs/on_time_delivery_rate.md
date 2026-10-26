---
id: on_time_delivery_rate
name: On-time delivery rate
aliases: [OTD, on-time delivery, delivered on time, late delivery rate]
category: operations
unit: "%"
direction: higher_is_better
data_availability: full
related: [delivery_time, review_score]
---

# On-time delivery rate

## Definition
The share of delivered orders that reached the customer no later than the delivery date
promised at purchase.

## Formula
```
On-time delivery rate = delivered orders with delivery date ≤ estimated date / delivered orders × 100%
```
- Compared at **day** level: `order_estimated_delivery_date` always has time 00:00, so a
  timestamp comparison would count a delivery at 10:00 on the promised day as late.
- **Delivered orders**: status `delivered` with a non-null `order_delivered_customer_date`.

## Calculation on Olist data
```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(100.0 * count(*) FILTER (
                 WHERE o.order_delivered_customer_date::date <= o.order_estimated_delivery_date::date
             ) / count(*), 2) AS on_time_delivery_rate_pct
FROM olist.orders AS o
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY month
ORDER BY month;
```
Late delivery rate = 100% − on-time delivery rate.

## Interpretation
Late deliveries are the strongest driver of low [review_score](review_score.md).

## Pitfalls
- A few delivered orders have no delivery date; they are excluded, not counted as late.
