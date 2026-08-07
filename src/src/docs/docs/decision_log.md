# Decision Log

Record of analytical and modeling decisions made in this project, and why.

---

**2026-08-07 — Dataset selection**
Chose Olist Brazilian E-Commerce (Kaggle: `olistbr/brazilian-ecommerce`) over a beginner dataset (Titanic, House Prices) because it supports genuine two-sided marketplace business questions: revenue, seller concentration risk, delivery SLA performance, and review-driven reputation effects. Sourced via a GitHub mirror (`Ganesh7699/Brazilian-E-Commerce-OList`) since the environment cannot authenticate to Kaggle directly.

**2026-08-07 — Database choice: SQLite over flat CSVs**
Loaded all 10 raw tables into a single SQLite file (`olist.db`) rather than working from pandas CSV reads directly. This mirrors how a real analytics team would work (a queryable warehouse layer, not scattered files) and makes the SQL KPI layer reusable and auditable.

**2026-08-07 — KPI order-status filtering**
GMV and revenue KPIs by default exclude `canceled` and `unavailable` order statuses, since these never represent realized revenue. Delivery-performance KPIs are scoped to `delivered` orders only, since `order_delivered_customer_date` is null for anything else — including it would silently drop rows and bias the on-time rate.

**2026-08-07 — Delay-risk model: metric choice**
Initial model evaluation used default accuracy/0.5 threshold and looked good (92% accuracy) but was actually useless: it caught only ~5% of truly late orders, because late orders are only 8.1% of the dataset (an "always predict on-time" baseline already scores ~92% accuracy). Switched to a business-appropriate threshold chosen from the precision-recall curve, targeting ≥60% recall on the "late" class, since the cost of *missing* a genuinely late order (bad review, possible churn) is higher than the cost of a false alarm (Ops double-checks a shipment that was fine).

**2026-08-07 — Seller historical late-rate feature**
Added a feature representing each seller's own historical late-delivery rate, computed **only from the training split** and shrunk toward the global mean for low-volume sellers (Bayesian shrinkage, k=10) to avoid overfitting on sellers with very few orders. This is the single most important feature in the final model (35% of total importance), but its addition barely moved overall ROC-AUC (0.733 → 0.735) — indicating that much of the remaining unexplained variance is driven by macro effects like seasonal demand spikes (e.g., November 2017 order volume nearly doubles vs. surrounding months), not seller-specific quality alone. Documented as a limitation and a direction for future data enrichment (carrier capacity data is not present in this dataset).

**2026-08-07 — No customer-level churn label available**
The dataset has no subscription/relationship structure — each `customer_id` is effectively order-scoped and `customer_unique_id` is the true repeat-customer key. A seller-churn or buyer-churn model was scoped as a candidate next deliverable but not built in this iteration; flagged in README as a next step.
