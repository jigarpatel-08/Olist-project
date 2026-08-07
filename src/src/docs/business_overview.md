# Business Overview

## Company: Olist (Brazilian E-Commerce Marketplace)

**Industry:** Multi-sided e-commerce marketplace (comparable to Amazon Marketplace or Mercado Livre's third-party program, not a direct retailer).

**Business model:** Olist does not hold inventory. Small and medium Brazilian sellers list products through Olist, which provides the storefront experience and connects sellers to major marketplaces (Mercado Livre, Americanas, B2W, and others). Revenue comes from commission/subscription fees charged to sellers per transaction, not from product margin.

This is the single most important framing for any analysis of this dataset: Olist's growth depends on **platform health**, not inventory turnover. That means the business questions that matter are two-sided — buyer experience AND seller retention — not just "sales are up."

## Customers (two distinct groups)

| Group | Who they are | Success metric |
|---|---|---|
| **Buyers** | Brazilian consumers ordering products online | Fast, reliable delivery; product matches expectations |
| **Sellers** | Small/independent merchants across Brazil | Order volume, visibility, low platform friction, timely payout |

## Revenue model

Commission per sale + listing/subscription fees. Three independent levers drive revenue:
1. Number of active sellers retained
2. Volume moved per seller
3. Take-rate per transaction

A CEO evaluating "revenue is up" would ask **which of these three** moved, because each implies a different strategic response.

## Key structural risk identified in this dataset

The top 10% of sellers (by revenue) generate **67.6%** of total platform GMV. This is a concentration risk: if even a handful of top sellers churn to a competing marketplace, Olist's revenue is materially exposed. Any seller-retention or seller-experience initiative should be evaluated first against this top decile.

## Departments / functions relevant to this dataset

- **Seller Operations** — onboarding, retention, support
- **Buyer/Customer Experience** — support, reviews, complaints
- **Logistics & Fulfillment** — Olist orchestrates delivery SLAs; sellers ship, so this is coordination, not warehousing
- **Marketing/Growth** — buyer and seller acquisition (see `marketing_leads` / `closed_deals` tables)
- **Finance** — commission tracking, seller payouts
- **Product/Data** — platform experience, risk scoring, recommendations

## Competitors

Mercado Livre (dominant), Amazon Brazil, Americanas, Magazine Luiza, B2W. Notably, many Olist sellers also sell on these platforms simultaneously — Olist is partly a competitor and partly an enabler/integration layer for the same merchants.
