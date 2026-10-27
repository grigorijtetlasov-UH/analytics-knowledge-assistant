# Off-topic threshold calibration

Suggested `OFF_TOPIC_MIN_SIMILARITY` = **0.22** (lowest on-topic score minus 0.05).

> **Note.** The on-topic questions were written by the same person as the docs and
> their aliases. Re-check this threshold on independently written questions in
> milestone 6 before trusting it.

| group | n | min | max |
|---|---:|---:|---:|
| on-topic | 30 | 0.270 | 0.735 |
| off-topic far | 8 | 0.081 | 0.249 |
| off-topic near | 4 | 0.314 | 0.355 |

Rejected by the threshold (no LLM call): on-topic 0/30, off-topic far 7/8, off-topic near 0/4.

## All questions, lowest score first

| score | group | id | lang | top doc | question |
|---:|---|---|---|---|---|
| 0.081 | off-topic far | o06 | uk | acos | Яка столиця Австралії? |
| 0.087 | off-topic far | o07 | en | cross_sell_rate | Recommend a good science fiction book |
| 0.115 | off-topic far | o01 | en | review_score | What's the weather like in Kyiv tomorrow? |
| 0.116 | off-topic far | o03 | en | conventions | Who won the 2018 football World Cup? |
| 0.131 | off-topic far | o05 | en | repeat_purchase_rate | How do I reverse a list in Python? |
| 0.155 | off-topic far | o02 | uk | aov | Як приготувати борщ? |
| 0.176 | off-topic far | o04 | uk | on_time_delivery_rate | Напиши вірш про осінь |
| 0.249 | off-topic far | o08 | uk | aov | Як вивчити англійську за місяць? |
| 0.270 | on-topic | q01 | uk | aov | Що мається на увазі під середнім чеком? |
| 0.314 | off-topic near | o09 | en | unit_economics | What is EBITDA and how is it calculated? |
| 0.322 | off-topic near | o12 | uk | clv | Як рахувати плинність персоналу? |
| 0.350 | on-topic | q11 | uk | aov | Чи заробляємо ми на середньому замовленні після всіх витрат? |
| 0.351 | off-topic near | o11 | en | conventions | What is the current inflation rate in Brazil? |
| 0.355 | off-topic near | o10 | uk | repeat_purchase_rate | Що таке NPS і як його рахувати? |
| 0.363 | on-topic | q08 | uk | clv | Як зрозуміти, чи задоволені клієнти? |
| 0.393 | on-topic | q08 | en | review_score | How do we measure customer satisfaction? |
| 0.400 | on-topic | q12 | uk | conversion_rate | Чи можна з наших даних витягнути конверсію? |
| 0.416 | on-topic | q04 | uk | delivery_time | Скільки з чеку клієнта йде на доставку? |
| 0.420 | on-topic | q05 | uk | repeat_purchase_rate | Який відсоток замовлень у нас відміняють? |
| 0.442 | on-topic | q15 | en | conventions | Which orders do we include when we report sales? |
| 0.444 | on-topic | q13 | uk | cac | У скільки нам обходиться один новий клієнт, і чи можна це порахувати? |
| 0.446 | on-topic | q03 | uk | cross_sell_rate | Як часто клієнт докуповує щось з іншої категорії в тому ж замовленні? |
| 0.456 | on-topic | q15 | uk | cross_sell_rate | Які замовлення беремо в розрахунок продажів? |
| 0.470 | on-topic | q04 | en | freight_share | What part of what customers pay goes to shipping? |
| 0.484 | on-topic | q07 | uk | delivery_time | Скільки днів у середньому йде доставка до клієнта? |
| 0.485 | on-topic | q10 | en | clv | How is LTV calculated? |
| 0.498 | on-topic | q07 | en | delivery_time | How long does it take for an order to reach the customer? |
| 0.511 | on-topic | q11 | en | unit_economics | Does an average order still make money after all costs? |
| 0.514 | on-topic | q10 | uk | clv | Як рахувати LTV клієнта? |
| 0.524 | on-topic | q09 | uk | repeat_purchase_rate | Як порахувати, скільки клієнтів купують у нас повторно? |
| 0.525 | on-topic | q06 | en | on_time_delivery_rate | How is OTD measured? |
| 0.527 | on-topic | q06 | uk | on_time_delivery_rate | Як ми міряємо OTD? |
| 0.538 | on-topic | q13 | en | cac | Can we work out how much it costs to acquire a customer? |
| 0.550 | on-topic | q05 | en | cancellation_rate | What share of orders gets called off? |
| 0.560 | on-topic | q03 | en | cross_sell_rate | How often do customers buy products from different categories in one order? |
| 0.577 | on-topic | q09 | en | repeat_purchase_rate | How do we count customers who come back and buy again? |
| 0.591 | on-topic | q02 | uk | gmv | Чим GMV відрізняється від фактичної виручки? |
| 0.619 | on-topic | q12 | en | conversion_rate | Can we calculate conversion rate from our data? |
| 0.647 | on-topic | q14 | en | acos | What is DRR and how is it different from ACoS? |
| 0.653 | on-topic | q14 | uk | acos | Що таке ДРР і чим він відрізняється від ACoS? |
| 0.720 | on-topic | q01 | en | aov | What is average order value? |
| 0.735 | on-topic | q02 | en | realized_revenue | What's the difference between GMV and realized revenue? |
