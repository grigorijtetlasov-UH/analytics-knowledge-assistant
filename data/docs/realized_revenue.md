---
id: realized_revenue
name: Realized revenue
aliases: [delivered revenue, actual revenue, net sales delivered]
category: sales
unit: BRL
direction: higher_is_better
data_availability: full
related: [gmv, cancellation_rate, conventions]
---

# Realized revenue

## Definition
The value of goods that actually reached customers in a period. Unlike [gmv](gmv.md), it
excludes orders still in transit or never delivered.

## Formula
```
Realized revenue = Σ price of all items in orders with status 'delivered'
```
Freight is excluded, as in GMV. The difference from GMV is explained in
[conventions](conventions.md).

## Calculation on Olist data
Same as GMV, but filtered to `order_status = 'delivered'`. The period is still the purchase
month, so GMV and realized revenue for the same month are comparable.

```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       sum(oi.price) AS realized_revenue
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status = 'delivered'
GROUP BY month
ORDER BY month;
```

## Interpretation
Realized revenue / GMV for a closed period shows how much of what was ordered was delivered.

## Pitfalls
- For the most recent months realized revenue looks low only because orders are still in
  transit; compare closed periods.
