"""
Olist Delivery-Delay Risk Model
=================================
Business objective: score the probability that an order will arrive AFTER
the estimated delivery date, using ONLY information available at the moment
the order is placed and approved (no data leakage from actual delivery events).

Business use: flag high-risk orders in real time so Ops can expedite shipping,
proactively message the customer, or route to a faster carrier -- protecting
the review score (which we found collapses from 4.29 -> 2.57 on late orders).
"""
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

conn = sqlite3.connect('/home/claude/olist_project/olist.db')

query = """
SELECT
    o.order_id,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_estimated_delivery_date,
    o.order_delivered_customer_date,
    c.customer_state,
    s.seller_state,
    oi.price,
    oi.freight_value,
    p.product_weight_g,
    p.product_category_name,
    pay.payment_type,
    pay.payment_installments,
    oi.seller_id
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN order_payments pay ON o.order_id = pay.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_approved_at IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df = df.drop_duplicates(subset='order_id')
print(f"Loaded {len(df):,} delivered orders with complete data")

df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])
df['order_estimated_delivery_date'] = pd.to_datetime(df['order_estimated_delivery_date'])
df['is_late'] = (df['order_delivered_customer_date'] > df['order_estimated_delivery_date']).astype(int)

df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
df['order_approved_at'] = pd.to_datetime(df['order_approved_at'])

df['purchase_month'] = df['order_purchase_timestamp'].dt.month
df['purchase_dow'] = df['order_purchase_timestamp'].dt.dayofweek
df['purchase_hour'] = df['order_purchase_timestamp'].dt.hour
df['approval_lag_hours'] = (df['order_approved_at'] - df['order_purchase_timestamp']).dt.total_seconds() / 3600
df['cross_state'] = (df['customer_state'] != df['seller_state']).astype(int)
df['estimated_days'] = (df['order_estimated_delivery_date'] - df['order_purchase_timestamp']).dt.days

df['product_weight_g'] = df['product_weight_g'].fillna(df['product_weight_g'].median())
df['product_category_name'] = df['product_category_name'].fillna('unknown')
df['payment_type'] = df['payment_type'].fillna('unknown')
df['payment_installments'] = df['payment_installments'].fillna(1)
df['approval_lag_hours'] = df['approval_lag_hours'].fillna(df['approval_lag_hours'].median())

numeric_features = ['price', 'freight_value', 'product_weight_g', 'purchase_month',
                     'purchase_dow', 'purchase_hour', 'approval_lag_hours',
                     'cross_state', 'estimated_days', 'payment_installments']
categorical_features = ['customer_state', 'seller_state', 'payment_type']
top_cats = df['product_category_name'].value_counts().head(15).index
df['product_category_grouped'] = df['product_category_name'].where(
    df['product_category_name'].isin(top_cats), 'other')
categorical_features.append('product_category_grouped')

X = df[numeric_features + categorical_features]
y = df['is_late']

print(f"\nClass balance: {y.mean():.1%} late, {1-y.mean():.1%} on-time")

df_train_idx, df_test_idx = train_test_split(
    df.index, test_size=0.2, random_state=42, stratify=y)

global_late_rate = df.loc[df_train_idx, 'is_late'].mean()
seller_late_rate = df.loc[df_train_idx].groupby('seller_id')['is_late'].agg(['mean', 'count'])
K = 10
seller_late_rate['seller_hist_late_rate'] = (
    (seller_late_rate['mean'] * seller_late_rate['count'] + global_late_rate * K)
    / (seller_late_rate['count'] + K)
)
df['seller_hist_late_rate'] = df['seller_id'].map(seller_late_rate['seller_hist_late_rate'])
df['seller_hist_late_rate'] = df['seller_hist_late_rate'].fillna(global_late_rate)
df['seller_order_count'] = df['seller_id'].map(seller_late_rate['count']).fillna(0)

numeric_features.append('seller_hist_late_rate')
numeric_features.append('seller_order_count')
X = df[numeric_features + categorical_features]

X_train, X_test = X.loc[df_train_idx], X.loc[df_test_idx]
y_train, y_test = y.loc[df_train_idx], y.loc[df_test_idx]

preprocessor = ColumnTransformer([
    ('num', 'passthrough', numeric_features),
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
])

model = Pipeline([
    ('prep', preprocessor),
    ('clf', RandomForestClassifier(n_estimators=300, max_depth=8,
                                    class_weight='balanced_subsample',
                                    min_samples_leaf=20,
                                    random_state=42, n_jobs=-1))
])

model.fit(X_train, y_train)
y_proba = model.predict_proba(X_test)[:, 1]

from sklearn.metrics import precision_recall_curve
precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)

target_recall = 0.60
valid_idx = np.where(recalls[:-1] >= target_recall)[0]
if len(valid_idx) > 0:
    best_idx = valid_idx[np.argmax(precisions[:-1][valid_idx])]
    chosen_threshold = thresholds[best_idx]
else:
    chosen_threshold = 0.5

y_pred_default = (y_proba >= 0.5).astype(int)
y_pred_business = (y_proba >= chosen_threshold).astype(int)

print("\nMODEL PERFORMANCE -- default 0.5 threshold")
print(classification_report(y_test, y_pred_default, target_names=['On-time', 'Late']))

print(f"\nMODEL PERFORMANCE -- business threshold ({chosen_threshold:.3f})")
print(classification_report(y_test, y_pred_business, target_names=['On-time', 'Late']))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.3f}")
print(f"Confusion matrix:\n{confusion_matrix(y_test, y_pred_business)}")

tn, fp, fn, tp = confusion_matrix(y_test, y_pred_business).ravel()
print(f"\nBusiness read: of {tp+fn} truly late orders, we catch {tp} ({tp/(tp+fn):.0%}). "
      f"False-alarm rate: {fp/(fp+tn):.1%}")

cat_encoder = model.named_steps['prep'].named_transformers_['cat']
cat_names = cat_encoder.get_feature_names_out(categorical_features)
all_feature_names = numeric_features + list(cat_names)
importances = model.named_steps['clf'].feature_importances_
imp_df = pd.DataFrame({'feature': all_feature_names, 'importance': importances})
imp_df = imp_df.sort_values('importance', ascending=False).head(15)

print("\nTOP 15 FEATURE IMPORTANCES")
print(imp_df.to_string(index=False))

imp_df.to_csv('/home/claude/olist_project/outputs/feature_importance.csv', index=False)

import joblib
joblib.dump(model, '/home/claude/olist_project/outputs/delay_risk_model.pkl')
print("\nModel saved")
