---
id: cac
name: Customer Acquisition Cost
aliases: [CAC, acquisition cost, cost per new customer]
category: marketing
unit: BRL
direction: lower_is_better
data_availability: none
related: [clv, ad_spend_share, unit_economics]
---

# Customer Acquisition Cost (CAC)

## Definition
How much the business spends on marketing to acquire one new customer. Compared with
[clv](clv.md): a healthy business has CLV well above CAC.

## Formula
```
CAC = marketing spend / number of new customers, for the same period
```
- **New customer**: a `customer_unique_id` whose first valid order falls in the period
- **Marketing spend**: all paid acquisition costs (ads, agencies, promotions)

## Calculation on Olist data
Not possible. Olist has no marketing spend data. New customers per month can be counted, so
CAC could be calculated once spend is added:

```sql
WITH first_orders AS (
    SELECT c.customer_unique_id,
           min(o.order_purchase_timestamp) AS first_order_at
    FROM olist.orders AS o
    JOIN olist.customers AS c USING (customer_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
)
SELECT date_trunc('month', first_order_at)::date AS month,
       count(*) AS new_customers
FROM first_orders
GROUP BY month
ORDER BY month;
```

## Interpretation
Track CAC by channel; a blended CAC hides channels that do not pay back.

## Pitfalls
- Dividing by all customers instead of new ones understates CAC.
