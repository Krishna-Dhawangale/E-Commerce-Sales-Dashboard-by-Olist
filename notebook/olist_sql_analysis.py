# ============================================================
# OLIST E-COMMERCE DASHBOARD PROJECT
# Step 3: SQL Analysis — 15+ Queries using SQLite + Python
# Covers: Basic, Intermediate & Advanced SQL
# ============================================================

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
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
# SETUP — Load CSVs into SQLite Database
# ============================================================
print("=" * 55)
print("  Setting up SQLite Database...")
print("=" * 55)

conn = sqlite3.connect('olist.db')

# Load all 9 tables into SQLite
tables = {
    'orders'      : 'olist_orders_dataset.csv',
    'customers'   : 'olist_customers_dataset.csv',
    'order_items' : 'olist_order_items_dataset.csv',
    'payments'    : 'olist_order_payments_dataset.csv',
    'reviews'     : 'olist_order_reviews_dataset.csv',
    'products'    : 'olist_products_dataset.csv',
    'sellers'     : 'olist_sellers_dataset.csv',
    'geolocation' : 'olist_geolocation_dataset.csv',
    'category'    : 'product_category_name_translation.csv',
}

for table_name, file_name in tables.items():
    df = pd.read_csv(file_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f"  ✅ {table_name:<15} loaded — {len(df):>8,} rows")

print("\n✅ SQLite database 'olist.db' ready!\n")

# ── Helper function to run & display queries ─────────────────
def run_query(title, sql, show_rows=10):
    print("─" * 55)
    print(f"  {title}")
    print("─" * 55)
    df = pd.read_sql_query(sql, conn)
    print(df.head(show_rows).to_string(index=False))
    print(f"\n  → {len(df)} rows returned\n")
    return df

# ============================================================
# QUERY 1 — Total Business KPIs (Basic)
# ============================================================
q1 = run_query(
    "Q1: Overall Business KPIs",
    """
    SELECT
        COUNT(DISTINCT o.order_id)          AS total_orders,
        COUNT(DISTINCT o.customer_id)       AS total_customers,
        ROUND(SUM(p.payment_value), 2)      AS total_revenue,
        ROUND(AVG(p.payment_value), 2)      AS avg_order_value,
        ROUND(MIN(p.payment_value), 2)      AS min_order_value,
        ROUND(MAX(p.payment_value), 2)      AS max_order_value
    FROM orders o
    JOIN payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
    """
)

# ============================================================
# QUERY 2 — Monthly Revenue Trend (Basic + Date functions)
# ============================================================
q2 = run_query(
    "Q2: Monthly Revenue Trend",
    """
    SELECT
        STRFTIME('%Y', order_purchase_timestamp)       AS year,
        STRFTIME('%m', order_purchase_timestamp)       AS month,
        COUNT(DISTINCT o.order_id)                     AS total_orders,
        ROUND(SUM(p.payment_value), 2)                 AS monthly_revenue
    FROM orders o
    JOIN payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY year, month
    ORDER BY year, month
    """,
    show_rows=20
)

# ============================================================
# QUERY 3 — Revenue by Product Category (Basic JOIN)
# ============================================================
q3 = run_query(
    "Q3: Revenue by Product Category (Top 10)",
    """
    SELECT
        COALESCE(ct.product_category_name_english,
                 pr.product_category_name, 'Unknown') AS category,
        COUNT(DISTINCT o.order_id)                    AS total_orders,
        ROUND(SUM(oi.price), 2)                       AS total_revenue,
        ROUND(AVG(oi.price), 2)                       AS avg_price
    FROM orders o
    JOIN order_items oi  ON o.order_id  = oi.order_id
    JOIN products pr     ON oi.product_id = pr.product_id
    LEFT JOIN category ct ON pr.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY category
    ORDER BY total_revenue DESC
    LIMIT 10
    """
)

# ============================================================
# QUERY 4 — Revenue by State (Basic GROUP BY)
# ============================================================
q4 = run_query(
    "Q4: Revenue by Customer State (Top 10)",
    """
    SELECT
        c.customer_state                          AS state,
        COUNT(DISTINCT o.order_id)                AS total_orders,
        COUNT(DISTINCT c.customer_unique_id)      AS unique_customers,
        ROUND(SUM(p.payment_value), 2)            AS total_revenue,
        ROUND(AVG(p.payment_value), 2)            AS avg_order_value
    FROM orders o
    JOIN customers c  ON o.customer_id  = c.customer_id
    JOIN payments p   ON o.order_id     = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY state
    ORDER BY total_revenue DESC
    LIMIT 10
    """
)

# ============================================================
# QUERY 5 — Payment Method Analysis (Basic)
# ============================================================
q5 = run_query(
    "Q5: Payment Method Analysis",
    """
    SELECT
        payment_type,
        COUNT(*)                              AS total_transactions,
        ROUND(SUM(payment_value), 2)          AS total_value,
        ROUND(AVG(payment_value), 2)          AS avg_value,
        ROUND(AVG(payment_installments), 1)   AS avg_installments
    FROM payments
    GROUP BY payment_type
    ORDER BY total_transactions DESC
    """
)

# ============================================================
# QUERY 6 — Delivery Performance Analysis (Intermediate)
# ============================================================
q6 = run_query(
    "Q6: Delivery Performance — On-time vs Late",
    """
    SELECT
        CASE
            WHEN order_delivered_customer_date <= order_estimated_delivery_date
            THEN 'On Time'
            ELSE 'Late'
        END AS delivery_status,
        COUNT(*)                    AS total_orders,
        ROUND(COUNT(*) * 100.0 /
            SUM(COUNT(*)) OVER (), 2) AS percentage
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
    GROUP BY delivery_status
    """
)

# ============================================================
# QUERY 7 — Top 10 Sellers by Revenue (Intermediate JOIN)
# ============================================================
q7 = run_query(
    "Q7: Top 10 Sellers by Revenue",
    """
    SELECT
        s.seller_id,
        s.seller_state,
        COUNT(DISTINCT oi.order_id)       AS total_orders,
        COUNT(DISTINCT oi.product_id)     AS unique_products,
        ROUND(SUM(oi.price), 2)           AS total_revenue,
        ROUND(AVG(oi.price), 2)           AS avg_item_price,
        ROUND(AVG(r.review_score), 2)     AS avg_review_score
    FROM order_items oi
    JOIN sellers s  ON oi.seller_id  = s.seller_id
    JOIN orders o   ON oi.order_id   = o.order_id
    LEFT JOIN reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY s.seller_id, s.seller_state
    ORDER BY total_revenue DESC
    LIMIT 10
    """
)

# ============================================================
# QUERY 8 — Review Score by Category (Intermediate)
# ============================================================
q8 = run_query(
    "Q8: Avg Review Score by Product Category (Top 10)",
    """
    SELECT
        COALESCE(ct.product_category_name_english,
                 pr.product_category_name) AS category,
        COUNT(DISTINCT o.order_id)         AS total_orders,
        ROUND(AVG(r.review_score), 2)      AS avg_review_score,
        SUM(CASE WHEN r.review_score = 5
                 THEN 1 ELSE 0 END)        AS five_star_count,
        SUM(CASE WHEN r.review_score <= 2
                 THEN 1 ELSE 0 END)        AS low_score_count
    FROM orders o
    JOIN order_items oi  ON o.order_id    = oi.order_id
    JOIN products pr     ON oi.product_id = pr.product_id
    LEFT JOIN category ct ON pr.product_category_name = ct.product_category_name
    JOIN reviews r       ON o.order_id    = r.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY category
    HAVING total_orders >= 100
    ORDER BY avg_review_score DESC
    LIMIT 10
    """
)

# ============================================================
# QUERY 9 — Month-over-Month Revenue Growth (Window Function)
# ============================================================
q9 = run_query(
    "Q9: Month-over-Month Revenue Growth % (Window Function)",
    """
    WITH monthly_revenue AS (
        SELECT
            STRFTIME('%Y', o.order_purchase_timestamp) AS year,
            STRFTIME('%m', o.order_purchase_timestamp) AS month,
            ROUND(SUM(p.payment_value), 2)             AS revenue
        FROM orders o
        JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY year, month
    )
    SELECT
        year,
        month,
        revenue,
        LAG(revenue) OVER (ORDER BY year, month)   AS prev_month_revenue,
        ROUND(
            (revenue - LAG(revenue) OVER (ORDER BY year, month))
            * 100.0
            / LAG(revenue) OVER (ORDER BY year, month),
        2) AS mom_growth_pct
    FROM monthly_revenue
    ORDER BY year, month
    """,
    show_rows=20
)

# ============================================================
# QUERY 10 — Running Total Revenue (Window Function)
# ============================================================
q10 = run_query(
    "Q10: Cumulative Revenue Over Time (Running Total)",
    """
    WITH monthly AS (
        SELECT
            STRFTIME('%Y-%m', o.order_purchase_timestamp) AS period,
            ROUND(SUM(p.payment_value), 2)                AS monthly_revenue
        FROM orders o
        JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY period
    )
    SELECT
        period,
        monthly_revenue,
        ROUND(SUM(monthly_revenue) OVER (
            ORDER BY period
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2) AS cumulative_revenue
    FROM monthly
    ORDER BY period
    """,
    show_rows=20
)

# ============================================================
# QUERY 11 — Customer Ranking by Spend (Window Function)
# ============================================================
q11 = run_query(
    "Q11: Top Customers by Total Spend (RANK + Window)",
    """
    WITH customer_spend AS (
        SELECT
            c.customer_unique_id,
            c.customer_state,
            c.customer_city,
            COUNT(DISTINCT o.order_id)      AS total_orders,
            ROUND(SUM(p.payment_value), 2)  AS total_spent
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN payments p  ON o.order_id    = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id
    )
    SELECT
        customer_unique_id,
        customer_state,
        customer_city,
        total_orders,
        total_spent,
        RANK() OVER (ORDER BY total_spent DESC) AS spend_rank,
        ROUND(total_spent * 100.0 /
            SUM(total_spent) OVER (), 4)        AS revenue_share_pct
    FROM customer_spend
    ORDER BY spend_rank
    LIMIT 10
    """
)

# ============================================================
# QUERY 12 — Seller Performance Ranking by State (Advanced CTE)
# ============================================================
q12 = run_query(
    "Q12: Seller Performance Ranking within Each State (CTE + RANK)",
    """
    WITH seller_stats AS (
        SELECT
            s.seller_id,
            s.seller_state,
            COUNT(DISTINCT oi.order_id)    AS total_orders,
            ROUND(SUM(oi.price), 2)        AS total_revenue,
            ROUND(AVG(r.review_score), 2)  AS avg_rating
        FROM order_items oi
        JOIN sellers s      ON oi.seller_id  = s.seller_id
        JOIN orders o       ON oi.order_id   = o.order_id
        LEFT JOIN reviews r ON o.order_id    = r.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY s.seller_id, s.seller_state
    ),
    ranked AS (
        SELECT
            seller_id,
            seller_state,
            total_orders,
            total_revenue,
            avg_rating,
            RANK() OVER (
                PARTITION BY seller_state
                ORDER BY total_revenue DESC
            ) AS rank_in_state
        FROM seller_stats
    )
    SELECT *
    FROM ranked
    WHERE rank_in_state <= 3
    ORDER BY seller_state, rank_in_state
    LIMIT 20
    """
)

# ============================================================
# QUERY 13 — Cohort Analysis — First Purchase Month (Advanced)
# ============================================================
q13 = run_query(
    "Q13: Customer Cohort — First Purchase Month",
    """
    WITH first_purchase AS (
        SELECT
            c.customer_unique_id,
            MIN(STRFTIME('%Y-%m', o.order_purchase_timestamp)) AS cohort_month
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id
    )
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS new_customers
    FROM first_purchase
    GROUP BY cohort_month
    ORDER BY cohort_month
    """,
    show_rows=20
)

# ============================================================
# QUERY 14 — Late Delivery Impact on Review Score (Advanced)
# ============================================================
q14 = run_query(
    "Q14: Impact of Late Delivery on Review Scores",
    """
    SELECT
        CASE
            WHEN order_delivered_customer_date <= order_estimated_delivery_date
            THEN 'On Time'
            ELSE 'Late'
        END                               AS delivery_status,
        COUNT(*)                          AS total_orders,
        ROUND(AVG(r.review_score), 3)     AS avg_review_score,
        SUM(CASE WHEN r.review_score = 5
                 THEN 1 ELSE 0 END)       AS five_star,
        SUM(CASE WHEN r.review_score <= 2
                 THEN 1 ELSE 0 END)       AS one_two_star
    FROM orders o
    JOIN reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
    GROUP BY delivery_status
    """
)

# ============================================================
# QUERY 15 — Revenue Contribution: Top 20% Categories (Pareto)
# ============================================================
q15 = run_query(
    "Q15: Pareto Analysis — 80/20 Rule on Categories",
    """
    WITH cat_revenue AS (
        SELECT
            COALESCE(ct.product_category_name_english,
                     pr.product_category_name) AS category,
            ROUND(SUM(oi.price), 2)            AS revenue
        FROM order_items oi
        JOIN products pr     ON oi.product_id = pr.product_id
        LEFT JOIN category ct ON pr.product_category_name = ct.product_category_name
        JOIN orders o        ON oi.order_id   = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY category
    ),
    ranked AS (
        SELECT
            category,
            revenue,
            ROUND(revenue * 100.0 / SUM(revenue) OVER (), 2) AS revenue_pct,
            ROUND(SUM(revenue) OVER (
                ORDER BY revenue DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) * 100.0 / SUM(revenue) OVER (), 2)             AS cumulative_pct
        FROM cat_revenue
    )
    SELECT
        category,
        revenue,
        revenue_pct,
        cumulative_pct
    FROM ranked
    ORDER BY revenue DESC
    LIMIT 15
    """
)

# ============================================================
# QUERY 16 — Average Delivery Days by State (Intermediate)
# ============================================================
q16 = run_query(
    "Q16: Average Delivery Days by State",
    """
    SELECT
        c.customer_state                   AS state,
        COUNT(*)                           AS total_orders,
        ROUND(AVG(
            JULIANDAY(o.order_delivered_customer_date) -
            JULIANDAY(o.order_purchase_timestamp)
        ), 1)                              AS avg_delivery_days,
        ROUND(AVG(
            JULIANDAY(o.order_estimated_delivery_date) -
            JULIANDAY(o.order_purchase_timestamp)
        ), 1)                              AS avg_estimated_days
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY state
    HAVING total_orders >= 100
    ORDER BY avg_delivery_days DESC
    LIMIT 10
    """
)

# ============================================================
# VISUALISE SQL RESULTS — 3 Charts from SQL output
# ============================================================
print("\n📊 Generating charts from SQL results...\n")

# SQL Chart 1 — MoM Revenue Growth
mom = q9.dropna(subset=['mom_growth_pct'])
mom['period'] = mom['year'] + '-' + mom['month']

fig, ax = plt.subplots(figsize=(14, 5))
colors = ['#4CAF50' if x >= 0 else '#F44336'
          for x in mom['mom_growth_pct']]
ax.bar(range(len(mom)), mom['mom_growth_pct'], color=colors, edgecolor='white')
ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')
ax.set_xticks(range(len(mom)))
ax.set_xticklabels(mom['period'], rotation=45, ha='right', fontsize=8)
ax.set_title('Month-over-Month Revenue Growth %')
ax.set_ylabel('Growth %')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
plt.tight_layout()
plt.savefig('sql_chart1_mom_growth.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: sql_chart1_mom_growth.png")

# SQL Chart 2 — Cumulative Revenue
q10_clean = q10.copy()
fig, ax = plt.subplots(figsize=(14, 5))
ax.fill_between(range(len(q10_clean)),
                q10_clean['cumulative_revenue'], alpha=0.2, color='#9C27B0')
ax.plot(range(len(q10_clean)), q10_clean['cumulative_revenue'],
        color='#9C27B0', linewidth=2.5, marker='o', markersize=4)
ax.set_xticks(range(len(q10_clean)))
ax.set_xticklabels(q10_clean['period'], rotation=45, ha='right', fontsize=8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e6:.1f}M'))
ax.set_title('Cumulative Revenue Over Time')
ax.set_ylabel('Cumulative Revenue')
plt.tight_layout()
plt.savefig('sql_chart2_cumulative_revenue.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: sql_chart2_cumulative_revenue.png")

# SQL Chart 3 — Late Delivery vs Review Score
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(q14['delivery_status'], q14['avg_review_score'],
              color=['#4CAF50', '#F44336'], edgecolor='white',
              width=0.4)
for bar, val in zip(bars, q14['avg_review_score']):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.02,
            f'{val:.2f} ⭐', ha='center', fontsize=12, fontweight='bold')
ax.set_ylim(0, 5.5)
ax.set_title('Late Delivery Impact on Review Scores')
ax.set_ylabel('Average Review Score')
ax.set_xlabel('Delivery Status')
plt.tight_layout()
plt.savefig('sql_chart3_delivery_vs_review.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: sql_chart3_delivery_vs_review.png")

# ============================================================
# CLOSE CONNECTION & SUMMARY
# ============================================================
conn.close()

print("\n" + "=" * 55)
print("         SQL ANALYSIS COMPLETE!")
print("=" * 55)
print("""
  16 SQL queries executed covering:
  ✅ Basic    — KPIs, GROUP BY, JOINs, aggregations
  ✅ Intermediate — CASE WHEN, HAVING, multi-table JOINs
  ✅ Advanced  — CTEs, Window Functions (LAG, RANK,
                 PARTITION BY, Running Totals)

  3 SQL result charts saved:
  ✅ sql_chart1_mom_growth.png
  ✅ sql_chart2_cumulative_revenue.png
  ✅ sql_chart3_delivery_vs_review.png

  Database saved as: olist.db

  🎉 Next Step → RFM Customer Segmentation
""")