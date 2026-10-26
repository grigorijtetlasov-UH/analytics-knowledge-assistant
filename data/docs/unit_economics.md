---
id: unit_economics
name: Unit economics per order
aliases: [unit economics, contribution margin per order, order profitability, margin per order]
category: finance
unit: BRL
direction: higher_is_better
data_availability: partial
related: [aov, freight_share, cac, clv, ad_spend_share]
---

# Unit economics per order

## Definition
Whether a single average order makes or loses money after all variable costs. If the
contribution per order is negative, growth in orders increases losses.

## Formula
```
Contribution per order = AOV
                       − cost of goods per order
                       − fulfilment and delivery cost per order (paid by the business)
                       − marketplace commission per order
                       − payment processing fees per order
                       − advertising cost per order
Contribution margin % = contribution per order / AOV × 100%
```
- **AOV**: see [aov](aov.md)
- **Advertising cost per order**: ad spend / orders; see [ad_spend_share](ad_spend_share.md)

## Calculation on Olist data
Only the revenue side is available: item price and the freight the customer paid. Cost of
goods, commissions, fees and ad spend are not in the dataset, so contribution cannot be
calculated. What can be shown:

```sql
SELECT round(sum(oi.price) / count(DISTINCT oi.order_id), 2) AS aov,
       round(sum(oi.freight_value) / count(DISTINCT oi.order_id), 2) AS freight_per_order
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable');
```

## Interpretation
Look at which cost line grows fastest relative to AOV.

## Pitfalls
- In Olist freight is paid by the customer, so it is not a cost line here.
