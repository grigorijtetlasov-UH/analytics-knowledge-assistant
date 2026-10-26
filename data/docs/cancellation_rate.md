---
id: cancellation_rate
name: Cancellation rate
aliases: [cancel rate, order cancellation rate, canceled orders share, "% скасувань", відміни, процент отмен]
category: operations
unit: "%"
direction: lower_is_better
data_availability: partial
related: [conventions, realized_revenue]
---

# Cancellation rate

## Definition
The share of placed orders that were called off before fulfilment: canceled by the customer
or the seller, or unavailable (the seller could not fulfil it).

## Formula
```
Cancellation rate = orders with status 'canceled' or 'unavailable' / all orders × 100%
```
Unlike most metrics, the denominator is **all** orders, not only valid ones.

## Calculation on Olist data
```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(100.0 * count(*) FILTER (WHERE o.order_status IN ('canceled', 'unavailable'))
             / count(*), 2) AS cancellation_rate_pct
FROM olist.orders AS o
GROUP BY month
ORDER BY month;
```

## Interpretation
Spikes usually point to stock problems at specific sellers; break down by seller.

## Pitfalls
- In e-commerce, **refusal rate** usually means the share of orders the customer refused at
  delivery. Olist has no such status, so refusal rate cannot be calculated from this data.
  Do not substitute cancellation rate for it.
- Olist does not record who canceled (customer or seller) or why.
