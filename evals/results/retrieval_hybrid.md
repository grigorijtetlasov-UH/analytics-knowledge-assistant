# Retrieval eval: hybrid

30 questions (15 intents x en/uk), top 5 chunks, embeddings: text-embedding-3-small.

## Summary

| mode | group | n | hit@1 | hit@3 | hit@5 | MRR@5 |
|---|---|---:|---:|---:|---:|---:|
| vector | all | 30 | 0.83 | 0.90 | 0.90 | 0.86 |
| vector | en | 15 | 1.00 | 1.00 | 1.00 | 1.00 |
| vector | uk | 15 | 0.67 | 0.80 | 0.80 | 0.72 |
| vector | kind=alias | 8 | 0.88 | 0.88 | 0.88 | 0.88 |
| vector | kind=availability | 4 | 1.00 | 1.00 | 1.00 | 1.00 |
| vector | kind=name | 4 | 0.75 | 1.00 | 1.00 | 0.88 |
| vector | kind=paraphrase | 14 | 0.79 | 0.86 | 0.86 | 0.81 |
| fulltext | all | 30 | 0.37 | 0.47 | 0.53 | 0.43 |
| fulltext | en | 15 | 0.47 | 0.67 | 0.80 | 0.60 |
| fulltext | uk | 15 | 0.27 | 0.27 | 0.27 | 0.27 |
| fulltext | kind=alias | 8 | 0.75 | 0.88 | 0.88 | 0.81 |
| fulltext | kind=availability | 4 | 0.50 | 0.50 | 0.50 | 0.50 |
| fulltext | kind=name | 4 | 0.75 | 0.75 | 0.75 | 0.75 |
| fulltext | kind=paraphrase | 14 | 0.00 | 0.14 | 0.29 | 0.11 |
| hybrid | all | 30 | 0.70 | 0.90 | 0.90 | 0.78 |
| hybrid | en | 15 | 0.73 | 1.00 | 1.00 | 0.84 |
| hybrid | uk | 15 | 0.67 | 0.80 | 0.80 | 0.72 |
| hybrid | kind=alias | 8 | 0.75 | 0.88 | 0.88 | 0.81 |
| hybrid | kind=availability | 4 | 1.00 | 1.00 | 1.00 | 1.00 |
| hybrid | kind=name | 4 | 0.75 | 1.00 | 1.00 | 0.88 |
| hybrid | kind=paraphrase | 14 | 0.57 | 0.86 | 0.86 | 0.68 |

## Misses (no expected document at rank 1)

| mode | id | lang | rank | question | expected | top-3 returned |
|---|---|---|---:|---|---|---|
| vector | q01 | uk | 2 | Що мається на увазі під середнім чеком? | aov | delivery_time, aov, delivery_time |
| vector | q04 | uk | - | Скільки з чеку клієнта йде на доставку? | freight_share | delivery_time, delivery_time, delivery_time |
| vector | q05 | uk | 3 | Який відсоток замовлень у нас відміняють? | cancellation_rate | repeat_purchase_rate, repeat_purchase_rate, cancellation_rate |
| vector | q08 | uk | - | Як зрозуміти, чи задоволені клієнти? | review_score | clv, clv, clv |
| vector | q15 | uk | - | Які замовлення беремо в розрахунок продажів? | conventions | cross_sell_rate, cross_sell_rate, cross_sell_rate |
| fulltext | q01 | uk | - | Що мається на увазі під середнім чеком? | aov |  |
| fulltext | q03 | en | 2 | How often do customers buy products from different categories in one order? | cross_sell_rate | unit_economics, cross_sell_rate, unit_economics |
| fulltext | q03 | uk | - | Як часто клієнт докуповує щось з іншої категорії в тому ж замовленні? | cross_sell_rate |  |
| fulltext | q04 | en | 4 | What part of what customers pay goes to shipping? | freight_share | clv, delivery_time, delivery_time |
| fulltext | q04 | uk | - | Скільки з чеку клієнта йде на доставку? | freight_share |  |
| fulltext | q05 | en | - | What share of orders gets called off? | cancellation_rate | unit_economics, freight_share, freight_share |
| fulltext | q05 | uk | - | Який відсоток замовлень у нас відміняють? | cancellation_rate |  |
| fulltext | q07 | en | - | How long does it take for an order to reach the customer? | delivery_time | unit_economics, unit_economics, unit_economics |
| fulltext | q07 | uk | - | Скільки днів у середньому йде доставка до клієнта? | delivery_time |  |
| fulltext | q08 | en | 2 | How do we measure customer satisfaction? | review_score | clv, review_score, cac |
| fulltext | q08 | uk | - | Як зрозуміти, чи задоволені клієнти? | review_score |  |
| fulltext | q09 | en | 4 | How do we count customers who come back and buy again? | repeat_purchase_rate | clv, conventions, cac |
| fulltext | q09 | uk | - | Як порахувати, скільки клієнтів купують у нас повторно? | repeat_purchase_rate |  |
| fulltext | q11 | en | 2 | Does an average order still make money after all costs? | unit_economics | aov, unit_economics, aov |
| fulltext | q11 | uk | - | Чи заробляємо ми на середньому замовленні після всіх витрат? | unit_economics |  |
| fulltext | q12 | uk | - | Чи можна з наших даних витягнути конверсію? | conversion_rate |  |
| fulltext | q13 | uk | - | У скільки нам обходиться один новий клієнт, і чи можна це порахувати? | cac |  |
| fulltext | q15 | en | - | Which orders do we include when we report sales? | conventions | unit_economics, unit_economics, unit_economics |
| fulltext | q15 | uk | - | Які замовлення беремо в розрахунок продажів? | conventions |  |
| hybrid | q01 | uk | 2 | Що мається на увазі під середнім чеком? | aov | delivery_time, aov, delivery_time |
| hybrid | q04 | uk | - | Скільки з чеку клієнта йде на доставку? | freight_share | delivery_time, delivery_time, delivery_time |
| hybrid | q05 | en | 3 | What share of orders gets called off? | cancellation_rate | freight_share, freight_share, cancellation_rate |
| hybrid | q05 | uk | 3 | Який відсоток замовлень у нас відміняють? | cancellation_rate | repeat_purchase_rate, repeat_purchase_rate, cancellation_rate |
| hybrid | q07 | en | 2 | How long does it take for an order to reach the customer? | delivery_time | conventions, delivery_time, cac |
| hybrid | q08 | en | 2 | How do we measure customer satisfaction? | review_score | clv, review_score, clv |
| hybrid | q08 | uk | - | Як зрозуміти, чи задоволені клієнти? | review_score | clv, clv, clv |
| hybrid | q11 | en | 3 | Does an average order still make money after all costs? | unit_economics | aov, aov, unit_economics |
| hybrid | q15 | uk | - | Які замовлення беремо в розрахунок продажів? | conventions | cross_sell_rate, cross_sell_rate, cross_sell_rate |
