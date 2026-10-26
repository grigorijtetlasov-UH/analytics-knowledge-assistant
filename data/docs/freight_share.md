---
id: freight_share
name: Freight share
aliases: [delivery cost share, shipping share, freight ratio, freight to order value, частка доставки, доля доставки в чеке, delivery share, скільки з'їдає доставка]
category: operations
unit: "%"
direction: lower_is_better
data_availability: full
related: [gmv, unit_economics, delivery_time]
---

# Freight share

## Definition
The share of the total order value that customers pay for delivery. High freight share
discourages purchases of cheap items and hurts conversion.

## Formula
```
Freight share = Σ freight_value / Σ (price + freight_value) × 100%, over valid orders
```
- **Valid orders**: see [conventions](conventions.md)

## Calculation on Olist data
```sql
SELECT round(100.0 * sum(oi.freight_value) / sum(oi.price + oi.freight_value), 2)
       AS freight_share_pct
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable');
```
Group by `products.product_category_name` or `customers.customer_state` to find where
delivery is relatively expensive.

## Interpretation
Freight share is highest for cheap and heavy items and for remote states.

## Pitfalls
- Averaging per-order freight percentages gives a different number from the ratio of sums;
  state which one you report.
