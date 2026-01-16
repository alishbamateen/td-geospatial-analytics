import pandas as pd
import sqlite3
from datetime import datetime

print("📊 Preparing data for Tableau Dashboard...\n")

conn = sqlite3.connect('data/td_banking.db')

# 1. BRANCH PERFORMANCE DATA

print("🏢 Exporting branch performance data...")

df_branches = pd.read_sql_query("""
    SELECT 
        b.branch_id,
        b.province,
        b.region_id,
        b.region_name,
        b.latitude,
        b.longitude,
        b.staff_count,
        b.branch_type,
        b.opening_year,
        b.monthly_transactions,
        b.transactions_per_staff,
        CASE 
            WHEN b.transactions_per_staff > 900 THEN 'Critical'
            WHEN b.transactions_per_staff > 700 THEN 'High'
            WHEN b.transactions_per_staff > 500 THEN 'Moderate'
            ELSE 'Normal'
        END AS load_status,
        CASE 
            WHEN b.transactions_per_staff > 900 THEN 4
            WHEN b.transactions_per_staff > 700 THEN 3
            WHEN b.transactions_per_staff > 500 THEN 2
            ELSE 1
        END AS load_severity
    FROM branches b
""", conn)

df_branches.to_csv('dashboard/tableau_branches.csv', index=False)
print(f"   ✓ tableau_branches.csv ({len(df_branches)} records)")


# 2. REGIONAL SUMMARY DATA

print("\n📍 Exporting regional summary data...")

df_regional = pd.read_sql_query("""
    SELECT 
        r.region_id,
        r.region_name,
        r.province,
        r.population,
        r.median_income,
        r.digital_adoption_rate,
        r.avg_monthly_transactions AS regional_demand,
        r.in_branch_preference,
        r.small_business_density,
        r.demand_score,
        v.branch_count,
        v.total_branch_capacity,
        v.capacity_gap,
        v.coverage_status,
        CASE v.coverage_status
            WHEN 'No Coverage' THEN 1
            WHEN 'Underserved' THEN 2
            WHEN 'Balanced' THEN 3
            WHEN 'Oversupplied' THEN 4
        END AS coverage_rank
    FROM regional_demand r
    LEFT JOIN vw_regional_summary v ON r.region_id = v.region_id
""", conn)

# Calculate average lat/lon for regions
region_coords = pd.read_sql_query("""
    SELECT 
        region_id,
        AVG(latitude) as latitude,
        AVG(longitude) as longitude
    FROM branches
    GROUP BY region_id
""", conn)

df_regional = df_regional.merge(region_coords, on='region_id', how='left')

df_regional.to_csv('dashboard/tableau_regional_summary.csv', index=False)
print(f"   ✓ tableau_regional_summary.csv ({len(df_regional)} records)")

# 3. TIME SERIES DATA

print("\n📈 Exporting time series data...")

df_timeseries = pd.read_sql_query("""
    SELECT 
        region_id,
        region_name,
        province,
        date,
        year,
        month,
        transactions,
        in_branch_transactions,
        digital_transactions,
        ROUND(100.0 * digital_transactions / transactions, 2) AS digital_percentage
    FROM transactions_timeseries
    ORDER BY date
""", conn)

df_timeseries.to_csv('dashboard/tableau_timeseries.csv', index=False)
print(f"   ✓ tableau_timeseries.csv ({len(df_timeseries)} records)")

# 4. KPI SUMMARY DATA

print("\n📊 Creating KPI summary...")

# Calculate key metrics
total_branches = df_branches.shape[0]
total_regions = df_regional.shape[0]
underserved_regions = len(df_regional[df_regional['coverage_status'] == 'Underserved'])
coverage_rate = round((1 - underserved_regions / total_regions) * 100, 1)

overloaded_branches = len(df_branches[df_branches['load_status'].isin(['Critical', 'High'])])
total_capacity = df_branches['monthly_transactions'].sum()
total_demand = df_regional['regional_demand'].sum()
total_gap = total_demand - total_capacity

avg_transactions_per_staff = df_branches['transactions_per_staff'].mean()

kpi_data = {
    'Metric': [
        'Total Branches',
        'Total Regions',
        'Underserved Regions',
        'Coverage Rate (%)',
        'Overloaded Branches',
        'Total Monthly Capacity',
        'Total Monthly Demand',
        'Capacity Gap',
        'Avg Transactions per Staff'
    ],
    'Value': [
        total_branches,
        total_regions,
        underserved_regions,
        coverage_rate,
        overloaded_branches,
        total_capacity,
        total_demand,
        total_gap,
        round(avg_transactions_per_staff, 0)
    ],
    'Category': [
        'Branch Metrics',
        'Regional Metrics',
        'Regional Metrics',
        'Regional Metrics',
        'Branch Metrics',
        'Capacity Metrics',
        'Capacity Metrics',
        'Capacity Metrics',
        'Efficiency Metrics'
    ]
}

df_kpi = pd.DataFrame(kpi_data)
df_kpi.to_csv('dashboard/tableau_kpis.csv', index=False)
print(f"   ✓ tableau_kpis.csv ({len(df_kpi)} records)")

# 5. EXPANSION RECOMMENDATIONS

print("\n🎯 Creating expansion recommendations...")

df_expansion = df_regional[df_regional['coverage_status'] == 'Underserved'].copy()
df_expansion = df_expansion.sort_values('demand_score', ascending=False)

# Calculate recommendations
df_expansion['branches_needed'] = (df_expansion['capacity_gap'] / 10000).round(0).astype(int)
df_expansion['staff_needed'] = (df_expansion['capacity_gap'] / 600).round(0).astype(int)
df_expansion['priority_rank'] = range(1, len(df_expansion) + 1)

df_expansion['recommendation'] = df_expansion.apply(lambda x: 
    f"Open {x['branches_needed']} new branches, hire {x['staff_needed']} staff" 
    if x['branches_needed'] > 0 
    else f"Increase staffing by {x['staff_needed']}", axis=1)

df_expansion['priority_level'] = df_expansion['demand_score'].apply(lambda x:
    'High Priority' if x > 2.5 else 'Medium Priority' if x > 2.0 else 'Low Priority')

df_expansion_export = df_expansion[[
    'priority_rank', 'region_name', 'province', 'population', 'demand_score',
    'regional_demand', 'total_branch_capacity', 'capacity_gap', 'branch_count',
    'branches_needed', 'staff_needed', 'priority_level', 'recommendation',
    'latitude', 'longitude'
]]

df_expansion_export.to_csv('dashboard/tableau_expansion_recommendations.csv', index=False)
print(f"   ✓ tableau_expansion_recommendations.csv ({len(df_expansion_export)} records)")


# 6. PROVINCE SUMMARY

print("\n🗺️  Creating province-level summary...")

df_province = pd.read_sql_query("""
    SELECT 
        b.province,
        COUNT(DISTINCT b.branch_id) as branch_count,
        COUNT(DISTINCT b.region_id) as region_count,
        SUM(b.monthly_transactions) as total_capacity,
        AVG(b.staff_count) as avg_staff_per_branch,
        AVG(b.transactions_per_staff) as avg_transactions_per_staff
    FROM branches b
    GROUP BY b.province
""", conn)

# Add regional demand
province_demand = pd.read_sql_query("""
    SELECT 
        province,
        SUM(population) as total_population,
        SUM(avg_monthly_transactions) as total_demand,
        AVG(median_income) as avg_income,
        AVG(digital_adoption_rate) as avg_digital_adoption
    FROM regional_demand
    GROUP BY province
""", conn)

df_province = df_province.merge(province_demand, on='province', how='left')
df_province['capacity_gap'] = df_province['total_demand'] - df_province['total_capacity']
df_province['coverage_ratio'] = (df_province['total_capacity'] / df_province['total_demand'] * 100).round(1)

df_province.to_csv('dashboard/tableau_province_summary.csv', index=False)
print(f"   ✓ tableau_province_summary.csv ({len(df_province)} records)")

conn.close()

# ============================================
# 7. CREATE DATA DICTIONARY
# ============================================

print("\n📖 Creating data dictionary...")

data_dict = """
TD BANKING ANALYTICS - TABLEAU DATA DICTIONARY
==============================================

FILE: tableau_branches.csv
- branch_id: Unique branch identifier
- province: Province location
- region_name: Specific region within province
- latitude/longitude: Geographic coordinates
- staff_count: Number of employees
- branch_type: Full Service, Express, or Flagship
- monthly_transactions: Average monthly transaction volume
- transactions_per_staff: Efficiency metric
- load_status: Critical/High/Moderate/Normal (workload indicator)
- load_severity: Numeric ranking (4=Critical, 1=Normal)

FILE: tableau_regional_summary.csv
- region_id: Unique region identifier
- region_name: Region name
- province: Province
- population: Total population in region
- regional_demand: Monthly transaction demand
- branch_count: Number of branches in region
- total_branch_capacity: Combined capacity of all branches
- capacity_gap: Demand minus capacity (positive = underserved)
- coverage_status: Underserved/Balanced/Oversupplied
- demand_score: Composite demand metric (higher = more demand)

FILE: tableau_timeseries.csv
- date: Month/year
- region_name: Region
- transactions: Total monthly transactions
- digital_transactions: Online/mobile transactions
- in_branch_transactions: Physical branch transactions
- digital_percentage: % of transactions that are digital

FILE: tableau_kpis.csv
- Metric: KPI name
- Value: KPI value
- Category: Grouping for filtering

FILE: tableau_expansion_recommendations.csv
- priority_rank: 1 = highest priority
- region_name: Target region
- capacity_gap: Unmet demand
- branches_needed: Recommended new branches
- staff_needed: Recommended new hires
- priority_level: High/Medium/Low
- recommendation: Action description

FILE: tableau_province_summary.csv
- province: Province name
- branch_count: Total branches
- total_capacity: Combined branch capacity
- total_demand: Total regional demand
- capacity_gap: Province-level shortage
- coverage_ratio: % of demand being met
"""

with open('dashboard/data_dictionary.txt', 'w') as f:
    f.write(data_dict)

print("   ✓ data_dictionary.txt")

print("\n" + "="*70)
print("✅ TABLEAU DATA PREPARATION COMPLETE!")
print("="*70)
print("\nFiles created in dashboard/ folder:")
print("  • tableau_branches.csv")
print("  • tableau_regional_summary.csv")
print("  • tableau_timeseries.csv")
print("  • tableau_kpis.csv")
print("  • tableau_expansion_recommendations.csv")
print("  • tableau_province_summary.csv")
print("  • data_dictionary.txt")
print("\nReady to import into Tableau!")
print("Next: Follow the dashboard build guide\n")