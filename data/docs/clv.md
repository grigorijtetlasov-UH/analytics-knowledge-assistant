---
id: clv
name: Customer Lifetime Value
aliases: [CLV, LTV, lifetime value, customer value, цінність клієнта, сколько приносит клиент]
category: customers
unit: BRL
direction: higher_is_better
data_availability: partial
related: [aov, repeat_purchase_rate, cac, unit_economics]
---

# Customer Lifetime Value (CLV)

## Definition
The value a customer brings over the whole relationship with the store. It is compared
with [cac](cac.md) to decide how much can be spent on acquiring a customer.

## Formula
Predictive CLV (margin-based, the version used for CAC decisions):
```
CLV = AOV × purchase frequency × gross margin % × customer lifetime
```
Historical CLV (what Olist data supports):
```
Historical CLV = GMV / number of customers, over the observed period
```
- **AOV**: see [aov](aov.md)
- **Purchase frequency**: orders per customer per year
- **Customer lifetime**: expected years a customer keeps buying
- **Customer**: `customer_unique_id`, see [conventions](conventions.md)

## Calculation on Olist data
Olist has no product costs, so gross margin is unknown and only historical CLV on GMV can be
calculated.

```sql
SELECT round(sum(oi.price) / count(DISTINCT c.customer_unique_id), 2) AS historical_clv
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
JOIN olist.customers AS c USING (customer_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable');
```

## Interpretation
With a low repeat purchase rate, historical CLV is close to AOV.

## Pitfalls
- CLV on revenue overstates value; for CLV/CAC use CLV on margin.
