# ============================================================
# OLIST E-COMMERCE DASHBOARD PROJECT
# Step 2: Exploratory Data Analysis (EDA)
# 10+ Professional Charts for Dashboard & GitHub README
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── Style settings ───────────────────────────────────────────
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'figure.dpi'      : 150,
    'axes.titlesize'  : 14,
    'axes.titleweight': 'bold',
    'axes.labelsize'  : 11,
    'xtick.labelsize' : 10,
    'ytick.labelsize' : 10,
    'figure.facecolor': 'white',
    'axes.facecolor'  : '#f9f9f9',
})
BLUE   = '#2196F3'
GREEN  = '#4CAF50'
ORANGE = '#FF9800'
RED    = '#F44336'
PURPLE = '#9C27B0'

# ── Load saved files ─────────────────────────────────────────
print("Loading data...")
df        = pd.read_csv('olist_master.csv',    low_memory=False)
delivered = pd.read_csv('olist_delivered.csv', low_memory=False)

# Re-parse date columns
for col in ['order_purchase_timestamp', 'order_delivered_customer_date',
            'order_estimated_delivery_date']:
    df[col]        = pd.to_datetime(df[col], errors='coerce')
    delivered[col] = pd.to_datetime(delivered[col], errors='coerce')

delivered['delivery_days'] = (
    delivered['order_delivered_customer_date'] -
    delivered['order_purchase_timestamp']
).dt.days

delivered['year']       = delivered['order_purchase_timestamp'].dt.year
delivered['month']      = delivered['order_purchase_timestamp'].dt.month
delivered['month_name'] = delivered['order_purchase_timestamp'].dt.strftime('%b')
delivered['quarter']    = delivered['order_purchase_timestamp'].dt.quarter
delivered['day_of_week']= delivered['order_purchase_timestamp'].dt.day_name()

print("✅ Data loaded successfully!\n")
print(f"   Master dataframe  : {df.shape[0]:,} rows")
print(f"   Delivered orders  : {delivered.shape[0]:,} rows\n")

# ============================================================
# CHART 1 — Monthly Revenue Trend
# ============================================================
print("Generating Chart 1: Monthly Revenue Trend...")

monthly = (
    delivered.groupby(['year', 'month'])['payment_value']
    .sum().reset_index().sort_values(['year', 'month'])
)
monthly['period'] = (monthly['year'].astype(str) + '-' +
                     monthly['month'].astype(str).str.zfill(2))
# Remove incomplete months (keep only months with full data)
monthly = monthly[monthly['payment_value'] > 50000]

fig, ax = plt.subplots(figsize=(14, 5))
ax.fill_between(range(len(monthly)), monthly['payment_value'],
                alpha=0.15, color=BLUE)
ax.plot(range(len(monthly)), monthly['payment_value'],
        color=BLUE, linewidth=2.5, marker='o', markersize=5)

# Annotate peak month
peak_idx = monthly['payment_value'].idxmax()
peak_row  = monthly.loc[peak_idx]
ax.annotate(
    f"Peak\nR$ {peak_row['payment_value']/1e6:.1f}M",
    xy=(list(monthly.index).index(peak_idx), peak_row['payment_value']),
    xytext=(list(monthly.index).index(peak_idx) - 2,
            peak_row['payment_value'] * 1.05),
    arrowprops=dict(arrowstyle='->', color='gray'),
    fontsize=9, color='gray'
)

ax.set_xticks(range(len(monthly)))
ax.set_xticklabels(monthly['period'], rotation=45, ha='right', fontsize=8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e6:.1f}M'))
ax.set_title('Monthly Revenue Trend (2016 – 2018)')
ax.set_xlabel('Month')
ax.set_ylabel('Total Revenue')
plt.tight_layout()
plt.savefig('chart1_monthly_revenue.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart1_monthly_revenue.png")

# ============================================================
# CHART 2 — Top 10 Product Categories by Revenue
# ============================================================
print("Generating Chart 2: Top 10 Categories by Revenue...")

top_cats = (
    delivered.groupby('product_category_name_english')['payment_value']
    .sum().sort_values(ascending=False).head(10).reset_index()
)
top_cats.columns = ['category', 'revenue']
top_cats['category'] = top_cats['category'].str.replace('_', ' ').str.title()

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(top_cats['category'][::-1], top_cats['revenue'][::-1],
               color=sns.color_palette('Blues_r', 10))
for bar, val in zip(bars, top_cats['revenue'][::-1]):
    ax.text(bar.get_width() + 20000, bar.get_y() + bar.get_height()/2,
            f'R$ {val/1e6:.2f}M', va='center', fontsize=9)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e6:.1f}M'))
ax.set_title('Top 10 Product Categories by Revenue')
ax.set_xlabel('Total Revenue')
plt.tight_layout()
plt.savefig('chart2_top_categories.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart2_top_categories.png")

# ============================================================
# CHART 3 — Revenue by Brazilian State (Top 10)
# ============================================================
print("Generating Chart 3: Revenue by State...")

state_rev = (
    delivered.groupby('customer_state')['payment_value']
    .sum().sort_values(ascending=False).head(10).reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(state_rev['customer_state'], state_rev['payment_value'],
              color=sns.color_palette('viridis', 10))
for bar, val in zip(bars, state_rev['payment_value']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50000,
            f'R$ {val/1e6:.1f}M', ha='center', fontsize=8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e6:.1f}M'))
ax.set_title('Top 10 States by Revenue')
ax.set_xlabel('State')
ax.set_ylabel('Total Revenue')
plt.tight_layout()
plt.savefig('chart3_revenue_by_state.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart3_revenue_by_state.png")

# ============================================================
# CHART 4 — Order Status Distribution (Pie Chart)
# ============================================================
print("Generating Chart 4: Order Status Distribution...")

status = df['order_status'].value_counts()
explode = [0.05 if s == 'delivered' else 0 for s in status.index]

fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(
    status.values, labels=status.index,
    autopct='%1.1f%%', explode=explode,
    colors=sns.color_palette('Set2', len(status)),
    startangle=140, pctdistance=0.85
)
for text in autotexts:
    text.set_fontsize(9)
ax.set_title('Order Status Distribution')
plt.tight_layout()
plt.savefig('chart4_order_status.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart4_order_status.png")

# ============================================================
# CHART 5 — Delivery Time Distribution
# ============================================================
print("Generating Chart 5: Delivery Time Distribution...")

delivery_clean = delivered['delivery_days'].dropna()
delivery_clean = delivery_clean[(delivery_clean > 0) & (delivery_clean < 60)]

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(delivery_clean, bins=40, color=GREEN, edgecolor='white', alpha=0.85)
ax.axvline(delivery_clean.mean(),   color=RED,    linestyle='--',
           linewidth=2, label=f'Mean: {delivery_clean.mean():.1f} days')
ax.axvline(delivery_clean.median(), color=ORANGE, linestyle='--',
           linewidth=2, label=f'Median: {delivery_clean.median():.1f} days')
ax.set_title('Delivery Time Distribution')
ax.set_xlabel('Days to Deliver')
ax.set_ylabel('Number of Orders')
ax.legend()
plt.tight_layout()
plt.savefig('chart5_delivery_time.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart5_delivery_time.png")

# ============================================================
# CHART 6 — Review Score Distribution
# ============================================================
print("Generating Chart 6: Review Score Distribution...")

review_counts = delivered['review_score'].value_counts().sort_index()
colors = [RED, ORANGE, '#FFC107', '#8BC34A', GREEN]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(review_counts.index.astype(str), review_counts.values,
              color=colors, edgecolor='white', linewidth=1.5, width=0.6)
for bar, val in zip(bars, review_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 300,
            f'{val:,}', ha='center', fontsize=10, fontweight='bold')
ax.set_title('Customer Review Score Distribution')
ax.set_xlabel('Review Score (1 = Poor, 5 = Excellent)')
ax.set_ylabel('Number of Reviews')

avg_score = delivered['review_score'].mean()
ax.axhline(0, color='none')
fig.text(0.75, 0.82, f'Avg Score\n{avg_score:.2f} / 5.0',
         fontsize=11, ha='center',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#E3F2FD',
                   edgecolor=BLUE, linewidth=1.5))
plt.tight_layout()
plt.savefig('chart6_review_scores.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart6_review_scores.png")

# ============================================================
# CHART 7 — Payment Method Distribution
# ============================================================
print("Generating Chart 7: Payment Methods...")

pay_method = delivered['payment_type'].value_counts()
pay_method.index = pay_method.index.str.replace('_', ' ').str.title()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Pie
ax1.pie(pay_method.values, labels=pay_method.index,
        autopct='%1.1f%%', colors=sns.color_palette('Pastel1', len(pay_method)),
        startangle=90, pctdistance=0.8)
ax1.set_title('Payment Method Share')

# Bar
bars = ax2.bar(pay_method.index, pay_method.values,
               color=sns.color_palette('Pastel1', len(pay_method)),
               edgecolor='gray', linewidth=0.5)
for bar, val in zip(bars, pay_method.values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
             f'{val:,}', ha='center', fontsize=9)
ax2.set_title('Payment Method Count')
ax2.set_ylabel('Number of Orders')
ax2.tick_params(axis='x', rotation=15)

plt.suptitle('Payment Method Analysis', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('chart7_payment_methods.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart7_payment_methods.png")

# ============================================================
# CHART 8 — Orders by Day of Week
# ============================================================
print("Generating Chart 8: Orders by Day of Week...")

day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
day_counts = delivered['day_of_week'].value_counts().reindex(day_order)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(day_counts.index, day_counts.values,
              color=[BLUE if d not in ['Saturday','Sunday'] else ORANGE
                     for d in day_counts.index],
              edgecolor='white', linewidth=1)
for bar, val in zip(bars, day_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
            f'{val:,}', ha='center', fontsize=9)
ax.set_title('Orders by Day of Week\n(Blue = Weekday, Orange = Weekend)')
ax.set_xlabel('Day')
ax.set_ylabel('Number of Orders')
plt.tight_layout()
plt.savefig('chart8_orders_by_day.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart8_orders_by_day.png")

# ============================================================
# CHART 9 — Average Order Value by Category (Top 10)
# ============================================================
print("Generating Chart 9: Avg Order Value by Category...")

aov_cat = (
    delivered.groupby('product_category_name_english')['payment_value']
    .mean().sort_values(ascending=False).head(10).reset_index()
)
aov_cat.columns = ['category', 'avg_order_value']
aov_cat['category'] = aov_cat['category'].str.replace('_', ' ').str.title()

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(aov_cat['category'][::-1], aov_cat['avg_order_value'][::-1],
               color=sns.color_palette('Oranges_r', 10))
for bar, val in zip(bars, aov_cat['avg_order_value'][::-1]):
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
            f'R$ {val:.0f}', va='center', fontsize=9)
ax.set_title('Top 10 Categories by Average Order Value')
ax.set_xlabel('Average Order Value (R$)')
plt.tight_layout()
plt.savefig('chart9_avg_order_value.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart9_avg_order_value.png")

# ============================================================
# CHART 10 — Quarterly Revenue Growth
# ============================================================
print("Generating Chart 10: Quarterly Revenue Growth...")

quarterly = (
    delivered.groupby(['year', 'quarter'])['payment_value']
    .sum().reset_index()
)
quarterly['label'] = ('Q' + quarterly['quarter'].astype(str) +
                       ' ' + quarterly['year'].astype(str))
quarterly = quarterly[quarterly['payment_value'] > 100000]

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(quarterly['label'], quarterly['payment_value'],
              color=[BLUE if y == 2017 else GREEN if y == 2018 else ORANGE
                     for y in quarterly['year']],
              edgecolor='white', linewidth=1)
for bar, val in zip(bars, quarterly['payment_value']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20000,
            f'R$ {val/1e6:.1f}M', ha='center', fontsize=8, rotation=0)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e6:.1f}M'))
ax.set_title('Quarterly Revenue Growth')
ax.set_xlabel('Quarter')
ax.set_ylabel('Total Revenue')

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=ORANGE, label='2016'),
    Patch(facecolor=BLUE,   label='2017'),
    Patch(facecolor=GREEN,  label='2018'),
]
ax.legend(handles=legend_elements, loc='upper left')
plt.tight_layout()
plt.savefig('chart10_quarterly_revenue.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart10_quarterly_revenue.png")

# ============================================================
# CHART 11 — Late Delivery Analysis by State
# ============================================================
print("Generating Chart 11: Late Delivery Analysis...")

delivered['is_late'] = (
    delivered['order_delivered_customer_date'] >
    pd.to_datetime(delivered['order_estimated_delivery_date'])
).astype(int)

late_by_state = (
    delivered.groupby('customer_state')
    .agg(total_orders=('order_id', 'count'),
         late_orders=('is_late', 'sum'))
    .reset_index()
)
late_by_state['late_pct'] = (late_by_state['late_orders'] /
                              late_by_state['total_orders'] * 100).round(1)
late_by_state = late_by_state[late_by_state['total_orders'] >= 100]
late_by_state = late_by_state.sort_values('late_pct', ascending=False).head(10)

fig, ax = plt.subplots(figsize=(11, 5))
bars = ax.bar(late_by_state['customer_state'], late_by_state['late_pct'],
              color=[RED if p > 15 else ORANGE if p > 8 else GREEN
                     for p in late_by_state['late_pct']],
              edgecolor='white')
for bar, val in zip(bars, late_by_state['late_pct']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val}%', ha='center', fontsize=9)
ax.axhline(late_by_state['late_pct'].mean(), color='gray',
           linestyle='--', linewidth=1.5,
           label=f"Avg: {late_by_state['late_pct'].mean():.1f}%")
ax.set_title('Late Delivery Rate by State (Top 10)')
ax.set_xlabel('State')
ax.set_ylabel('Late Delivery %')
ax.legend()
plt.tight_layout()
plt.savefig('chart11_late_deliveries.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: chart11_late_deliveries.png")

# ============================================================
# SUMMARY — KEY BUSINESS INSIGHTS
# ============================================================
print("\n" + "=" * 55)
print("          KEY BUSINESS INSIGHTS FROM EDA")
print("=" * 55)

total_rev   = delivered['payment_value'].sum()
total_ord   = delivered['order_id'].nunique()
avg_del     = delivery_clean.mean()
avg_review  = delivered['review_score'].mean()
late_rate   = delivered['is_late'].mean() * 100
top_state   = delivered.groupby('customer_state')['payment_value'].sum().idxmax()
top_cat     = delivered.groupby('product_category_name_english')['payment_value'].sum().idxmax()
top_payment = delivered['payment_type'].value_counts().idxmax()

print(f"  Total Revenue          : R$ {total_rev:,.0f}")
print(f"  Total Delivered Orders : {total_ord:,}")
print(f"  Avg Delivery Time      : {avg_del:.1f} days")
print(f"  Avg Review Score       : {avg_review:.2f} / 5.0")
print(f"  Late Delivery Rate     : {late_rate:.1f}%")
print(f"  Top State by Revenue   : {top_state}")
print(f"  Top Category           : {top_cat}")
print(f"  Most Used Payment      : {top_payment}")
print("=" * 55)

print("""
📊 CHARTS GENERATED (11 total):
   chart1_monthly_revenue.png
   chart2_top_categories.png
   chart3_revenue_by_state.png
   chart4_order_status.png
   chart5_delivery_time.png
   chart6_review_scores.png
   chart7_payment_methods.png
   chart8_orders_by_day.png
   chart9_avg_order_value.png
   chart10_quarterly_revenue.png
   chart11_late_deliveries.png

🎉 Step 2 (EDA) Complete!
   Next step → SQL Analysis & RFM Segmentation
""")