# ============================================================
# QUICK FIX — Add review_score to olist_delivered.csv
# Run this ONCE, then re-run olist_eda.py normally
# ============================================================

import pandas as pd

print("Loading files...")

delivered = pd.read_csv('olist_delivered.csv', low_memory=False)
reviews   = pd.read_csv('olist_order_reviews_dataset.csv')

print(f"  delivered shape before : {delivered.shape}")

# Keep only one review per order (some orders have multiple reviews)
reviews_clean = (
    reviews[['order_id', 'review_score']]
    .drop_duplicates(subset='order_id', keep='last')
)

# Merge review_score into delivered
delivered = delivered.merge(reviews_clean, on='order_id', how='left')

print(f"  delivered shape after  : {delivered.shape}")
print(f"  review_score nulls     : {delivered['review_score'].isnull().sum()}")
print(f"  review_score sample    : {delivered['review_score'].value_counts().sort_index().to_dict()}")

# Save back
delivered.to_csv('olist_delivered.csv', index=False)

print("\n✅ Fix applied! olist_delivered.csv updated.")
print("   Now re-run: python olist_eda.py")