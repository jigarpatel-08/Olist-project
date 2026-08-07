"""
Builds olist.db from the raw CSV files in data/.
Run this after placing the Olist CSVs in data/ (see README for download link).
"""
import sqlite3
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'olist.db')

TABLES = {
    'customers': 'olist_customers_dataset.csv',
    'orders': 'olist_orders_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'order_payments': 'olist_order_payments_dataset.csv',
    'order_reviews': 'olist_order_reviews_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'sellers': 'olist_sellers_dataset.csv',
    'category_translation': 'product_category_name_translation.csv',
    'marketing_leads': 'olist_marketing_qualified_leads_dataset.csv',
    'closed_deals': 'olist_closed_deals_dataset.csv',
}

def build_db():
    conn = sqlite3.connect(DB_PATH)
    for table_name, filename in TABLES.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"WARNING: {filename} not found in data/, skipping {table_name}")
            continue
        df = pd.read_csv(path)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"{table_name}: {len(df):,} rows loaded")
    conn.close()
    print(f"\nDatabase built at {DB_PATH}")

if __name__ == '__main__':
    build_db()
