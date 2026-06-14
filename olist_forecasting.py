# ============================================================
# OLIST E-COMMERCE DASHBOARD PROJECT
# Step 5: Revenue Forecasting using Facebook Prophet
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
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
print("  Step 5: Revenue Forecasting with Prophet")
print("=" * 55)

delivered = pd.read_csv('olist_delivered.csv', low_memory=False)
delivered['order_purchase_timestamp'] = pd.to_datetime(
    delivered['order_purchase_timestamp'], errors='coerce')

print(f"  ✅ Delivered orders loaded: {len(delivered):,} rows\n")

# ============================================================
# 2. PREPARE MONTHLY REVENUE TIME SERIES
# ============================================================
print("Preparing monthly revenue time series...")

# Aggregate to monthly revenue
monthly = (
    delivered.groupby(
        delivered['order_purchase_timestamp'].dt.to_period('M')
    )['payment_value']
    .sum()
    .reset_index()
)
monthly.columns = ['period', 'revenue']
monthly['ds'] = monthly['period'].dt.to_timestamp()
monthly['y']  = monthly['revenue'].round(2)
monthly = monthly[['ds', 'y']].sort_values('ds').reset_index(drop=True)

# Remove first and last month (incomplete data)
monthly = monthly.iloc[1:-1].reset_index(drop=True)

print(f"  ✅ Monthly data prepared: {len(monthly)} months")
print(f"  Date range: {monthly['ds'].min().date()} → {monthly['ds'].max().date()}")
print(f"  Revenue range: R$ {monthly['y'].min():,.0f} → R$ {monthly['y'].max():,.0f}")
print(f"\n  Monthly Revenue Data:")
print(monthly.to_string(index=False))

# ============================================================
# 3. TRAIN PROPHET MODEL
# ============================================================
print("\nTraining Prophet model...")

model = Prophet(
    yearly_seasonality =True,
    weekly_seasonality =False,   # Monthly data — no weekly pattern
    daily_seasonality  =False,   # Monthly data — no daily pattern
    seasonality_mode   ='multiplicative',  # Better for growing trends
    changepoint_prior_scale=0.05,          # Controls trend flexibility
    seasonality_prior_scale=10,            # Controls seasonality strength
    interval_width=0.95                    # 95% confidence interval
)

# Add Brazilian holidays as special events
model.add_country_holidays(country_name='BR')

# Fit the model
model.fit(monthly)
print("  ✅ Prophet model trained successfully!")

# ============================================================
# 4. GENERATE FORECAST (3 months ahead)
# ============================================================
print("\nGenerating 3-month forecast...")

# Create future dataframe — 3 months ahead
future   = model.make_future_dataframe(periods=3, freq='MS')
forecast = model.predict(future)

# Key forecast columns
forecast_clean = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper',
                            'trend', 'yearly']].copy()
forecast_clean.columns = ['date', 'forecast', 'lower_bound',
                           'upper_bound', 'trend', 'yearly_seasonality']
forecast_clean = forecast_clean.round(2)

# Split historical fit vs future predictions
historical_forecast = forecast_clean[forecast_clean['date'] <= monthly['ds'].max()]
future_forecast     = forecast_clean[forecast_clean['date'] >  monthly['ds'].max()]

print("\n  📅 3-MONTH REVENUE FORECAST:")
print("  " + "─" * 50)
print(f"  {'Month':<15} {'Forecast':>12} {'Lower':>12} {'Upper':>12}")
print("  " + "─" * 50)
for _, row in future_forecast.iterrows():
    print(f"  {str(row['date'].date()):<15} "
          f"R$ {row['forecast']:>9,.0f} "
          f"R$ {row['lower_bound']:>9,.0f} "
          f"R$ {row['upper_bound']:>9,.0f}")
print("  " + "─" * 50)

total_forecast = future_forecast['forecast'].sum()
print(f"\n  Total forecasted revenue (3 months): R$ {total_forecast:,.0f}")

# ============================================================
# 5. MODEL EVALUATION (on historical data)
# ============================================================
print("\nEvaluating model accuracy...")

# Merge actual vs predicted for historical period
eval_df = monthly.merge(
    forecast_clean[['date', 'forecast']],
    left_on='ds', right_on='date', how='inner'
)
eval_df['error']    = eval_df['y'] - eval_df['forecast']
eval_df['abs_error']= eval_df['error'].abs()
eval_df['pct_error']= (eval_df['abs_error'] / eval_df['y'] * 100)

mae  = eval_df['abs_error'].mean()
mape = eval_df['pct_error'].mean()
rmse = np.sqrt((eval_df['error'] ** 2).mean())

print(f"\n  MODEL ACCURACY METRICS:")
print(f"  MAE  (Mean Absolute Error)       : R$ {mae:,.0f}")
print(f"  MAPE (Mean Absolute % Error)     : {mape:.2f}%")
print(f"  RMSE (Root Mean Squared Error)   : R$ {rmse:,.0f}")
print(f"  Model Accuracy                   : {100 - mape:.2f}%")

# ============================================================
# 6. VISUALISATIONS — 5 Forecast Charts
# ============================================================
print("\n\n📊 Generating forecast charts...")

BLUE   = '#2196F3'
GREEN  = '#4CAF50'
ORANGE = '#FF9800'
RED    = '#F44336'
PURPLE = '#9C27B0'

# ── Chart 1: Full Forecast with Confidence Interval ─────────
fig, ax = plt.subplots(figsize=(14, 6))

# Actual revenue
ax.plot(monthly['ds'], monthly['y'],
        color=BLUE, linewidth=2.5, marker='o',
        markersize=5, label='Actual Revenue', zorder=5)

# Historical fitted values
ax.plot(historical_forecast['date'], historical_forecast['forecast'],
        color=GREEN, linewidth=1.5, linestyle='--',
        label='Model Fit', alpha=0.8)

# Future forecast
ax.plot(future_forecast['date'], future_forecast['forecast'],
        color=ORANGE, linewidth=2.5, marker='D',
        markersize=7, label='Forecast (3 months)', zorder=5)

# Confidence interval for future
ax.fill_between(future_forecast['date'],
                future_forecast['lower_bound'],
                future_forecast['upper_bound'],
                alpha=0.2, color=ORANGE, label='95% Confidence Interval')

# Vertical line separating history and forecast
ax.axvline(monthly['ds'].max(), color='gray',
           linestyle=':', linewidth=1.5, label='Forecast Start')

# Annotate forecast values
for _, row in future_forecast.iterrows():
    ax.annotate(
        f"R$ {row['forecast']/1e3:.0f}K",
        xy=(row['date'], row['forecast']),
        xytext=(0, 12), textcoords='offset points',
        ha='center', fontsize=9, fontweight='bold', color=ORANGE
    )

ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e6:.1f}M'))
ax.set_title('Monthly Revenue — Actual vs Forecast (3 Months Ahead)',
             fontsize=14)
ax.set_xlabel('Month')
ax.set_ylabel('Revenue')
ax.legend(loc='upper left', fontsize=9)
plt.tight_layout()
plt.savefig('forecast_chart1_main.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: forecast_chart1_main.png")

# ── Chart 2: Trend Component ─────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(forecast_clean['date'], forecast_clean['trend'],
        color=PURPLE, linewidth=2.5)
ax.fill_between(forecast_clean['date'],
                forecast_clean['trend'] * 0.95,
                forecast_clean['trend'] * 1.05,
                alpha=0.15, color=PURPLE)
ax.axvline(monthly['ds'].max(), color='gray',
           linestyle=':', linewidth=1.5, label='Forecast Start')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e6:.1f}M'))
ax.set_title('Revenue Trend Component (Prophet Decomposition)')
ax.set_xlabel('Month')
ax.set_ylabel('Trend')
ax.legend()
plt.tight_layout()
plt.savefig('forecast_chart2_trend.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: forecast_chart2_trend.png")

# ── Chart 3: Actual vs Predicted (Historical) ────────────────
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(eval_df['ds'], eval_df['y'],
        color=BLUE, linewidth=2, marker='o',
        markersize=4, label='Actual')
ax.plot(eval_df['ds'], eval_df['forecast'],
        color=RED, linewidth=2, linestyle='--',
        marker='s', markersize=4, label='Predicted')
ax.fill_between(eval_df['ds'],
                eval_df['y'], eval_df['forecast'],
                alpha=0.1, color='gray', label='Error')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e6:.1f}M'))
ax.set_title(f'Actual vs Predicted Revenue | MAPE: {mape:.2f}% | Accuracy: {100-mape:.2f}%')
ax.set_xlabel('Month')
ax.set_ylabel('Revenue')
ax.legend()
plt.tight_layout()
plt.savefig('forecast_chart3_actual_vs_predicted.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: forecast_chart3_actual_vs_predicted.png")

# ── Chart 4: Forecast Bar Chart (Future 3 months) ────────────
fig, ax = plt.subplots(figsize=(8, 5))
months_label = [d.strftime('%b %Y') for d in future_forecast['date']]
bars = ax.bar(months_label, future_forecast['forecast'],
              color=[ORANGE, '#FF7043', '#E64A19'],
              edgecolor='white', linewidth=1.5, width=0.5)
ax.errorbar(
    x=range(len(future_forecast)),
    y=future_forecast['forecast'],
    yerr=[
        future_forecast['forecast'] - future_forecast['lower_bound'],
        future_forecast['upper_bound'] - future_forecast['forecast']
    ],
    fmt='none', color='gray', capsize=6, linewidth=1.5
)
for bar, val in zip(bars, future_forecast['forecast']):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 5000,
            f'R$ {val/1e3:.0f}K',
            ha='center', fontsize=11, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e3:.0f}K'))
ax.set_title('3-Month Revenue Forecast with Error Bars')
ax.set_ylabel('Forecasted Revenue')
plt.tight_layout()
plt.savefig('forecast_chart4_bar.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: forecast_chart4_bar.png")

# ── Chart 5: Yearly Seasonality Pattern ──────────────────────
monthly['month_num']  = monthly['ds'].dt.month
monthly['month_name'] = monthly['ds'].dt.strftime('%b')
seasonality = monthly.groupby(['month_num', 'month_name'])['y'].mean().reset_index()
seasonality = seasonality.sort_values('month_num')

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(seasonality['month_name'], seasonality['y'],
              color=sns.color_palette('coolwarm', 12),
              edgecolor='white', linewidth=1)
ax.axhline(seasonality['y'].mean(), color='gray',
           linestyle='--', linewidth=1.5,
           label=f"Avg: R$ {seasonality['y'].mean():,.0f}")
for bar, val in zip(bars, seasonality['y']):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 1000,
            f'R$ {val/1e3:.0f}K',
            ha='center', fontsize=8, rotation=0)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'R$ {x/1e3:.0f}K'))
ax.set_title('Average Monthly Revenue by Month — Seasonality Pattern')
ax.set_xlabel('Month')
ax.set_ylabel('Average Revenue')
ax.legend()
plt.tight_layout()
plt.savefig('forecast_chart5_seasonality.png', dpi=150, bbox_inches='tight')
plt.show()
print("   ✅ Saved: forecast_chart5_seasonality.png")

# ============================================================
# 7. SAVE FORECAST TO CSV (for Power BI dashboard)
# ============================================================
# Save full forecast
forecast_clean.to_csv('olist_forecast.csv', index=False)

# Save future 3 months only
future_forecast.to_csv('olist_forecast_future.csv', index=False)

print("\n✅ Forecast saved:")
print("   olist_forecast.csv         — full forecast (historical + future)")
print("   olist_forecast_future.csv  — future 3 months only (for Power BI)")

# ============================================================
# 8. SUMMARY
# ============================================================
print("\n" + "=" * 55)
print("  FORECASTING SUMMARY")
print("=" * 55)
print(f"""
  Model        : Facebook Prophet
  Seasonality  : Multiplicative (yearly)
  Holidays     : Brazilian public holidays included
  Confidence   : 95% interval

  ACCURACY:
  MAPE         : {mape:.2f}%
  Accuracy     : {100-mape:.2f}%
  MAE          : R$ {mae:,.0f}
  RMSE         : R$ {rmse:,.0f}

  3-MONTH FORECAST:""")

for _, row in future_forecast.iterrows():
    print(f"  {str(row['date'].date())}  →  "
          f"R$ {row['forecast']:>10,.0f}  "
          f"[R$ {row['lower_bound']:,.0f} – R$ {row['upper_bound']:,.0f}]")

print(f"""
  Total (3 months) : R$ {total_forecast:,.0f}

  5 Forecast Charts saved:
  ✅ forecast_chart1_main.png
  ✅ forecast_chart2_trend.png
  ✅ forecast_chart3_actual_vs_predicted.png
  ✅ forecast_chart4_bar.png
  ✅ forecast_chart5_seasonality.png

""")