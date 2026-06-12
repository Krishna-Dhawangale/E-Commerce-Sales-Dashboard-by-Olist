# ============================================================
# QUICK FIX — Query 12: Seller Ranking by State
# SQLite doesn't allow WHERE on window function alias directly
# Solution: wrap in a second CTE
# ============================================================

import pandas as pd
import sqlite3

conn = sqlite3.connect('olist.db')

def run_query(title, sql, show_rows=10):
    print("─" * 55)
    print(f"  {title}")
    print("─" * 55)
    df = pd.read_sql_query(sql, conn)
    print(df.head(show_rows).to_string(index=False))
    print(f"\n  → {len(df)} rows returned\n")
    return df

# ── Fixed Query 12 ───────────────────────────────────────────
q12 = run_query(
    "Q12 FIXED: Seller Ranking within Each State",
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

conn.close()
print("✅ Fix successful! Now re-run olist_sql_analysis.py")
print("   Replace Q12 block with this fixed version.")