---
id: aov
name: Average Order Value
aliases: [AOV, average check, average basket value, average order size]
category: sales
unit: BRL
direction: higher_is_better
data_availability: full
related: [gmv, cross_sell_rate, unit_economics, clv]
---

# Average Order Value (AOV)

## Definition
The average amount a customer spends on goods in one order. Together with the number of
orders it explains GMV: GMV = orders × AOV.

## Formula
```
AOV = GMV / number of valid orders that have items
```
- **GMV**: see [gmv](gmv.md) (price only, freight excluded)
- **Valid orders**: see [conventions](conventions.md)

## Calculation on Olist data
Divide by distinct orders that appear in `order_items`, so that the few valid orders with
no items do not lower the average.

```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(sum(oi.price) / count(DISTINCT oi.order_id), 2) AS aov
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY month
ORDER BY month;
```

## Interpretation
- Rising AOV with flat order count usually means pricier products or more items per order.
- AOV grows with the share of high-ticket categories (in Olist: computers, home appliances,
  office and bedroom furniture) and with cross-sell. Track it by category, not only in total.
- A rising AOV with falling order count can mean price increases are pushing away smaller
  baskets: read it together with the number of orders.

## Pitfalls
- Averaging `price` over item rows gives average item price, not AOV.
- A few very large orders shift the mean noticeably. Report the median alongside the average.
