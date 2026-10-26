---
id: gmv
name: Gross Merchandise Value
aliases: [GMV, gross sales, merchandise value, sales volume, оборот, сума замовлень, скільки назамовляли]
category: sales
unit: BRL
direction: higher_is_better
data_availability: full
related: [realized_revenue, aov, freight_share, conventions]
---

# Gross Merchandise Value (GMV)

## Definition
The total value of goods customers ordered in a period, before cancellations of delivered
orders, returns and costs. It is the main measure of marketplace sales volume.

## Formula
```
GMV = Σ price of all items in valid orders
```
- **price**: item price, excluding freight
- **Valid orders**: see [conventions](conventions.md)

**Total order value** is a related measure that includes delivery:
```
Total order value = Σ (price + freight_value) of all items in valid orders
```

## Calculation on Olist data
Table `olist.order_items` joined to `olist.orders`, filtered to valid orders, grouped by the
month of `order_purchase_timestamp`.

```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       sum(oi.price) AS gmv,
       sum(oi.price + oi.freight_value) AS total_order_value
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY month
ORDER BY month;
```

## Interpretation
Growth in GMV comes from more orders or a higher [aov](aov.md); check both.

## Pitfalls
- GMV is not revenue the business has earned; see [realized_revenue](realized_revenue.md).
- Mixing GMV and total order value across reports makes numbers disagree: in Olist total
  order value is ~17% higher than GMV (the freight).
