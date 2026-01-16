import pandas as pd
import numpy as np
import sqlite3

def assign_branches_to_regions():
    """Assign each branch to a specific region within its province"""
    
    print("🔧 Fixing branch-to-region assignments...\n")
    
    # Load data
    df_branches = pd.read_csv('data/raw/branches.csv')
    df_regions = pd.read_csv('data/raw/regional_demand.csv')
    
    # Create a mapping: for each branch, assign it to a region in the same province
    branches_with_regions = []
    
    for province in df_branches['province'].unique():
        # Get branches in this province
        province_branches = df_branches[df_branches['province'] == province]
        
        # Get regions in this province
        province_regions = df_regions[df_regions['province'] == province]
        
        if len(province_regions) == 0:
            print(f"   ⚠️  Warning: No regions found for {province}")
            continue
        
        # Assign branches to regions (weighted by demand_score)
        region_weights = province_regions['demand_score'].values
        region_weights = region_weights / region_weights.sum()  # Normalize
        
        for _, branch in province_branches.iterrows():
            # Randomly assign based on demand weights
            # (higher demand regions get more branches)
            assigned_region = np.random.choice(
                province_regions['region_id'].values,
                p=region_weights
            )
            
            region_info = province_regions[province_regions['region_id'] == assigned_region].iloc[0]
            
            branch_copy = branch.to_dict()
            branch_copy['region_id'] = assigned_region
            branch_copy['region_name'] = region_info['region_name']
            
            branches_with_regions.append(branch_copy)
    
    df_branches_updated = pd.DataFrame(branches_with_regions)
    
    # Save updated branches file
    df_branches_updated.to_csv('data/raw/branches.csv', index=False)
    print(f"   ✓ Updated {len(df_branches_updated)} branch assignments")
    
    # Show distribution
    print("\n📊 Branches per region (top 10):")
    distribution = df_branches_updated.groupby('region_name').size().sort_values(ascending=False).head(10)
    for region, count in distribution.items():
        print(f"   {region}: {count} branches")
    
    # Update database
    print("\n🗄️  Updating database...")
    conn = sqlite3.connect('data/td_banking.db')
    
    # Drop and recreate branches table with region_id
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS branches")
    
    cursor.execute("""
        CREATE TABLE branches (
            branch_id TEXT PRIMARY KEY,
            province TEXT NOT NULL,
            region_id TEXT NOT NULL,
            region_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            staff_count INTEGER NOT NULL,
            branch_type TEXT NOT NULL,
            opening_year INTEGER NOT NULL,
            monthly_transactions INTEGER NOT NULL,
            transactions_per_staff REAL NOT NULL,
            FOREIGN KEY (region_id) REFERENCES regional_demand(region_id)
        )
    """)
    
    df_branches_updated.to_sql('branches', conn, if_exists='replace', index=False)
    
    # Recreate indexes
    cursor.execute("CREATE INDEX idx_branches_province ON branches(province)")
    cursor.execute("CREATE INDEX idx_branches_region ON branches(region_id)")
    
    # Update the regional summary view
    cursor.execute("DROP VIEW IF EXISTS vw_regional_summary")
    cursor.execute("""
        CREATE VIEW vw_regional_summary AS
        SELECT 
            r.region_id,
            r.region_name,
            r.province,
            r.population,
            r.avg_monthly_transactions AS regional_demand,
            r.demand_score,
            COUNT(DISTINCT b.branch_id) AS branch_count,
            COALESCE(SUM(b.monthly_transactions), 0) AS total_branch_capacity,
            r.avg_monthly_transactions - COALESCE(SUM(b.monthly_transactions), 0) AS capacity_gap,
            CASE 
                WHEN COUNT(DISTINCT b.branch_id) = 0 THEN 'No Coverage'
                WHEN r.avg_monthly_transactions / COALESCE(SUM(b.monthly_transactions), 1) > 2 THEN 'Underserved'
                WHEN r.avg_monthly_transactions / COALESCE(SUM(b.monthly_transactions), 1) < 0.5 THEN 'Oversupplied'
                ELSE 'Balanced'
            END AS coverage_status
        FROM regional_demand r
        LEFT JOIN branches b ON r.region_id = b.region_id
        GROUP BY r.region_id, r.region_name, r.province, 
                 r.population, r.avg_monthly_transactions, r.demand_score
    """)
    
    conn.commit()
    conn.close()
    

if __name__ == "__main__":
    np.random.seed(42)  # For reproducibility
    assign_branches_to_regions()