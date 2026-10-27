# Answer eval: models

> **Note.** Formal checks only (status, cited documents, clarifying question, SQL present, answer language); answer correctness is judged by an LLM in milestone 6. The cases were written by the same person as the docs.

12 cases x 3 run(s) per model, effort `low`, off-topic threshold 0.22. Cost and latency are averaged over questions that reached the LLM.

## Summary

| model | passed | failed cases | cost per question | total cost | mean latency, s | cache read tokens |
|---|---:|---|---:|---:|---:|---:|
| claude-opus-5-5 | 36/36 | - | $0.0117 | $0.3867 | 4.2 | 47553 |
| claude-sonnet-5-5 | 36/36 | - | $0.0055 | $0.1817 | 2.9 | 46112 |
| claude-haiku-5-5 | 32/36 | a04, a06 | $0.0003 | $0.0085 | 2.3 | 47553 |

## Cases

| model | run | id | kind | status | sources | cost | s | result |
|---|---:|---|---|---|---|---:|---:|---|
| claude-opus-5-5 | 1 | a01 | answered | answered | aov | $0.0142 | 5.0 | pass |
| claude-opus-5-5 | 1 | a02 | answered | answered | on_time_delivery_rate | $0.0162 | 6.3 | pass |
| claude-opus-5-5 | 1 | a03 | answered_definition_without_data | answered | cac | $0.0107 | 3.4 | pass |
| claude-opus-5-5 | 1 | a04 | answered_numeric | answered | aov | $0.0151 | 7.2 | pass |
| claude-opus-5-5 | 1 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0128 | 5.2 | pass |
| claude-opus-5-5 | 1 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0120 | 4.0 | pass |
| claude-opus-5-5 | 1 | a07 | no_data | no_data | conversion_rate | $0.0106 | 4.6 | pass |
| claude-opus-5-5 | 1 | a08 | no_data | no_data | cac | $0.0147 | 4.8 | pass |
| claude-opus-5-5 | 1 | a09 | no_data | no_data | ad_spend_share | $0.0093 | 3.1 | pass |
| claude-opus-5-5 | 1 | o09 | off_topic_near | off_topic |  | $0.0079 | 2.5 | pass |
| claude-opus-5-5 | 1 | o10 | off_topic_near | off_topic | review_score | $0.0062 | 2.5 | pass |
| claude-opus-5-5 | 1 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |
| claude-opus-5-5 | 2 | a01 | answered | answered | aov | $0.0135 | 4.3 | pass |
| claude-opus-5-5 | 2 | a02 | answered | answered | on_time_delivery_rate | $0.0162 | 5.6 | pass |
| claude-opus-5-5 | 2 | a03 | answered_definition_without_data | answered | cac | $0.0109 | 3.3 | pass |
| claude-opus-5-5 | 2 | a04 | answered_numeric | answered | aov | $0.0148 | 5.5 | pass |
| claude-opus-5-5 | 2 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0127 | 4.7 | pass |
| claude-opus-5-5 | 2 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0123 | 3.9 | pass |
| claude-opus-5-5 | 2 | a07 | no_data | no_data | conversion_rate | $0.0098 | 7.2 | pass |
| claude-opus-5-5 | 2 | a08 | no_data | no_data | cac | $0.0142 | 4.7 | pass |
| claude-opus-5-5 | 2 | a09 | no_data | no_data | ad_spend_share | $0.0093 | 3.4 | pass |
| claude-opus-5-5 | 2 | o09 | off_topic_near | off_topic |  | $0.0077 | 1.9 | pass |
| claude-opus-5-5 | 2 | o10 | off_topic_near | off_topic |  | $0.0062 | 2.4 | pass |
| claude-opus-5-5 | 2 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |
| claude-opus-5-5 | 3 | a01 | answered | answered | aov | $0.0149 | 4.8 | pass |
| claude-opus-5-5 | 3 | a02 | answered | answered | on_time_delivery_rate | $0.0162 | 5.5 | pass |
| claude-opus-5-5 | 3 | a03 | answered_definition_without_data | answered | cac | $0.0108 | 3.4 | pass |
| claude-opus-5-5 | 3 | a04 | answered_numeric | answered | aov | $0.0149 | 5.4 | pass |
| claude-opus-5-5 | 3 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0126 | 4.7 | pass |
| claude-opus-5-5 | 3 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0120 | 4.0 | pass |
| claude-opus-5-5 | 3 | a07 | no_data | no_data | conversion_rate | $0.0100 | 3.8 | pass |
| claude-opus-5-5 | 3 | a08 | no_data | no_data | cac | $0.0144 | 4.7 | pass |
| claude-opus-5-5 | 3 | a09 | no_data | no_data | ad_spend_share | $0.0094 | 3.2 | pass |
| claude-opus-5-5 | 3 | o09 | off_topic_near | off_topic |  | $0.0078 | 1.7 | pass |
| claude-opus-5-5 | 3 | o10 | off_topic_near | off_topic | review_score | $0.0065 | 2.5 | pass |
| claude-opus-5-5 | 3 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |
| claude-sonnet-5-5 | 1 | a01 | answered | answered | aov | $0.0096 | 2.8 | pass |
| claude-sonnet-5-5 | 1 | a02 | answered | answered | on_time_delivery_rate | $0.0081 | 4.2 | pass |
| claude-sonnet-5-5 | 1 | a03 | answered_definition_without_data | answered | cac | $0.0048 | 2.4 | pass |
| claude-sonnet-5-5 | 1 | a04 | answered_numeric | answered | aov | $0.0069 | 4.3 | pass |
| claude-sonnet-5-5 | 1 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0060 | 3.8 | pass |
| claude-sonnet-5-5 | 1 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0052 | 3.0 | pass |
| claude-sonnet-5-5 | 1 | a07 | no_data | no_data | conversion_rate | $0.0043 | 2.6 | pass |
| claude-sonnet-5-5 | 1 | a08 | no_data | no_data | cac | $0.0065 | 3.2 | pass |
| claude-sonnet-5-5 | 1 | a09 | no_data | no_data | ad_spend_share | $0.0037 | 1.5 | pass |
| claude-sonnet-5-5 | 1 | o09 | off_topic_near | off_topic |  | $0.0038 | 1.4 | pass |
| claude-sonnet-5-5 | 1 | o10 | off_topic_near | off_topic |  | $0.0031 | 2.0 | pass |
| claude-sonnet-5-5 | 1 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |
| claude-sonnet-5-5 | 2 | a01 | answered | answered | aov | $0.0065 | 3.1 | pass |
| claude-sonnet-5-5 | 2 | a02 | answered | answered | on_time_delivery_rate | $0.0084 | 4.1 | pass |
| claude-sonnet-5-5 | 2 | a03 | answered_definition_without_data | answered | cac | $0.0048 | 2.2 | pass |
| claude-sonnet-5-5 | 2 | a04 | answered_numeric | answered | aov | $0.0071 | 4.6 | pass |
| claude-sonnet-5-5 | 2 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0059 | 3.8 | pass |
| claude-sonnet-5-5 | 2 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0054 | 2.8 | pass |
| claude-sonnet-5-5 | 2 | a07 | no_data | no_data | conversion_rate | $0.0043 | 2.6 | pass |
| claude-sonnet-5-5 | 2 | a08 | no_data | no_data | cac | $0.0064 | 3.2 | pass |
| claude-sonnet-5-5 | 2 | a09 | no_data | no_data | ad_spend_share | $0.0037 | 1.5 | pass |
| claude-sonnet-5-5 | 2 | o09 | off_topic_near | off_topic |  | $0.0038 | 2.1 | pass |
| claude-sonnet-5-5 | 2 | o10 | off_topic_near | off_topic |  | $0.0031 | 1.8 | pass |
| claude-sonnet-5-5 | 2 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |
| claude-sonnet-5-5 | 3 | a01 | answered | answered | aov | $0.0062 | 2.9 | pass |
| claude-sonnet-5-5 | 3 | a02 | answered | answered | on_time_delivery_rate | $0.0084 | 4.5 | pass |
| claude-sonnet-5-5 | 3 | a03 | answered_definition_without_data | answered | cac | $0.0048 | 2.5 | pass |
| claude-sonnet-5-5 | 3 | a04 | answered_numeric | answered | aov | $0.0072 | 4.5 | pass |
| claude-sonnet-5-5 | 3 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0065 | 4.5 | pass |
| claude-sonnet-5-5 | 3 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0054 | 2.9 | pass |
| claude-sonnet-5-5 | 3 | a07 | no_data | no_data | conversion_rate | $0.0042 | 2.7 | pass |
| claude-sonnet-5-5 | 3 | a08 | no_data | no_data | cac | $0.0065 | 3.1 | pass |
| claude-sonnet-5-5 | 3 | a09 | no_data | no_data | ad_spend_share | $0.0037 | 1.6 | pass |
| claude-sonnet-5-5 | 3 | o09 | off_topic_near | off_topic |  | $0.0039 | 1.4 | pass |
| claude-sonnet-5-5 | 3 | o10 | off_topic_near | off_topic |  | $0.0032 | 2.3 | pass |
| claude-sonnet-5-5 | 3 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |
| claude-haiku-5-5 | 1 | a01 | answered | answered | aov | $0.0003 | 2.7 | pass |
| claude-haiku-5-5 | 1 | a02 | answered | answered | on_time_delivery_rate | $0.0003 | 2.6 | pass |
| claude-haiku-5-5 | 1 | a03 | answered_definition_without_data | answered | cac | $0.0002 | 2.0 | pass |
| claude-haiku-5-5 | 1 | a04 | answered_numeric | answered | aov | $0.0004 | 3.4 | pass |
| claude-haiku-5-5 | 1 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0003 | 2.7 | pass |
| claude-haiku-5-5 | 1 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0003 | 2.7 | FAIL: answer is in Russian |
| claude-haiku-5-5 | 1 | a07 | no_data | no_data | conversion_rate | $0.0004 | 3.4 | pass |
| claude-haiku-5-5 | 1 | a08 | no_data | no_data | cac | $0.0002 | 1.6 | pass |
| claude-haiku-5-5 | 1 | a09 | no_data | no_data | ad_spend_share | $0.0002 | 2.6 | pass |
| claude-haiku-5-5 | 1 | o09 | off_topic_near | off_topic |  | $0.0002 | 1.1 | pass |
| claude-haiku-5-5 | 1 | o10 | off_topic_near | off_topic |  | $0.0002 | 1.9 | pass |
| claude-haiku-5-5 | 1 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |
| claude-haiku-5-5 | 2 | a01 | answered | answered | aov | $0.0003 | 2.3 | pass |
| claude-haiku-5-5 | 2 | a02 | answered | answered | on_time_delivery_rate | $0.0003 | 2.9 | pass |
| claude-haiku-5-5 | 2 | a03 | answered_definition_without_data | answered | cac | $0.0002 | 2.3 | pass |
| claude-haiku-5-5 | 2 | a04 | answered_numeric | answered | aov | $0.0003 | 2.5 | FAIL: answer lacks 'SELECT' |
| claude-haiku-5-5 | 2 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0003 | 2.8 | pass |
| claude-haiku-5-5 | 2 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0003 | 2.8 | FAIL: answer is in Russian |
| claude-haiku-5-5 | 2 | a07 | no_data | no_data | conversion_rate | $0.0002 | 1.9 | pass |
| claude-haiku-5-5 | 2 | a08 | no_data | no_data | cac | $0.0002 | 2.1 | pass |
| claude-haiku-5-5 | 2 | a09 | no_data | no_data | ad_spend_share | $0.0002 | 2.0 | pass |
| claude-haiku-5-5 | 2 | o09 | off_topic_near | off_topic | unit_economics, ad_spend_share, acos | $0.0002 | 1.3 | pass |
| claude-haiku-5-5 | 2 | o10 | off_topic_near | off_topic |  | $0.0002 | 1.4 | pass |
| claude-haiku-5-5 | 2 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |
| claude-haiku-5-5 | 3 | a01 | answered | answered | aov | $0.0003 | 2.6 | pass |
| claude-haiku-5-5 | 3 | a02 | answered | answered | on_time_delivery_rate | $0.0003 | 2.8 | pass |
| claude-haiku-5-5 | 3 | a03 | answered_definition_without_data | answered | cac | $0.0002 | 2.1 | pass |
| claude-haiku-5-5 | 3 | a04 | answered_numeric | answered | aov | $0.0003 | 2.6 | FAIL: answer lacks 'SELECT' |
| claude-haiku-5-5 | 3 | a05 | ambiguous | ambiguous | ad_spend_share, acos | $0.0003 | 2.7 | pass |
| claude-haiku-5-5 | 3 | a06 | ambiguous | ambiguous | ad_spend_share, acos | $0.0003 | 2.5 | pass |
| claude-haiku-5-5 | 3 | a07 | no_data | no_data | conversion_rate | $0.0004 | 4.0 | pass |
| claude-haiku-5-5 | 3 | a08 | no_data | no_data | cac | $0.0002 | 1.6 | pass |
| claude-haiku-5-5 | 3 | a09 | no_data | no_data | ad_spend_share | $0.0002 | 1.8 | pass |
| claude-haiku-5-5 | 3 | o09 | off_topic_near | off_topic |  | $0.0002 | 1.2 | pass |
| claude-haiku-5-5 | 3 | o10 | off_topic_near | off_topic |  | $0.0002 | 1.2 | pass |
| claude-haiku-5-5 | 3 | o01 | off_topic_far | off_topic |  |  | 0.0 | pass |

## Answers (run 1)

### claude-opus-5-5 · a01 · What is average order value and how is it calculated?

Average Order Value (AOV) is the average amount a customer spends on goods in one order. Together with the number of orders it explains GMV: GMV = orders × AOV [S1].

Formula [S2]:
```
AOV = GMV / number of valid orders that have items
```
- GMV counts price only; freight is excluded.
- Valid orders follow the company conventions [S2].

On Olist data, divide by distinct orders that appear in `order_items`, so that the few valid orders with no items do not lower the average [S3]:
```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(sum(oi.price) / count(DISTINCT oi.order_id), 2) AS aov
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY month
ORDER BY month;
```

Pitfalls [S4]:
- Averaging `price` over item rows gives average item price, not AOV.
- A few very large orders can shift the mean noticeably, so report the median alongside the average.

Interpretation: read AOV together with order count, and track it by category, since high-ticket categories and cross-sell raise it [S5].

### claude-opus-5-5 · a02 · Як рахується частка замовлень, доставлених вчасно?

On-time delivery rate — це частка доставлених замовлень, які дійшли до клієнта не пізніше дати доставки, обіцяної під час покупки [S5].

Формула [S2]:
```
On-time delivery rate = delivered orders with delivery date ≤ estimated date / delivered orders × 100%
```
- Доставлені замовлення — статус `delivered` і непорожня `order_delivered_customer_date` [S2].
- Порівняння робиться на рівні дня: `order_estimated_delivery_date` завжди має час 00:00, тож порівняння за timestamp зарахувало б доставку о 10:00 в обіцяний день як запізнення [S2].
- Кілька доставлених замовлень не мають дати доставки — їх виключають, а не рахують як запізнілі [S1].

SQL на даних Olist (по місяцях) [S4]:
```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(100.0 * count(*) FILTER (
                 WHERE o.order_delivered_customer_date::date <= o.order_estimated_delivery_date::date
             ) / count(*), 2) AS on_time_delivery_rate_pct
FROM olist.orders AS o
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY month
ORDER BY month;
```
Частка запізнілих доставок = 100% − on-time delivery rate [S4].

### claude-opus-5-5 · a03 · How is CAC defined?

Customer Acquisition Cost (CAC) is how much the business spends on marketing to acquire one new customer. It is compared with CLV: a healthy business has CLV well above CAC [S2].

Formula [S4]:
```
CAC = marketing spend / number of new customers, for the same period
```
- **New customer**: a `customer_unique_id` whose first valid order falls in the period.
- **Marketing spend**: all paid acquisition costs (ads, agencies, promotions).

Pitfall: dividing by all customers instead of new ones understates CAC [S3]. Track CAC by channel, because a blended CAC hides channels that do not pay back [S1].

Note: CAC cannot be calculated on Olist data because it has no marketing spend data. Only new customers per month can be counted [S5].

### claude-opus-5-5 · a04 · Який був середній чек у 2018 році?

Середній чек (AOV) — це середня сума, яку клієнт витрачає на товари в одному замовленні; GMV = orders × AOV [S2].

Формула: AOV = GMV / number of valid orders that have items, де GMV рахується лише за ціною товарів, без доставки (freight excluded) [S3]. Ділити треба на кількість унікальних замовлень з `order_items`, щоб валідні замовлення без товарів не занижували середнє [S5].

SQL з документації (помісячно; для 2018 року можна додати фільтр за `order_purchase_timestamp` у 2018 році або прибрати групування за місяцем) [S5]:
```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(sum(oi.price) / count(DISTINCT oi.order_id), 2) AS aov
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY month
ORDER BY month;
```

Саме значення за 2018 рік можна отримати лише виконавши цей запит до бази даних.

Зверніть увагу: не усереднюйте `price` по рядках товарів — це дасть середню ціну товару, а не AOV; кілька дуже великих замовлень помітно зсувають середнє, тому варто наводити й медіану [S1].

### claude-opus-5-5 · a05 · Як порахувати ДРР?

Термін «ДРР» у документації може означати дві різні метрики [S1][S2]:

1. Ad-spend share (ad_spend_share, TACoS) — частка всієї виручки, що витрачається на рекламу: рекламні витрати / уся виручка. Показує, яка частина кожного продажу йде на платне просування в цілому по бізнесу, включно з продажами, не пов'язаними з рекламою [S3][S1].

2. ACoS (Advertising Cost of Sales) — рекламні витрати / виручка, атрибутована рекламі [S1][S2]. Зверніть увагу: вікна атрибуції різняться між рекламними платформами, тому ACoS з двох платформ не можна порівнювати [S2].

Важливо: для обох метрик data_availability = "none" — у датасеті Olist немає даних про рекламні витрати, тож порахувати їх на цих даних не вийде [S1][S2][S3].

*Clarifying question:* Який знаменник ви маєте на увазі: усю виручку (ad-spend share) чи лише виручку, атрибутовану рекламі (ACoS)?

### claude-opus-5-5 · a06 · What is our DRR and how should we track it?

"DRR" can refer to two different metrics, which differ in the denominator [S1][S2]:

1. Ad-spend share (ad_spend_share, also TACoS): the share of total revenue spent on advertising, i.e. ad spend / all revenue. It covers the whole business, including sales not driven by ads [S3]. Compare it with contribution margin: if ad-spend share is higher, sales are unprofitable [S4].

2. ACoS (Advertising Cost of Sales): ad spend relative to revenue attributed to ads. Using ad-attributed revenue in the denominator turns the metric into ACoS [S1]. Note that attribution windows differ between ad platforms, so ACoS from two platforms is not comparable [S2].

Neither metric can be calculated from the Olist dataset: both have data availability "none" [S1][S2].

*Clarifying question:* Which denominator do you mean for DRR: all revenue (ad-spend share/TACoS) or only revenue attributed to ads (ACoS)?

### claude-opus-5-5 · a07 · Яка в нас конверсія сайту за 2018 рік?

Порахувати конверсію сайту за 2018 рік на даних Olist неможливо [S4].

Conversion rate — це частка візитів на сайт або в застосунок, які завершилися замовленням [S3]. Формула: Conversion rate = orders / sessions × 100%, де Sessions — візити з веб-аналітики (наприклад, GA4) за той самий період і канал, а Orders — валідні замовлення [S5].

У датасеті Olist є лише замовлення. Даних про трафік, сесії чи відвідувачів там немає. Для розрахунку потрібен експорт із веб-аналітики із сесіями в розрізі днів і каналів [S4]. Замовлення й сесії мають охоплювати той самий період і той самий обсяг трафіку [S2]. Конверсію варто порівнювати за каналами та пристроями, бо загальна цифра приховує різницю між ними [S1].

### claude-opus-5-5 · a08 · Calculate our customer acquisition cost for 2018.

CAC for 2018 cannot be calculated from the Olist data.

- Formula: CAC = marketing spend / number of new customers, for the same period [S1]. A new customer is a `customer_unique_id` whose first valid order falls in the period. Marketing spend is all paid acquisition costs (ads, agencies, promotions) [S1].
- What is missing: Olist has no marketing spend data, so the numerator is unavailable [S5].
- What is available: the denominator, new customers per month, can be counted. CAC could then be calculated once spend data is added [S5]. The query from the documentation:

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

Divide by new customers only, not all customers. Dividing by all customers understates CAC [S2]. The documentation also recommends tracking CAC by channel [S4].

### claude-opus-5-5 · a09 · What share of our revenue did we spend on advertising last year?

This is the ad-spend share metric: the share of total revenue spent on advertising [S1].

Formula: Ad-spend share = total advertising spend / total revenue × 100%, for the same period; total revenue can be gmv or realized_revenue, and you should state which [S2].

It cannot be calculated on the Olist data: the dataset has no advertising spend data. The calculation would need ad spend per day and channel from the ad platforms; revenue itself is available [S3].

Once spend data is available, compare the result with contribution margin: if ad-spend share is higher, sales are unprofitable [S4].

### claude-opus-5-5 · o09 · What is EBITDA and how is it calculated?

The available metric documentation does not cover EBITDA. The sources only describe unit economics per order (contribution margin), ad-spend share and ACoS, so I can't provide a definition or formula for EBITDA from them.

### claude-opus-5-5 · o10 · Що таке NPS і як його рахувати?

Документація з метрик не містить визначення чи формули NPS (Net Promoter Score). Найближча за змістом метрика в джерелах — середня оцінка відгуків (review_score), але це інша метрика [S2]. Можу пояснити її, якщо це підходить.

### claude-opus-5-5 · o01 · What's the weather like in Kyiv tomorrow?

This question is not covered by the metric documentation, so I cannot answer it.

### claude-sonnet-5-5 · a01 · What is average order value and how is it calculated?

Average Order Value (AOV, average check) is the average amount a customer spends on goods in one order. Together with the number of orders it explains GMV: GMV = orders × AOV [S1].

Formula: AOV = GMV / number of valid orders that have items. GMV counts price only, freight excluded [S2].

On Olist data, divide by distinct orders in `order_items`, so that valid orders with no items do not lower the average [S3]:

SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(sum(oi.price) / count(DISTINCT oi.order_id), 2) AS aov
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY month
ORDER BY month;

Pitfalls: averaging `price` over item rows gives average item price, not AOV. A few very large orders shift the mean, so report the median alongside the average [S4].

### claude-sonnet-5-5 · a02 · Як рахується частка замовлень, доставлених вчасно?

Частка замовлень, доставлених вчасно (on_time_delivery_rate), — це частка доставлених замовлень, які надійшли до клієнта не пізніше обіцяної при покупці дати [S5].

Формула:
On-time delivery rate = delivered orders with delivery date ≤ estimated date / delivered orders × 100% [S2]

- Порівняння робиться на рівні **дня**: `order_estimated_delivery_date` завжди має час 00:00, тому порівняння за timestamp помилково вважало б доставку о 10:00 в обіцяний день запізненням [S2].
- Доставлені замовлення — це статус `delivered` з непорожнім `order_delivered_customer_date` [S2].
- Кілька доставлених замовлень без дати доставки виключаються, а не рахуються як запізнілі [S1].

SQL для Olist (по місяцях):
```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(100.0 * count(*) FILTER (
                 WHERE o.order_delivered_customer_date::date <= o.order_estimated_delivery_date::date
             ) / count(*), 2) AS on_time_delivery_rate_pct
FROM olist.orders AS o
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY month
ORDER BY month;
```
Late delivery rate = 100% − on-time delivery rate [S4].

### claude-sonnet-5-5 · a03 · How is CAC defined?

CAC (Customer Acquisition Cost) is how much the business spends on marketing to acquire one new customer [S2].

Formula: `CAC = marketing spend / number of new customers, for the same period` [S4].
- New customer: a `customer_unique_id` whose first valid order falls in the period [S4].
- Marketing spend: all paid acquisition costs (ads, agencies, promotions) [S4].

CAC is compared with CLV: a healthy business has CLV well above CAC [S2]. It should be tracked by channel, since a blended CAC hides channels that do not pay back [S1]. Dividing by all customers instead of new ones understates CAC [S3].

### claude-sonnet-5-5 · a04 · Який був середній чек у 2018 році?

Середній чек (AOV) — це середня сума, яку клієнт витрачає на товари в одному замовленні [S2]. Формула: AOV = GMV / кількість валідних замовлень, що мають позиції (GMV — лише price, без доставки) [S3].

На даних Olist ділимо на унікальні замовлення з `order_items`, щоб кілька валідних замовлень без позицій не занижували середнє [S5]:

```sql
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month,
       round(sum(oi.price) / count(DISTINCT oi.order_id), 2) AS aov
FROM olist.order_items AS oi
JOIN olist.orders AS o USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY month
ORDER BY month;
```

Само значення за 2018 рік потребує виконання цього запиту до бази даних (з відбором місяців 2018 року); у документації числа немає.

Зауваження: усереднення `price` по рядках позицій дає середню ціну товару, а не AOV; кілька дуже великих замовлень помітно зсувають середнє, тому варто показувати також медіану [S1].

### claude-sonnet-5-5 · a05 · Як порахувати ДРР?

Під «ДРР» можуть мати на увазі дві різні метрики:

1. Ad-spend share (частка реклами у виручці) — частка загальної виручки, яку витрачають на рекламу в усьому бізнесі, включно з продажами, не пов'язаними з рекламою [S3]. Тут у знаменнику вся виручка [S1].

2. ACoS (Advertising Cost of Sales) — у знаменнику стоїть виручка, атрибутована рекламі, а не вся виручка [S1][S2]. Також атрибуційні вікна різняться між рекламними платформами, тому ACoS з двох платформ не можна порівнювати [S2].

У документації немає точних формул чи SQL для цих метрик, а дані Olist для їх розрахунку недоступні (data_availability: none) [S1][S2].

*Clarifying question:* Яке саме знаменник ви маєте на увазі для ДРР: усю виручку (ad-spend share) чи виручку, атрибутовану рекламі (ACoS)?

### claude-sonnet-5-5 · a06 · What is our DRR and how should we track it?

"DRR" (ДРР) can mean two different metrics, and the question does not say which one:
- Ad-spend share (ad_spend_share): the share of total revenue spent on advertising, across the whole business including sales not driven by ads [S3]. The denominator is all revenue.
- ACoS (Advertising Cost of Sales): the same idea, but with revenue attributed to ads in the denominator [S1][S2]. Attribution windows differ between ad platforms, so ACoS from two platforms is not comparable [S2].
The sources do not give a calculation for either one, and the Olist data does not support calculating them (data_availability is "none") [S1][S2].

*Clarifying question:* Which denominator do you mean by DRR: all revenue (ad-spend share) or only revenue attributed to ads (ACoS)?

### claude-sonnet-5-5 · a07 · Яка в нас конверсія сайту за 2018 рік?

Порахувати конверсію сайту за 2018 рік на даних Olist неможливо. Формула: Conversion rate = orders / sessions × 100%, де sessions — візити з веб-аналітики (наприклад, GA4) за той самий період і канал, а orders — валідні замовлення [S5]. Olist містить лише замовлення: у ньому немає даних про трафік, сесії чи відвідувачів. Для розрахунку потрібен експорт з веб-аналітики з кількістю сесій по днях і каналах [S4]. Також замовлення та сесії мають охоплювати той самий період і ту саму сегментацію трафіку [S2].

### claude-sonnet-5-5 · a08 · Calculate our customer acquisition cost for 2018.

CAC for 2018 cannot be calculated from the Olist data. The formula is CAC = marketing spend / number of new customers, for the same period [S1]. Marketing spend means all paid acquisition costs (ads, agencies, promotions), and a new customer is a `customer_unique_id` whose first valid order falls in the period [S1]. Olist has no marketing spend data, so the calculation is not possible [S5]. Only the number of new customers per month can be counted, so CAC could be calculated once spend data is added [S5]. The query for new customers per month is:

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

### claude-sonnet-5-5 · a09 · What share of our revenue did we spend on advertising last year?

Ad-spend share = total advertising spend / total revenue × 100% for the same period, where total revenue is gmv or realized_revenue (state which) [S2]. It cannot be calculated on Olist data: the dataset has no advertising spend data. The calculation would need spend per day and channel from the ad platforms; revenue is available [S3].

### claude-sonnet-5-5 · o09 · What is EBITDA and how is it calculated?

The documentation does not cover EBITDA. The available sources only describe unit economics per order (contribution per order and contribution margin %), ad-spend share and ACoS.

### claude-sonnet-5-5 · o10 · Що таке NPS і як його рахувати?

Документація не охоплює метрику NPS, тому я не можу пояснити, що це таке і як її рахувати. У джерелах є лише метрики на кшталт повторних покупок, середньої оцінки відгуків, відсотка скасувань та частки витрат на рекламу.

### claude-sonnet-5-5 · o01 · What's the weather like in Kyiv tomorrow?

This question is not covered by the metric documentation, so I cannot answer it.

### claude-haiku-5-5 · a01 · What is average order value and how is it calculated?

Average Order Value (AOV) is the average amount a customer spends on goods in one order. Together with the number of orders it explains GMV: GMV = orders × AOV [S1]. Formula: AOV = GMV / number of valid orders that have items, where GMV counts price only with freight excluded, and valid orders are defined in the conventions [S2]. On Olist data, divide by distinct orders that appear in order_items, excluding orders with status canceled or unavailable, for example: SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month, round(sum(oi.price) / count(DISTINCT oi.order_id), 2) AS aov FROM olist.order_items AS oi JOIN olist.orders AS o USING (order_id) WHERE o.order_status NOT IN ('canceled', 'unavailable') GROUP BY month ORDER BY month; [S3]. Do not average price over item rows, since that gives average item price, not AOV; report the median alongside the average because large orders skew the mean [S4]. The actual AOV values require running this query against the database.

### claude-haiku-5-5 · a02 · Як рахується частка замовлень, доставлених вчасно?

Частка вчасно доставлених замовлень (on_time_delivery_rate) — це відсоток доставлених замовлень, які дійшли до клієнта не пізніше обіцяної при покупці дати [S5]. Формула: кількість доставлених замовлень з датою доставки ≤ орієнтовної дати доставки / кількість доставлених замовлень × 100% [S2]. Порівняння робиться на рівні дня, бо order_estimated_delivery_date завжди має час 00:00; інакше доставка о 10:00 у обіцяний день рахувалася б як запізнення [S2]. Доставленими вважаються замовлення зі статусом delivered і непорожньою order_delivered_customer_date [S2]. Замовлення без дати доставки виключаються, а не рахуються як запізнілі [S1]. Late delivery rate = 100% − on-time delivery rate [S4]. SQL для розрахунку за місяцями є в документації [S4]; саме число потрібно отримати, виконавши цей запит у базі даних.

### claude-haiku-5-5 · a03 · How is CAC defined?

CAC (Customer Acquisition Cost) is how much the business spends on marketing to acquire one new customer [S2]. The formula is CAC = marketing spend / number of new customers, for the same period [S4]. A new customer is a customer_unique_id whose first valid order falls in the period, and marketing spend is all paid acquisition costs such as ads, agencies and promotions [S4]. Dividing by all customers instead of new ones understates CAC [S3].

### claude-haiku-5-5 · a04 · Який був середній чек у 2018 році?

Середній чек (AOV) — це середня сума, яку клієнт витрачає на товари в одному замовленні [S2]. Формула: AOV = GMV / кількість валідних замовлень, що мають товари; GMV рахується лише за ціною, без доставки [S3]. Для розрахунку на даних Olist використовується сума price, поділена на кількість унікальних order_id з order_items, з виключенням замовлень зі статусом canceled та unavailable [S5]. Число за 2018 рік потребує виконання цього запиту до бази даних; я не можу його запустити і не наводжу значення. Зверніть увагу: середнє може зсуватися через кілька дуже великих замовлень, тому варто подавати разом із медіаною [S1].

SQL:
SELECT date_trunc('month', o.order_purchase_timestamp)::date AS month, round(sum(oi.price) / count(DISTINCT oi.order_id), 2) AS aov FROM olist.order_items AS oi JOIN olist.orders AS o USING (order_id) WHERE o.order_status NOT IN ('canceled', 'unavailable') GROUP BY month ORDER BY month;

Для 2018 року потрібно відфільтрувати місяці цього року (наприклад, додати умову на рік у WHERE).

### claude-haiku-5-5 · a05 · Як порахувати ДРР?

Термін «ДРР» у документації може означати два різні метрики [S1][S2]. Перша: Ad-spend share (частка реклами у виручці) — частка загальної виручки, яка витрачена на рекламу; знаменник — вся виручка, включно з продажами, не пов'язаними з рекламою [S3][S1]. Друга: ACoS (Advertising Cost of Sales) — рекламні витрати відносно виручки, отриманої саме від реклами; ad-attributed revenue є знаменником [S1][S2]. Точна формула в джерелах не наведена, тож розрахунок числа потребує запиту до бази даних.

*Clarifying question:* Яку виручку брати в знаменник: всю виручку компанії (частка реклами у виручці) чи виручку, атрибутовану саме рекламі (ACoS)?

### claude-haiku-5-5 · a06 · What is our DRR and how should we track it?

«ДРР» (DRR) в документации может означать два разных показателя. Первый — доля рекламы в выручке (ad_spend_share): доля всей выручки, потраченная на рекламу; знаменатель — вся выручка, включая продажи без рекламы [S3]. Второй — ACoS (Advertising Cost of Sales): рекламные расходы, деленные на выручку, атрибутированную рекламе [S2]. Если в знаменателе выручка, атрибутированная рекламе, метрика становится ACoS [S1]. Оба показателя в Olist-данных пока не рассчитываются: в источниках data_availability = none, поэтому значение потребует данных о рекламных расходах, которых в датасете нет [S1][S2].

*Clarifying question:* Какой знаменатель вы имеете в виду: всю выручку (доля рекламы в выручке) или выручку, атрибутированную рекламе (ACoS)?

### claude-haiku-5-5 · a07 · Яка в нас конверсія сайту за 2018 рік?

Конверсію сайту за 2018 рік розрахувати неможливо: набір Olist містить лише замовлення, без даних про трафік, сесії чи відвідувачі [S4]. Формула: Conversion rate = orders / sessions × 100% [S5]. Sessions — це візити з веб-аналітики (наприклад, GA4) за той самий період і канал, а orders — валідні замовлення [S5]. Для розрахунку потрібен експорт веб-аналітики з кількістю сесій за день і каналом [S4]. Не можна порівнювати замовлення і сесії за різні періоди або різні сфери трафіку [S2].

### claude-haiku-5-5 · a08 · Calculate our customer acquisition cost for 2018.

CAC is calculated as marketing spend divided by the number of new customers for the same period [S1]. A new customer is a customer_unique_id whose first valid order falls in the period, and marketing spend covers all paid acquisition costs such as ads, agencies and promotions [S1]. The Olist dataset has no marketing spend data, so CAC for 2018 cannot be calculated from it [S5]. The number of new customers per month can be counted from Olist, so CAC could be calculated once marketing spend data is added [S5].

### claude-haiku-5-5 · a09 · What share of our revenue did we spend on advertising last year?

Ad-spend share is the share of total revenue spent on advertising: total advertising spend / total revenue × 100%, for the same period [S2]. It is defined as the share of total revenue that is spent on advertising across the whole business [S1]. The Olist dataset cannot calculate it: it contains no advertising spend data, and calculating it would require spend per day and channel from the ad platforms, while revenue is available [S3]. Therefore last year's figure cannot be computed from the Olist data.

### claude-haiku-5-5 · o09 · What is EBITDA and how is it calculated?

The provided documentation does not cover EBITDA or its calculation. The sources only describe unit economics, ad-spend share and ACoS metrics, so I can't answer this question from them.

### claude-haiku-5-5 · o10 · Що таке NPS і як його рахувати?

Документація, яка мені доступна, не містить опису NPS (Net Promoter Score), тому я не можу пояснити його визначення чи формулу за цими джерелами. Наявні джерела стосуються повторних покупок, оцінок відгуків, скасувань і частки рекламних витрат.

### claude-haiku-5-5 · o01 · What's the weather like in Kyiv tomorrow?

This question is not covered by the metric documentation, so I cannot answer it.
