---
id: repeat_purchase_rate
name: Repeat purchase rate
aliases: [repeat rate, returning customer rate, retention, repurchase rate, повторні покупки, "% повторних клієнтів", повторники]
category: customers
unit: "%"
direction: higher_is_better
data_availability: full
related: [clv, conventions]
---

# Repeat purchase rate

## Definition
The share of customers who placed more than one order. It measures loyalty and how much
growth can come from existing customers.

## Formula
```
Repeat purchase rate = customers with ≥ 2 valid orders / customers with ≥ 1 valid order × 100%
```
- **Customer**: `customer_unique_id`, see [conventions](conventions.md)
- **Valid orders**: see [conventions](conventions.md)

## Calculation on Olist data
```sql
WITH customer_orders AS (
    SELECT c.customer_unique_id,
           count(*) AS orders
    FROM olist.orders AS o
    JOIN olist.customers AS c USING (customer_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
)
SELECT round(100.0 * count(*) FILTER (WHERE orders >= 2) / count(*), 2)
       AS repeat_purchase_rate_pct
FROM customer_orders;
```

## Interpretation
Olist is a marketplace for mostly one-off purchases, so the rate is low.

## Pitfalls
- Using `customer_id` gives 0%: it is unique per order.
- The rate depends on the observation window; customers who first bought in the last
  months had little time to come back.
