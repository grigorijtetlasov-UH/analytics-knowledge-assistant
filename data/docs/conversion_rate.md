---
id: conversion_rate
name: Conversion rate
aliases: [CR, conversion, session conversion, visitor to order rate, конверсія, конверсия сайта, "% з сесій у замовлення"]
category: marketing
unit: "%"
direction: higher_is_better
data_availability: none
related: [aov, cac, ad_spend_share]
---

# Conversion rate

## Definition
The share of website or app visits that end with an order. Together with traffic and AOV it
explains revenue: revenue = sessions × conversion rate × AOV.

## Formula
```
Conversion rate = orders / sessions × 100%
```
- **Sessions**: visits from web analytics (e.g. GA4), for the same period and channel
- **Orders**: valid orders, see [conventions](conventions.md)

## Calculation on Olist data
Not possible. Olist contains orders only; there is no traffic, session or visitor data. It
would need a web analytics export with sessions per day and channel.

## Interpretation
Compare by channel and device; blended conversion hides the differences.

## Pitfalls
- Orders and sessions must cover the same period and the same traffic scope.
