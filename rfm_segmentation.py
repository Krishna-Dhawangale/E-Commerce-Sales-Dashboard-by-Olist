# ============================================================
# OLIST E-COMMERCE DASHBOARD PROJECT
# Step 4: RFM Customer Segmentation + K-Means Clustering
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'figure.dpi'      : 150,
    'axes.titlesize'  : 13,
    'axes.titleweight': 'bold',
    'figure.facecolor': 'white',
})

# ============================================================
# 1. LOAD DATA
# ============================================================
print("=" * 55)
print("  Step 4: RFM Customer Segmentation")
print("=" * 55)

delivered = pd.read_csv('olist_delivered.csv', low_memory=False)
delivered['order_purchase_timestamp'] = pd.to_datetime(
    delivered['order_purchase_timestamp'], errors='coerce')

print(f"  ✅ Delivered orders loaded: {len(delivered):,} rows\n")

# ============================================================
# 2. CALCULATE RFM VALUES
# ============================================================
print("Calculating RFM values...")

# Reference date = 1 day after last order in dataset
reference_date = delivered['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
print(f"  Reference date: {reference_date.date()}")

rfm = (
    delivered.groupby('customer_unique_id')
    .agg(
        last_purchase =('order_purchase_timestamp', 'max'),
        frequency     =('order_id',                 'nunique'),
        monetary      =('payment_value',             'sum')
    )
    .reset_index()
)

# Recency = days since last purchase
rfm['recency'] = (reference_date - rfm['last_purchase']).dt.days
rfm = rfm.drop(columns='last_purchase')
rfm['monetary'] = rfm['monetary'].round(2)

print(f"\n  RFM Table shape: {rfm.shape}")
print("\n  Sample RFM values:")
print(rfm.head(8).to_string(index=False))

# ============================================================
# 3. RFM SCORING (1–5 scale)
# ============================================================
print("\nAssigning RFM scores (1-5)...")

# Recency: lower days = better = score 5
rfm['R_score'] = pd.qcut(rfm['recency'],  q=5,
                          labels=[5,4,3,2,1], duplicates='drop').astype(int)

# Frequency: higher = better = score 5
rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'),
                          q=5, labels=[1,2,3,4,5]).astype(int)

# Monetary: higher = better = score 5
rfm['M_score'] = pd.qcut(rfm['monetary'],  q=5,
                          labels=[1,2,3,4,5], duplicates='drop').astype(int)

# Combined RFM score
rfm['RFM_score'] = (rfm['R_score'].astype(str) +
                    rfm['F_score'].astype(str) +
                    rfm['M_score'].astype(str))

rfm['RFM_total'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']

print("  ✅ RFM scores assigned")
print(f"\n  Score distribution:")
print(rfm[['R_score','F_score','M_score','RFM_total']].describe().round(2))

# ============================================================
# 4. RULE-BASED SEGMENTATION
# ============================================================
print("\nApplying rule-based segmentation...")

def assign_segment(row):
    r, f, m = row['R_score'], row['F_score'], row['M_score']
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'
    elif r >= 3 and f >= 3 and m >= 3:
        return 'Loyal Customers'
    elif r >= 3 and f <= 2:
        return 'Potential Loyalists'
    elif r <= 2 and f >= 3:
        return 'At Risk'
    elif r == 1 and f == 1:
        return 'Lost'
    elif r >= 4 and f == 1:
        return 'New Customers'
    else:
        return 'Needs Attention'

rfm['segment'] = rfm.apply(assign_segment, axis=1)

seg_summary = (
    rfm.groupby('segment')
    .agg(
        customer_count=('customer_unique_id', 'count'),
        avg_recency   =('recency',   'mean'),
        avg_frequency =('frequency', 'mean'),
        avg_monetary  =('monetary',  'mean'),
        total_revenue =('monetary',  'sum')
    )
    .round(2)
    .sort_values('total_revenue', ascending=False)
    .reset_index()
)
seg_summary['revenue_pct'] = (
    seg_summary['total_revenue'] /
    seg_summary['total_revenue'].sum() * 100
).round(1)

print("\n" + "=" * 70)
print("  SEGMENT SUMMARY")
print("=" * 70)
print(seg_summary.to_string(index=False))

# ============================================================
# 5. K-MEANS CLUSTERING (Advanced ML layer)
# ============================================================
print("\n\nRunning K-Means Clustering...")

# Use log transform to handle skew
rfm_ml = rfm[['recency', 'frequency', 'monetary']].copy()
rfm_ml['recency']   = np.log1p(rfm_ml['recency'])
rfm_ml['frequency'] = np.log1p(rfm_ml['frequency'])
rfm_ml['monetary']  = np.log1p(rfm_ml['monetary'])

# Standardize
scaler    = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm_ml)

# Find optimal K using Elbow method
inertias    = []
sil_scores  = []
k_range     = range(2, 9)

print("  Testing K values (2–8)...")
for k in k_range:
    km  = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(rfm_scaled)
    inertias.append(km.inertia_)
    sil_scores.append(silhouette_score(rfm_scaled, km.labels_))
    print(f"    K={k}  Inertia={km.inertia_:.0f}  "
          f"Silhouette={silhouette_score(rfm_scaled, km.labels_):.3f}")

# Final model with K=4
print("\n  Training final model with K=4...")
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm['cluster'] = kmeans.fit_predict(rfm_scaled)

# Label clusters by monetary value
cluster_means = rfm.groupby('cluster')['monetary'].mean().sort_values(ascending=False)
cluster_labels = {
    cluster_means.index[0]: '👑 Champions',
    cluster_means.index[1]: '💚 Loyal Customers',
    cluster_means.index[2]: '⚠️  At Risk',
    cluster_means.index[3]: '💤 Lost / Inactive',
}
rfm['cluster_label'] = rfm['cluster'].map(cluster_labels)

cluster_summary = (
    rfm.groupby('cluster_label')
    .agg(
        customer_count=('customer_unique_id', 'count'),
        avg_recency   =('recency',   'mean'),
        avg_frequency =('frequency', 'mean'),
        avg_monetary  =('monetary',  'mean'),
        total_revenue =('monetary',  'sum')
    )
    .round(2)
    .reset_index()
)
cluster_summary['revenue_pct'] = (
    cluster_summary['total_revenue'] /
    cluster_summary['total_revenue'].sum() * 100
).round(1)

print("\n" + "=" * 70)
print("  K-MEANS CLUSTER SUMMARY")
print("=" * 70)
print(cluster_summary.to_string(index=False))

# ============================================================
# 6. VISUALISATIONS — 6 RFM Charts
# ============================================================
print("\n\n📊 Generating RFM charts...")

COLORS = {
    '👑 Champions'      : '#FFD700',
    '💚 Loyal Customers': '#4CAF50',
    '⚠️  At Risk'       : '#FF9800',
    '💤 Lost / Inactive': '#F44336',
}

# ── Chart 1: Elbow Curve ─────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

ax1.plot(k_range, inertias, marker='o', color='#2196F3',
         linewidth=2.5, markersize=7)
ax1.axvline(4, color='red', linestyle='--', alpha=0.6, label='Optimal K=4')
ax1.set_title('Elbow Method — Optimal K')
ax1.set_xlabel('Number of Clusters (K)')
ax1.set_ylabel('Inertia')
ax1.legend()

ax2.plot(k_range, sil_scores, marker='s', color='#9C27B0',
         linewidth=2.5, markersize=7)
ax2.axvline(4, color='red', linestyle='--', alpha=0.6, label='Optimal K=4')
ax2.set_title('Silhouette Score — Cluster Quality')
ax2.set_xlabel('Number of Clusters (K)')
ax2.set_ylabel('Silhouette Score')
ax2.legend()

plt.suptitle('K-Means: Finding Optimal Number of Clusters',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('rfm_chart1_elbow_curve.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: rfm_chart1_elbow_curve.png")

# ── Chart 2: Customer Count per Cluster ─────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
colors  = [COLORS[c] for c in cluster_summary['cluster_label']]
bars    = ax.bar(cluster_summary['cluster_label'],
                 cluster_summary['customer_count'],
                 color=colors, edgecolor='white', linewidth=1.5, width=0.5)
for bar, val, pct in zip(bars,
                         cluster_summary['customer_count'],
                         cluster_summary['revenue_pct']):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 200,
            f'{val:,}\n({pct}% rev)',
            ha='center', fontsize=9, fontweight='bold')
ax.set_title('Customer Count & Revenue Share per Segment')
ax.set_ylabel('Number of Customers')
ax.set_xlabel('Customer Segment')
plt.tight_layout()
plt.savefig('rfm_chart2_segment_counts.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: rfm_chart2_segment_counts.png")

# ── Chart 3: Avg Monetary per Cluster ───────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(cluster_summary['cluster_label'],
              cluster_summary['avg_monetary'],
              color=colors, edgecolor='white', linewidth=1.5, width=0.5)
for bar, val in zip(bars, cluster_summary['avg_monetary']):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 5,
            f'R$ {val:.0f}', ha='center', fontsize=10, fontweight='bold')
ax.set_title('Average Spend per Customer by Segment')
ax.set_ylabel('Average Monetary Value (R$)')
ax.set_xlabel('Customer Segment')
plt.tight_layout()
plt.savefig('rfm_chart3_avg_spend.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: rfm_chart3_avg_spend.png")

# ── Chart 4: RFM Score Distribution Heatmap ─────────────────
rfm_heat = rfm.groupby(['R_score', 'F_score'])['monetary'].mean().unstack()
fig, ax  = plt.subplots(figsize=(9, 6))
sns.heatmap(rfm_heat, annot=True, fmt='.0f', cmap='YlOrRd',
            linewidths=0.5, ax=ax,
            cbar_kws={'label': 'Avg Monetary (R$)'})
ax.set_title('RFM Heatmap — Avg Spend by Recency & Frequency Score')
ax.set_xlabel('Frequency Score (1=Low, 5=High)')
ax.set_ylabel('Recency Score (1=Old, 5=Recent)')
plt.tight_layout()
plt.savefig('rfm_chart4_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: rfm_chart4_heatmap.png")

# ── Chart 5: Recency vs Monetary Scatter ────────────────────
fig, ax = plt.subplots(figsize=(11, 6))
for label, group in rfm.groupby('cluster_label'):
    sample = group.sample(min(500, len(group)), random_state=42)
    ax.scatter(sample['recency'], sample['monetary'],
               label=label, alpha=0.5, s=20,
               color=COLORS.get(label, 'gray'))
ax.set_title('Customer Segments — Recency vs Monetary Value')
ax.set_xlabel('Recency (Days since last purchase)')
ax.set_ylabel('Total Spend (R$)')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x:,.0f}'))
ax.legend(title='Segment', fontsize=9)
plt.tight_layout()
plt.savefig('rfm_chart5_scatter.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: rfm_chart5_scatter.png")

# ── Chart 6: Revenue Contribution Pie ───────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(
    cluster_summary['total_revenue'],
    labels    =cluster_summary['cluster_label'],
    autopct   ='%1.1f%%',
    colors    =colors,
    startangle=140,
    pctdistance=0.8,
    wedgeprops=dict(edgecolor='white', linewidth=2)
)
for t in autotexts:
    t.set_fontsize(10)
    t.set_fontweight('bold')
ax.set_title('Revenue Contribution by Customer Segment')
plt.tight_layout()
plt.savefig('rfm_chart6_revenue_pie.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: rfm_chart6_revenue_pie.png")

# ============================================================
# 7. SAVE RFM OUTPUT
# ============================================================
rfm.to_csv('olist_rfm.csv', index=False)
print("\n✅ RFM data saved as 'olist_rfm.csv'")

# ============================================================
# 8. BUSINESS RECOMMENDATIONS FROM RFM
# ============================================================
print("\n" + "=" * 55)
print("  BUSINESS RECOMMENDATIONS FROM RFM")
print("=" * 55)

for _, row in cluster_summary.iterrows():
    seg   = row['cluster_label']
    count = int(row['customer_count'])
    rev   = row['revenue_pct']
    print(f"\n  {seg}")
    print(f"  {count:,} customers — {rev}% of revenue")
    if 'Champions' in seg:
        print("  → Reward with loyalty program & early access offers")
        print("  → Upsell premium products — highest conversion chance")
    elif 'Loyal' in seg:
        print("  → Send personalized recommendations")
        print("  → Offer referral bonuses to grow word-of-mouth")
    elif 'Risk' in seg:
        print("  → Send win-back email with discount coupon")
        print("  → Investigate what caused drop in purchases")
    elif 'Lost' in seg:
        print("  → Low priority — only target with very low-cost campaigns")
        print("  → Consider re-engagement survey to understand churn reason")

print("\n" + "=" * 55)
print("""
  6 RFM Charts saved:
  ✅ rfm_chart1_elbow_curve.png
  ✅ rfm_chart2_segment_counts.png
  ✅ rfm_chart3_avg_spend.png
  ✅ rfm_chart4_heatmap.png
  ✅ rfm_chart5_scatter.png
  ✅ rfm_chart6_revenue_pie.png

  RFM data saved: olist_rfm.csv

""")