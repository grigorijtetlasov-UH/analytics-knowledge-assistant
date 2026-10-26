---
id: review_score
name: Average review score
aliases: [review score, rating, CSAT, customer satisfaction, negative review rate]
category: quality
unit: score
direction: higher_is_better
data_availability: full
related: [on_time_delivery_rate, delivery_time]
---

# Average review score

## Definition
The average rating (1 to 5) customers give after an order, and the share of negative
reviews. It is the dataset's measure of customer satisfaction.

## Formula
```
Average review score = avg(review_score) over all reviews
Negative review rate = reviews with score 1 or 2 / all reviews × 100%
```

## Calculation on Olist data
```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(avg(r.review_score), 2) AS avg_review_score,
       round(100.0 * count(*) FILTER (WHERE r.review_score <= 2) / count(*), 2)
           AS negative_review_rate_pct
FROM olist.order_reviews AS r
JOIN olist.orders AS o USING (order_id)
GROUP BY month
ORDER BY month;
```

## Interpretation
Scores are strongly skewed toward 5; watch the negative review rate, it moves more.

## Pitfalls
- The average is taken over reviews, not orders, by design. Some orders have more than one
  review and some have none, so a per-order average (first average each order's reviews,
  then average the orders) gives a slightly different number. State which one you report.
