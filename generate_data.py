"""
TD Geospatial Analytics - Data Generation Script
Generates realistic Canadian banking data for analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Set random seed for reproducibility
np.random.seed(42)

# ============================================
# 1. GENERATE BRANCH DATA
# ============================================

def generate_branches():
    """Generate realistic branch locations across Canada"""
    
    # Define regions with realistic lat/long ranges
    regions = {
        'Ontario': {'lat': (43.0, 45.5), 'lon': (-79.5, -75.5), 'branches': 60},
        'British Columbia': {'lat': (49.0, 49.3), 'lon': (-123.2, -122.8), 'branches': 35},
        'Alberta': {'lat': (51.0, 51.1), 'lon': (-114.2, -113.9), 'branches': 30},
        'Quebec': {'lat': (45.4, 45.6), 'lon': (-73.8, -73.5), 'branches': 25}
    }
    
    branches = []
    branch_id = 1
    
    for province, config in regions.items():
        for _ in range(config['branches']):
            lat = np.random.uniform(config['lat'][0], config['lat'][1])
            lon = np.random.uniform(config['lon'][0], config['lon'][1])
            
            # Generate branch characteristics
            branch = {
                'branch_id': f'BR{branch_id:04d}',
                'province': province,
                'latitude': round(lat, 6),
                'longitude': round(lon, 6),
                'staff_count': np.random.randint(8, 25),
                'branch_type': np.random.choice(['Full Service', 'Express', 'Flagship'], p=[0.7, 0.2, 0.1]),
                'opening_year': np.random.randint(1995, 2020),
                'monthly_transactions': np.random.randint(3000, 15000)
            }
            branches.append(branch)
            branch_id += 1
    
    df_branches = pd.DataFrame(branches)
    
    # Add derived metrics
    df_branches['transactions_per_staff'] = (df_branches['monthly_transactions'] / 
                                             df_branches['staff_count']).round(0)
    
    return df_branches


# ============================================
# 2. GENERATE REGIONAL DEMAND DATA
# ============================================

def generate_regional_demand():
    """Generate customer demand metrics by region"""
    
    regions_data = []
    
    # Ontario regions
    ontario_regions = ['Toronto Central', 'Toronto North', 'Toronto East', 'Toronto West', 
                       'Mississauga', 'Brampton', 'Hamilton', 'Ottawa']
    
    # BC regions
    bc_regions = ['Vancouver Downtown', 'Vancouver East', 'Vancouver West', 
                  'Burnaby', 'Surrey', 'Richmond']
    
    # Alberta regions
    alberta_regions = ['Calgary Downtown', 'Calgary North', 'Calgary South', 
                       'Edmonton Central', 'Edmonton West']
    
    # Quebec regions
    quebec_regions = ['Montreal Central', 'Montreal East', 'Montreal West', 
                      'Laval', 'Quebec City']
    
    all_regions = [
        ('Ontario', ontario_regions),
        ('British Columbia', bc_regions),
        ('Alberta', alberta_regions),
        ('Quebec', quebec_regions)
    ]
    
    region_id = 1
    for province, region_list in all_regions:
        for region_name in region_list:
            # Generate realistic demographics
            population = np.random.randint(50000, 500000)
            median_income = np.random.randint(45000, 95000)
            
            # Digital adoption inversely correlated with age, positively with income
            digital_adoption = min(0.85, (median_income / 100000) * 0.7 + np.random.uniform(0.15, 0.25))
            
            region = {
                'region_id': f'RG{region_id:03d}',
                'region_name': region_name,
                'province': province,
                'population': population,
                'median_income': median_income,
                'digital_adoption_rate': round(digital_adoption, 3),
                'avg_monthly_transactions': int(population * np.random.uniform(0.4, 0.8)),
                'in_branch_preference': round(1 - digital_adoption, 3),
                'small_business_density': np.random.randint(100, 2000)
            }
            regions_data.append(region)
            region_id += 1
    
    df_regions = pd.DataFrame(regions_data)
    
    # Add customer demand score (composite metric)
    df_regions['demand_score'] = (
        (df_regions['population'] / 100000) * 0.4 +
        (df_regions['avg_monthly_transactions'] / 100000) * 0.3 +
        (df_regions['small_business_density'] / 500) * 0.3
    ).round(2)
    
    return df_regions


# ============================================
# 3. GENERATE TIME SERIES DATA
# ============================================

def generate_time_series(df_regions):
    """Generate 3 years of monthly transaction data with seasonality"""
    
    start_date = datetime(2021, 1, 1)
    months = 36  # 3 years
    
    time_series_data = []
    
    for _, region in df_regions.iterrows():
        base_transactions = region['avg_monthly_transactions']
        
        for month in range(months):
            current_date = start_date + timedelta(days=30 * month)
            month_num = current_date.month
            
            # Seasonal factors
            seasonal_factor = 1.0
            if month_num in [11, 12]:  # Holiday season
                seasonal_factor = 1.15
            elif month_num in [1, 2]:  # Post-holiday dip
                seasonal_factor = 0.90
            elif month_num in [6, 7, 8]:  # Summer
                seasonal_factor = 1.05
            
            # Growth trend (2% annual growth)
            growth_factor = 1 + (month / months) * 0.06
            
            # Random variation
            random_factor = np.random.uniform(0.95, 1.05)
            
            # Calculate transactions
            transactions = int(base_transactions * seasonal_factor * growth_factor * random_factor)
            
            time_series_data.append({
                'region_id': region['region_id'],
                'region_name': region['region_name'],
                'province': region['province'],
                'date': current_date.strftime('%Y-%m-%d'),
                'year': current_date.year,
                'month': current_date.month,
                'transactions': transactions,
                'in_branch_transactions': int(transactions * region['in_branch_preference']),
                'digital_transactions': int(transactions * region['digital_adoption_rate'])
            })
    
    return pd.DataFrame(time_series_data)


# ============================================
# 4. MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("🏦 Generating TD Banking Analytics Data...\n")
    
    # Generate datasets
    print("📍 Generating branch data...")
    df_branches = generate_branches()
    print(f"   ✓ Created {len(df_branches)} branches")
    
    print("\n📊 Generating regional demand data...")
    df_regions = generate_regional_demand()
    print(f"   ✓ Created {len(df_regions)} regions")
    
    print("\n📈 Generating time series data (36 months)...")
    df_timeseries = generate_time_series(df_regions)
    print(f"   ✓ Created {len(df_timeseries)} monthly records")
    
    # Save to CSV files
    print("\n💾 Saving files...")
    df_branches.to_csv('data/raw/branches.csv', index=False)
    df_regions.to_csv('data/raw/regional_demand.csv', index=False)
    df_timeseries.to_csv('data/raw/transactions_timeseries.csv', index=False)
    
    print("   ✓ branches.csv")
    print("   ✓ regional_demand.csv")
    print("   ✓ transactions_timeseries.csv")
    
    # Display sample data
    print("\n" + "="*60)
    print("📋 SAMPLE DATA PREVIEW")
    print("="*60)
    
    print("\n🏢 Branches (first 3):")
    print(df_branches.head(3).to_string(index=False))
    
    print("\n\n📍 Regional Demand (first 3):")
    print(df_regions.head(3).to_string(index=False))
    
    print("\n\n📅 Time Series (first 3):")
    print(df_timeseries.head(3).to_string(index=False))
    
    # Summary statistics
    print("\n" + "="*60)
    print("📊 SUMMARY STATISTICS")
    print("="*60)
    
    print(f"\nTotal branches: {len(df_branches)}")
    print(f"Branches by province:")
    print(df_branches['province'].value_counts().to_string())
    
    print(f"\n\nTotal regions: {len(df_regions)}")
    print(f"Total population covered: {df_regions['population'].sum():,}")
    print(f"Avg digital adoption: {df_regions['digital_adoption_rate'].mean():.1%}")
    
    print(f"\n\nTime series records: {len(df_timeseries)}")
    print(f"Date range: {df_timeseries['date'].min()} to {df_timeseries['date'].max()}")
    
    print("\n✅ Data generation complete! Ready for SQL setup.\n")