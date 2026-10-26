---
id: conventions
name: Conventions and business rules
aliases: [business rules, definitions, valid order, data conventions, glossary]
category: reference
data_availability: full
related: [gmv, realized_revenue, aov, cancellation_rate]
---

# Conventions and business rules

## Definition
Shared rules that every metric document relies on: what counts as an order, a customer,
revenue and a reporting period. If a metric document does not say otherwise, these apply.

## Valid order
An order counts toward sales metrics unless its `order_status` is `canceled` or
`unavailable`. All other statuses (`delivered`, `shipped`, `invoiced`, `processing`,
`approved`, `created`) are valid: the customer placed the order and it was not called off.

```sql
SELECT count(*) AS valid_orders
FROM olist.orders AS o
WHERE o.order_status NOT IN ('canceled', 'unavailable');
```

## GMV vs realized revenue
- **GMV** (gross merchandise value) measures what customers **ordered**: Σ `price` over
  valid orders. It includes orders still in transit. See [gmv](gmv.md).
- **Realized revenue** measures what was **actually delivered**: Σ `price` over orders with
  status `delivered`. See [realized_revenue](realized_revenue.md).

GMV ≥ realized revenue. The gap is orders not delivered yet (or never). For recent
periods the gap is large because many orders are still in transit; for closed periods it
is small. Use GMV for demand and sales performance, realized revenue for what the business
has actually earned.

Neither includes freight. Price + freight is **total order value**, see [gmv](gmv.md).

## Customer
A customer is a `customer_unique_id`. The `customer_id` column in `orders` is created
anew for every order, so counting `customer_id` treats every order as a new customer.

## Money, dates and periods
- Currency: Brazilian real (BRL). Money comes from `order_items.price` and
  `order_items.freight_value`; do not use `order_payments.payment_value` for revenue (it
  includes voucher splits and does not match item prices for some orders).
- An order belongs to the period of `order_purchase_timestamp`.
- Timestamps are Brazilian local time without a time-zone offset.
- Complete months in the dataset: **2017-01 to 2018-08**. 2016 and Sep–Oct 2018 contain only a
  handful of orders; exclude them from trends and month-over-month comparisons.

## Pitfalls
- Counting `customer_id` instead of `customer_unique_id` makes repeat purchases look like zero.
- A few valid orders have no rows in `order_items`; per-order averages should divide by
  orders that have items.
