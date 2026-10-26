---
id: cross_sell_rate
name: Cross-sell rate
aliases: [cross-sell, cross selling rate, multi-category order share, basket diversity]
category: sales
unit: "%"
direction: higher_is_better
data_availability: full
related: [aov, gmv]
---

# Cross-sell rate

## Definition
The share of orders in which the customer bought products from two or more different
categories. It measures how well the store sells complementary products.

## Formula
```
Cross-sell rate = orders with ≥ 2 distinct product categories / valid orders that have items × 100%
```
- **Product category**: `products.product_category_name`
- **Valid orders**: see [conventions](conventions.md)

## Calculation on Olist data
Count distinct categories per order, then take the share of orders with at least two.
Products without a category are ignored by `count(DISTINCT ...)`.

```sql
WITH order_categories AS (
    SELECT oi.order_id,
           count(DISTINCT p.product_category_name) AS categories
    FROM olist.order_items AS oi
    JOIN olist.orders AS o USING (order_id)
    JOIN olist.products AS p USING (product_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY oi.order_id
)
SELECT round(100.0 * count(*) FILTER (WHERE categories >= 2) / count(*), 2)
       AS cross_sell_rate_pct
FROM order_categories;
```

## Interpretation
- Low values are normal for a marketplace where customers search for one specific product.
- Cross-sell grows best on complementary pairs (mattress + pillow, bed + mattress). The
  metric shows whether recommendations and sales scripts actually work.

## Pitfalls
- Do not count items or distinct products. Buying two units of the same product, or two
  similar products, is a larger order, not a cross-sell. In Olist ~10% of orders have two or
  more items, but under 1% contain two or more categories.
- Promotional bundles sold as a single SKU are not cross-sell, even if they contain several
  products.
