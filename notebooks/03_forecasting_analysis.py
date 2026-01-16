"""
TD Geospatial Analytics - Phase 4: Transaction Forecasting
Uses simple time series methods to forecast future demand
Save as: notebooks/03_forecasting_analysis.py
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 1. LOAD TIME SERIES DATA
# ============================================

print("📈 Loading transaction time series data...\n")

conn = sqlite3.connect('data/td_banking.db')

df_timeseries = pd.read_sql_query("""
    SELECT * FROM transactions_timeseries
    ORDER BY date
""", conn)

df_regions = pd.read_sql_query("""
    SELECT * FROM vw_regional_summary
""", conn)

conn.close()

# Convert date to datetime
df_timeseries['date'] = pd.to_datetime(df_timeseries['date'])

print(f"✓ Loaded {len(df_timeseries)} monthly records")
print(f"  Date range: {df_timeseries['date'].min()} to {df_timeseries['date'].max()}")
print(f"  Regions: {df_timeseries['region_name'].nunique()}\n")

# ============================================
# 2. ANALYZE HISTORICAL TRENDS
# ============================================

print("="*70)
print("📊 HISTORICAL TREND ANALYSIS")
print("="*70 + "\n")

# Overall growth rate
province_trends = df_timeseries.groupby(['province', 'date'])['transactions'].sum().reset_index()

for province in province_trends['province'].unique():
    prov_data = province_trends[province_trends['province'] == province].sort_values('date')
    
    first_val = prov_data.iloc[0]['transactions']
    last_val = prov_data.iloc[-1]['transactions']
    months = len(prov_data)
    
    # Calculate CAGR (Compound Annual Growth Rate)
    growth_rate = ((last_val / first_val) ** (12 / months) - 1) * 100
    
    print(f"{province:20} | Growth Rate: {growth_rate:+.2f}% annually")

# ============================================
# 3. SEASONAL PATTERN ANALYSIS
# ============================================

print("\n" + "="*70)
print("🗓️  SEASONAL PATTERNS")
print("="*70 + "\n")

# Calculate average transactions by month across all years
seasonal_pattern = df_timeseries.groupby('month')['transactions'].mean().reset_index()
seasonal_pattern['month_name'] = seasonal_pattern['month'].map({
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
})

baseline = seasonal_pattern['transactions'].mean()
seasonal_pattern['vs_baseline'] = ((seasonal_pattern['transactions'] / baseline - 1) * 100).round(1)

print("Average monthly transaction patterns:\n")
for _, row in seasonal_pattern.iterrows():
    indicator = "🔥" if row['vs_baseline'] > 5 else "📉" if row['vs_baseline'] < -5 else "  "
    print(f"{indicator} {row['month_name']:4} | {row['transactions']:8,.0f} ({row['vs_baseline']:+.1f}% vs baseline)")

# ============================================
# 4. SIMPLE FORECASTING - LINEAR TREND + SEASONALITY
# ============================================

print("\n" + "="*70)
print("🔮 FORECASTING FUTURE DEMAND (Next 6 Months)")
print("="*70 + "\n")

def forecast_region(region_data, months_ahead=6):
    """
    Simple forecast using linear trend + seasonal adjustment
    """
    # Sort by date
    region_data = region_data.sort_values('date').copy()
    
    # Add time index
    region_data['time_idx'] = range(len(region_data))
    
    # Fit linear trend
    X = region_data['time_idx'].values
    y = region_data['transactions'].values
    
    # Simple linear regression (y = mx + b)
    n = len(X)
    x_mean = X.mean()
    y_mean = y.mean()
    
    slope = np.sum((X - x_mean) * (y - y_mean)) / np.sum((X - x_mean) ** 2)
    intercept = y_mean - slope * x_mean
    
    # Calculate seasonal factors
    region_data['month'] = region_data['date'].dt.month
    region_data['trend'] = slope * region_data['time_idx'] + intercept
    region_data['seasonal_factor'] = region_data['transactions'] / region_data['trend']
    
    seasonal_factors = region_data.groupby('month')['seasonal_factor'].mean().to_dict()
    
    # Generate forecasts
    last_date = region_data['date'].max()
    last_idx = region_data['time_idx'].max()
    
    forecasts = []
    for i in range(1, months_ahead + 1):
        future_date = last_date + timedelta(days=30 * i)
        future_idx = last_idx + i
        future_month = future_date.month
        
        # Trend projection
        trend_value = slope * future_idx + intercept
        
        # Apply seasonal adjustment
        seasonal_adj = seasonal_factors.get(future_month, 1.0)
        forecast_value = trend_value * seasonal_adj
        
        forecasts.append({
            'date': future_date,
            'forecast': int(forecast_value),
            'trend': int(trend_value)
        })
    
    return pd.DataFrame(forecasts), slope, intercept

# Forecast for underserved regions (top priorities)
underserved_regions = df_regions[df_regions['coverage_status'] == 'Underserved'].sort_values(
    'demand_score', ascending=False
).head(5)

forecast_results = []

for _, region in underserved_regions.iterrows():
    region_data = df_timeseries[df_timeseries['region_id'] == region['region_id']].copy()
    
    if len(region_data) < 12:  # Need at least 1 year of data
        continue
    
    forecast_df, slope, intercept = forecast_region(region_data, months_ahead=6)
    
    # Current capacity vs forecasted demand
    current_capacity = region['total_branch_capacity']
    forecast_6mo = forecast_df.iloc[-1]['forecast']
    
    capacity_gap_current = region['capacity_gap']
    capacity_gap_future = forecast_6mo - current_capacity
    
    print(f"\n📍 {region['region_name']}")
    print(f"   Province: {region['province']}")
    print(f"   Current Demand: {region['regional_demand']:,}")
    print(f"   Current Capacity: {current_capacity:,}")
    print(f"   6-Month Forecast: {forecast_6mo:,}")
    print(f"   Projected Gap: {capacity_gap_future:,}")
    print(f"   Trend: {'+' if slope > 0 else ''}{slope:.0f} transactions/month")
    
    forecast_results.append({
        'region_name': region['region_name'],
        'province': region['province'],
        'current_demand': region['regional_demand'],
        'current_capacity': current_capacity,
        'forecast_6mo': forecast_6mo,
        'projected_gap': capacity_gap_future,
        'monthly_growth': slope,
        'demand_score': region['demand_score']
    })

# ============================================
# 5. CAPACITY PLANNING RECOMMENDATIONS
# ============================================

print("\n" + "="*70)
print("💡 CAPACITY PLANNING RECOMMENDATIONS")
print("="*70 + "\n")

df_forecast_results = pd.DataFrame(forecast_results)

if len(df_forecast_results) > 0:
    df_forecast_results['branches_needed'] = (df_forecast_results['projected_gap'] / 10000).round(0).astype(int)
    df_forecast_results['staff_needed'] = (df_forecast_results['projected_gap'] / 600).round(0).astype(int)
    
    for _, row in df_forecast_results.iterrows():
        print(f"\n🎯 {row['region_name']}, {row['province']}")
        print(f"   Recommended Actions:")
        
        if row['branches_needed'] > 3:
            print(f"   • Open 3-4 new branches immediately")
        elif row['branches_needed'] > 1:
            print(f"   • Open {row['branches_needed']} new branches")
        else:
            print(f"   • Increase staffing in existing branches")
        
        print(f"   • Hire approximately {row['staff_needed']} additional staff")
        print(f"   • Projected demand increasing by {row['monthly_growth']:,.0f}/month")
        
        if row['monthly_growth'] > 1000:
            print(f"   ⚠️  High growth area - prioritize expansion")

# ============================================
# 6. CREATE FORECAST VISUALIZATIONS
# ============================================

print("\n" + "="*70)
print("📊 CREATING FORECAST VISUALIZATIONS")
print("="*70 + "\n")

# Plot forecasts for top 3 regions
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Transaction Forecasts - Top Underserved Regions', fontsize=16, fontweight='bold')

plot_regions = underserved_regions.head(4)

for idx, (_, region) in enumerate(plot_regions.iterrows()):
    if idx >= 4:
        break
    
    ax = axes[idx // 2, idx % 2]
    
    region_data = df_timeseries[df_timeseries['region_id'] == region['region_id']].copy()
    region_data = region_data.sort_values('date')
    
    # Historical data
    ax.plot(region_data['date'], region_data['transactions'], 
            marker='o', label='Historical', linewidth=2, color='#2E86AB')
    
    # Forecast
    forecast_df, slope, intercept = forecast_region(region_data, months_ahead=6)
    ax.plot(forecast_df['date'], forecast_df['forecast'], 
            marker='s', label='Forecast', linewidth=2, linestyle='--', color='#A23B72')
    
    # Current capacity line
    ax.axhline(y=region['total_branch_capacity'], color='red', 
               linestyle=':', linewidth=2, label='Current Capacity', alpha=0.7)
    
    ax.set_title(f"{region['region_name']}", fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Monthly Transactions')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='x', rotation=45)
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))

plt.tight_layout()
plt.savefig('data/processed/forecast_charts.png', dpi=300, bbox_inches='tight')
print("✓ Saved forecast_charts.png")

# ============================================
# 7. PROVINCE-LEVEL FORECAST SUMMARY
# ============================================

print("\n" + "="*70)
print("🗺️  PROVINCE-LEVEL FORECAST SUMMARY")
print("="*70 + "\n")

province_forecast = []

for province in df_timeseries['province'].unique():
    prov_data = df_timeseries[df_timeseries['province'] == province].copy()
    prov_data = prov_data.groupby('date')['transactions'].sum().reset_index()
    prov_data = prov_data.sort_values('date')
    
    # Simple trend
    prov_data['time_idx'] = range(len(prov_data))
    X = prov_data['time_idx'].values
    y = prov_data['transactions'].values
    
    slope = np.sum((X - X.mean()) * (y - y.mean())) / np.sum((X - X.mean()) ** 2)
    
    current_total = prov_data.iloc[-1]['transactions']
    forecast_6mo = current_total + (slope * 6)
    
    province_forecast.append({
        'province': province,
        'current_monthly': int(current_total),
        'forecast_6mo': int(forecast_6mo),
        'monthly_growth': int(slope),
        'growth_rate_pct': round((slope / current_total) * 100, 2)
    })

df_province_forecast = pd.DataFrame(province_forecast).sort_values('forecast_6mo', ascending=False)

for _, row in df_province_forecast.iterrows():
    print(f"{row['province']:20} | Current: {row['current_monthly']:>10,} | "
          f"6mo Forecast: {row['forecast_6mo']:>10,} | Growth: {row['growth_rate_pct']:+.2f}%/mo")

# ============================================
# 8. EXPORT RESULTS
# ============================================

print("\n💾 Exporting forecast results...\n")

if len(df_forecast_results) > 0:
    df_forecast_results.to_csv('data/processed/regional_forecasts.csv', index=False)
    print("✓ regional_forecasts.csv")

df_province_forecast.to_csv('data/processed/province_forecasts.csv', index=False)
print("✓ province_forecasts.csv")

print("\n" + "="*70)
print("✅ FORECASTING ANALYSIS COMPLETE!")
print("="*70)
print("\nKey Outputs:")
print("• Regional demand forecasts (6 months ahead)")
print("• Capacity gap projections")
print("• Staffing & expansion recommendations")
print("• Forecast visualization charts")
print("\nNext: Create dashboard in Tableau/PowerBI!\n")