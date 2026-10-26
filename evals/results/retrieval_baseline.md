# Retrieval eval: baseline

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

## Misses (no expected document at rank 1)

| mode | id | lang | rank | question | expected | top-3 returned |
|---|---|---|---:|---|---|---|
| vector | q01 | uk | 2 | Що мається на увазі під середнім чеком? | aov | delivery_time, aov, delivery_time |
| vector | q04 | uk | - | Скільки з чеку клієнта йде на доставку? | freight_share | delivery_time, delivery_time, delivery_time |
| vector | q05 | uk | 3 | Який відсоток замовлень у нас відміняють? | cancellation_rate | repeat_purchase_rate, repeat_purchase_rate, cancellation_rate |
| vector | q08 | uk | - | Як зрозуміти, чи задоволені клієнти? | review_score | clv, clv, clv |
| vector | q15 | uk | - | Які замовлення беремо в розрахунок продажів? | conventions | cross_sell_rate, cross_sell_rate, cross_sell_rate |
