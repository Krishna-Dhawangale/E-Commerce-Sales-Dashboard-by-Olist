# ============================================================
# OLIST E-COMMERCE DASHBOARD PROJECT
# Step 1: Load, Explore & Clean All 9 CSV Files
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── Set your folder path where CSVs are saved ───────────────
DATA_PATH = "your_folder_path_here/"   # e.g. "C:/Users/YourName/olist/"

# ============================================================
# 1. LOAD ALL 9 FILES
# ============================================================

customers   = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\olist_customers_dataset.csv")
geolocation = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\olist_geolocation_dataset.csv")
order_items = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\olist_order_items_dataset.csv")
payments    = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\olist_order_payments_dataset.csv")
reviews     = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\olist_order_reviews_dataset.csv")
orders      = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\olist_orders_dataset.csv")
products    = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\olist_products_dataset.csv")
sellers     = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\olist_sellers_dataset.csv")
category    = pd.read_csv("C:\\Users\\a\\Desktop\\E-Commerce Sales Dashboard by Olist\\product_category_name_translation.csv")

print("✅ All 9 files loaded successfully!\n")

# ============================================================
# 2. QUICK SHAPE & COLUMN OVERVIEW
# ============================================================

datasets = {
    "customers":   customers,
    "geolocation": geolocation,
    "order_items": order_items,
    "payments":    payments,
    "reviews":     reviews,
    "orders":      orders,
    "products":    products,
    "sellers":     sellers,
    "category":    category,
}

print("=" * 50)
print(f"{'Dataset':<15} {'Rows':>8} {'Columns':>8}")
print("=" * 50)
for name, df in datasets.items():
    print(f"{name:<15} {df.shape[0]:>8,} {df.shape[1]:>8}")
print("=" * 50)

# ============================================================
# 3. NULL VALUE CHECK (very important for data cleaning)
# ============================================================

print("\n📋 NULL VALUES PER DATASET:")
print("-" * 40)
for name, df in datasets.items():
    nulls = df.isnull().sum().sum()
    if nulls > 0:
        print(f"\n⚠️  {name} — {nulls} total nulls:")
        print(df.isnull().sum()[df.isnull().sum() > 0])
    else:
        print(f"✅ {name} — No nulls")

# ============================================================
# 4. FIX DATE COLUMNS IN ORDERS TABLE
# ============================================================

date_cols = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date'
]

for col in date_cols:
    orders[col] = pd.to_datetime(orders[col])

# Extract useful time features
orders['year']          = orders['order_purchase_timestamp'].dt.year
orders['month']         = orders['order_purchase_timestamp'].dt.month
orders['month_name']    = orders['order_purchase_timestamp'].dt.strftime('%b')
orders['quarter']       = orders['order_purchase_timestamp'].dt.quarter
orders['day_of_week']   = orders['order_purchase_timestamp'].dt.day_name()
orders['delivery_days'] = (
    orders['order_delivered_customer_date'] -
    orders['order_purchase_timestamp']
).dt.days

print("\n✅ Date columns parsed. Delivery days column added.")

# ============================================================
# 5. MERGE CORE TABLES INTO ONE MASTER DATAFRAME
# ============================================================

# Step 1: orders + customers
df = orders.merge(customers, on='customer_id', how='left')

# Step 2: + order_items
df = df.merge(order_items, on='order_id', how='left')

# Step 3: + payments (aggregate by order — sum payment value)
pay_agg = payments.groupby('order_id').agg(
    payment_value=('payment_value', 'sum'),
    payment_type =('payment_type',  lambda x: x.mode()[0])
).reset_index()
df = df.merge(pay_agg, on='order_id', how='left')

# Step 4: + products
df = df.merge(products, on='product_id', how='left')

# Step 5: + English category names
df = df.merge(category, on='product_category_name', how='left')

# Step 6: + sellers
df = df.merge(sellers, on='seller_id', how='left')

print(f"\n✅ Master dataframe created: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ============================================================
# 6. BASIC BUSINESS METRICS (quick sanity check)
# ============================================================

# Only delivered orders for revenue analysis
delivered = df[df['order_status'] == 'delivered'].copy()

total_revenue   = delivered['payment_value'].sum()
total_orders    = delivered['order_id'].nunique()
total_customers = delivered['customer_unique_id'].nunique()
avg_order_value = total_revenue / total_orders
avg_delivery    = delivered['delivery_days'].mean()

print("\n" + "=" * 45)
print("       BUSINESS OVERVIEW (Delivered Orders)")
print("=" * 45)
print(f"  Total Revenue      : R$ {total_revenue:>12,.2f}")
print(f"  Total Orders       : {total_orders:>14,}")
print(f"  Unique Customers   : {total_customers:>14,}")
print(f"  Avg Order Value    : R$ {avg_order_value:>12,.2f}")
print(f"  Avg Delivery Days  : {avg_delivery:>14.1f}")
print("=" * 45)

# ============================================================
# 7. ORDER STATUS DISTRIBUTION
# ============================================================

print("\n📦 ORDER STATUS BREAKDOWN:")
status_counts = df['order_status'].value_counts()
for status, count in status_counts.items():
    pct = count / len(df) * 100
    print(f"  {status:<25} {count:>7,}  ({pct:.1f}%)")

# ============================================================
# 8. TOP 10 PRODUCT CATEGORIES BY REVENUE
# ============================================================

top_cats = (
    delivered.groupby('product_category_name_english')['payment_value']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
top_cats.columns = ['category', 'revenue']
top_cats['revenue_pct'] = (top_cats['revenue'] / total_revenue * 100).round(1)

print("\n🏆 TOP 10 CATEGORIES BY REVENUE:")
print(f"  {'Category':<35} {'Revenue (R$)':>14} {'%':>6}")
print("  " + "-" * 57)
for _, row in top_cats.iterrows():
    print(f"  {str(row['category']):<35} {row['revenue']:>14,.0f} {row['revenue_pct']:>5.1f}%")

# ============================================================
# 9. MONTHLY REVENUE TREND
# ============================================================

monthly = (
    delivered.groupby(['year', 'month'])['payment_value']
    .sum()
    .reset_index()
    .sort_values(['year', 'month'])
)
monthly['period'] = monthly['year'].astype(str) + '-' + monthly['month'].astype(str).str.zfill(2)

print("\n📈 MONTHLY REVENUE TREND (first 6 months shown):")
print(monthly[['period', 'payment_value']].head(6).to_string(index=False))

# ============================================================
# 10. TOP 5 STATES BY REVENUE
# ============================================================

top_states = (
    delivered.groupby('customer_state')['payment_value']
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)
print("\n🗺️  TOP 5 STATES BY REVENUE:")
for _, row in top_states.iterrows():
    print(f"  {row['customer_state']}  →  R$ {row['payment_value']:,.0f}")

# ============================================================
# 11. QUICK VISUALISATION — Revenue by Category (bar chart)
# ============================================================

plt.figure(figsize=(12, 5))
sns.barplot(data=top_cats, x='revenue', y='category', palette='Blues_r')
plt.title('Top 10 Product Categories by Revenue', fontsize=14, fontweight='bold')
plt.xlabel('Total Revenue (R$)')
plt.ylabel('')
plt.tight_layout()
plt.savefig('top_categories_revenue.png', dpi=150)
plt.show()
print("\n✅ Chart saved as 'top_categories_revenue.png'")

# ============================================================
# 12. SAVE MASTER DATAFRAME FOR NEXT STEPS
# ============================================================

df.to_csv('olist_master.csv', index=False)
delivered.to_csv('olist_delivered.csv', index=False)

print("\n✅ olist_master.csv saved   — use for all future analysis")
print("✅ olist_delivered.csv saved — use for revenue & RFM analysis")
print("\n🎉 Step 1 Complete! You're ready for EDA & SQL analysis.")