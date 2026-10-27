# Retrieval eval: drr_acos_alias

> **Note.** Same as retrieval_uk_aliases, plus aliases DRR/ДРР added to acos (milestone 5) so that get_metric_definition returns both metrics for «ДРР».

30 questions (15 intents x en/uk), top 5 chunks, embeddings: text-embedding-3-small.

## Summary

| mode | group | n | hit@1 | hit@3 | hit@5 | MRR@5 |
|---|---|---:|---:|---:|---:|---:|
| vector | all | 30 | 0.83 | 0.97 | 0.97 | 0.89 |
| vector | en | 15 | 1.00 | 1.00 | 1.00 | 1.00 |
| vector | uk | 15 | 0.67 | 0.93 | 0.93 | 0.79 |
| vector | kind=alias | 8 | 0.88 | 0.88 | 0.88 | 0.88 |
| vector | kind=availability | 4 | 1.00 | 1.00 | 1.00 | 1.00 |
| vector | kind=name | 4 | 1.00 | 1.00 | 1.00 | 1.00 |
| vector | kind=paraphrase | 14 | 0.71 | 1.00 | 1.00 | 0.85 |
| hybrid | all | 30 | 0.67 | 0.83 | 0.87 | 0.74 |
| hybrid | en | 15 | 0.80 | 0.93 | 1.00 | 0.87 |
| hybrid | uk | 15 | 0.53 | 0.73 | 0.73 | 0.60 |
| hybrid | kind=alias | 8 | 0.75 | 0.88 | 0.88 | 0.81 |
| hybrid | kind=availability | 4 | 0.75 | 1.00 | 1.00 | 0.83 |
| hybrid | kind=name | 4 | 0.75 | 1.00 | 1.00 | 0.83 |
| hybrid | kind=paraphrase | 14 | 0.57 | 0.71 | 0.79 | 0.64 |

## Misses (no expected document at rank 1)

| mode | id | lang | rank | question | expected | top-3 returned |
|---|---|---|---:|---|---|---|
| vector | q04 | uk | 2 | Скільки з чеку клієнта йде на доставку? | freight_share | delivery_time, freight_share, delivery_time |
| vector | q05 | uk | 2 | Який відсоток замовлень у нас відміняють? | cancellation_rate | repeat_purchase_rate, cancellation_rate, repeat_purchase_rate |
| vector | q08 | uk | - | Як зрозуміти, чи задоволені клієнти? | review_score | clv, clv, clv |
| vector | q11 | uk | 2 | Чи заробляємо ми на середньому замовленні після всіх витрат? | unit_economics | aov, unit_economics, freight_share |
| vector | q15 | uk | 3 | Які замовлення беремо в розрахунок продажів? | conventions | cross_sell_rate, repeat_purchase_rate, conventions |
| hybrid | q01 | uk | 3 | Що мається на увазі під середнім чеком? | aov | conventions, ad_spend_share, aov |
| hybrid | q03 | uk | 3 | Як часто клієнт докуповує щось з іншої категорії в тому ж замовленні? | cross_sell_rate | conversion_rate, conversion_rate, cross_sell_rate |
| hybrid | q05 | en | 3 | What share of orders gets called off? | cancellation_rate | freight_share, freight_share, cancellation_rate |
| hybrid | q05 | uk | - | Який відсоток замовлень у нас відміняють? | cancellation_rate | cross_sell_rate, cross_sell_rate, ad_spend_share |
| hybrid | q07 | en | 4 | How long does it take for an order to reach the customer? | delivery_time | conventions, unit_economics, unit_economics |
| hybrid | q08 | en | 2 | How do we measure customer satisfaction? | review_score | clv, review_score, repeat_purchase_rate |
| hybrid | q08 | uk | - | Як зрозуміти, чи задоволені клієнти? | review_score | clv, clv, clv |
| hybrid | q09 | uk | - | Як порахувати, скільки клієнтів купують у нас повторно? | repeat_purchase_rate | conversion_rate, conversion_rate, conversion_rate |
| hybrid | q13 | uk | 3 | У скільки нам обходиться один новий клієнт, і чи можна це порахувати? | cac | conversion_rate, ad_spend_share, cac |
| hybrid | q15 | uk | - | Які замовлення беремо в розрахунок продажів? | conventions | aov, aov, unit_economics |
