---
id: acos
name: Advertising Cost of Sales
aliases: [ACoS, advertising cost of sale, ROAS, return on ad spend, DRR, ДРР, ДРР по рекламі, окупність реклами, ROAS навпаки]
category: marketing
unit: "%"
direction: lower_is_better
data_availability: none
related: [ad_spend_share, cac]
---

# Advertising Cost of Sales (ACoS)

## Definition
How much advertising costs per unit of revenue that the advertising itself generated. It is
the efficiency measure of ad campaigns. ROAS is its inverse.

## Formula
```
ACoS = ad spend / revenue attributed to ads × 100%
ROAS = revenue attributed to ads / ad spend = 1 / ACoS
```
- **Revenue attributed to ads**: sales the ad platform attributes to clicks on ads
- Differs from [ad_spend_share](ad_spend_share.md), which divides by all revenue

## Calculation on Olist data
Not possible. Olist has neither ad spend nor ad attribution data.

## Interpretation
Compare ACoS with gross margin %: ACoS above margin means the ads lose money.

## Pitfalls
- Attribution windows differ between ad platforms; ACoS from two platforms is not comparable.
- In everyday speech "ДРР" (DRR) is used both for this metric and for
  [ad_spend_share](ad_spend_share.md). When a question says only "ДРР", clarify which
  denominator is meant (revenue attributed to ads or all revenue) or explain both; do not
  assume one.
