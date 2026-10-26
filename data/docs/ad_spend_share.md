---
id: ad_spend_share
name: Ad-spend share
aliases: [advertising cost ratio, ad spend to revenue, marketing cost share, DRR, ДРР, TACoS, частка реклами у виручці, доля рекламы, "% на рекламу"]
category: marketing
unit: "%"
direction: lower_is_better
data_availability: none
related: [acos, cac, unit_economics]
---

# Ad-spend share

## Definition
The share of total revenue that is spent on advertising. It shows how much of every sale
goes to paid promotion across the whole business, including sales not driven by ads.

## Formula
```
Ad-spend share = total advertising spend / total revenue × 100%, for the same period
```
- **Total revenue**: [gmv](gmv.md) or [realized_revenue](realized_revenue.md); state which
- Differs from [acos](acos.md), which divides by revenue **attributed to ads** only

## Calculation on Olist data
Not possible. Olist has no advertising spend data. It would need spend per day and channel
from the ad platforms; revenue is available.

## Interpretation
Compare with contribution margin: if ad-spend share is higher, sales are unprofitable.

## Pitfalls
- Using ad-attributed revenue in the denominator turns it into ACoS.
- In everyday speech "ДРР" (DRR) is used both for this metric and for [acos](acos.md).
  When a question says only "ДРР", clarify which denominator is meant (all revenue or
  revenue attributed to ads) or explain both; do not assume one.
