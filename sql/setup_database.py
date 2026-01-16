import sqlite3
import pandas as pd
import os

def create_database():
    """Create SQLite database and load all data"""
    
    # Connect to database (creates if doesn't exist)
    db_path = 'data/td_banking.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🗄️  Creating TD Banking Database...\n")
    
    # 1. CREATE BRANCHES TABLE
    print("📍 Creating branches table...")
    
    cursor.execute("""
        DROP TABLE IF EXISTS branches
    """)
    
    cursor.execute("""
        CREATE TABLE branches (
            branch_id TEXT PRIMARY KEY,
            province TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            staff_count INTEGER NOT NULL,
            branch_type TEXT NOT NULL,
            opening_year INTEGER NOT NULL,
            monthly_transactions INTEGER NOT NULL,
            transactions_per_staff REAL NOT NULL,
            CHECK (latitude BETWEEN 41.0 AND 60.0),
            CHECK (longitude BETWEEN -141.0 AND -52.0),
            CHECK (staff_count > 0),
            CHECK (monthly_transactions >= 0)
        )
    """)
    
    # Load branches data
    df_branches = pd.read_csv('data/raw/branches.csv')
    df_branches.to_sql('branches', conn, if_exists='replace', index=False)
    
    print(f"   ✓ Loaded {len(df_branches)} branches")
    
    # ============================================
    # 2. CREATE REGIONAL DEMAND TABLE
    # ============================================
    print("\n📊 Creating regional_demand table...")
    
    cursor.execute("""
        DROP TABLE IF EXISTS regional_demand
    """)
    
    cursor.execute("""
        CREATE TABLE regional_demand (
            region_id TEXT PRIMARY KEY,
            region_name TEXT NOT NULL,
            province TEXT NOT NULL,
            population INTEGER NOT NULL,
            median_income INTEGER NOT NULL,
            digital_adoption_rate REAL NOT NULL,
            avg_monthly_transactions INTEGER NOT NULL,
            in_branch_preference REAL NOT NULL,
            small_business_density INTEGER NOT NULL,
            demand_score REAL NOT NULL,
            CHECK (population > 0),
            CHECK (median_income > 0),
            CHECK (digital_adoption_rate BETWEEN 0 AND 1),
            CHECK (in_branch_preference BETWEEN 0 AND 1)
        )
    """)
    
    # Load regional demand data
    df_regions = pd.read_csv('data/raw/regional_demand.csv')
    df_regions.to_sql('regional_demand', conn, if_exists='replace', index=False)
    
    print(f"   ✓ Loaded {len(df_regions)} regions")
    
    # ============================================
    # 3. CREATE TIME SERIES TABLE
    # ============================================
    print("\n📈 Creating transactions_timeseries table...")
    
    cursor.execute("""
        DROP TABLE IF EXISTS transactions_timeseries
    """)
    
    cursor.execute("""
        CREATE TABLE transactions_timeseries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_id TEXT NOT NULL,
            region_name TEXT NOT NULL,
            province TEXT NOT NULL,
            date TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            transactions INTEGER NOT NULL,
            in_branch_transactions INTEGER NOT NULL,
            digital_transactions INTEGER NOT NULL,
            FOREIGN KEY (region_id) REFERENCES regional_demand(region_id),
            CHECK (transactions >= 0),
            CHECK (month BETWEEN 1 AND 12)
        )
    """)
    
    # Load time series data
    df_timeseries = pd.read_csv('data/raw/transactions_timeseries.csv')
    df_timeseries.to_sql('transactions_timeseries', conn, if_exists='replace', index=False)
    
    print(f"   ✓ Loaded {len(df_timeseries)} monthly records")
    
    # ============================================
    # 4. CREATE INDEXES FOR PERFORMANCE
    # ============================================
    print("\n🔍 Creating indexes for query performance...")
    
    indexes = [
        "CREATE INDEX idx_branches_province ON branches(province)",
        "CREATE INDEX idx_regions_province ON regional_demand(province)",
        "CREATE INDEX idx_timeseries_region ON transactions_timeseries(region_id)",
        "CREATE INDEX idx_timeseries_date ON transactions_timeseries(date)",
        "CREATE INDEX idx_timeseries_province ON transactions_timeseries(province)",
    ]
    
    for idx_query in indexes:
        cursor.execute(idx_query)
    
    print(f"   ✓ Created {len(indexes)} indexes")
    
    # ============================================
    # 5. CREATE ANALYTICAL VIEWS
    # ============================================
    print("\n👁️  Creating analytical views...")
    
    # View 1: Branch Performance Summary
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_branch_performance AS
        SELECT 
            b.branch_id,
            b.province,
            b.branch_type,
            b.staff_count,
            b.monthly_transactions,
            b.transactions_per_staff,
            CASE 
                WHEN b.transactions_per_staff > 800 THEN 'High Load'
                WHEN b.transactions_per_staff > 500 THEN 'Moderate Load'
                ELSE 'Low Load'
            END AS capacity_status
        FROM branches b
    """)
    
    # View 2: Regional Demand Summary
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_regional_summary AS
        SELECT 
            r.region_id,
            r.region_name,
            r.province,
            r.population,
            r.avg_monthly_transactions,
            r.demand_score,
            COUNT(DISTINCT b.branch_id) AS branch_count,
            COALESCE(SUM(b.monthly_transactions), 0) AS total_branch_capacity,
            r.avg_monthly_transactions - COALESCE(SUM(b.monthly_transactions), 0) AS capacity_gap
        FROM regional_demand r
        LEFT JOIN branches b ON r.province = b.province
        GROUP BY r.region_id, r.region_name, r.province, 
                 r.population, r.avg_monthly_transactions, r.demand_score
    """)
    
    print("   ✓ Created 2 analytical views")
    
    # ============================================
    # 6. VERIFY DATA INTEGRITY
    # ============================================
    print("\n✅ Verifying data integrity...")
    
    # Check record counts
    tables = ['branches', 'regional_demand', 'transactions_timeseries']
    for table in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"   ✓ {table}: {count} records")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Database created successfully: {db_path}")
    print("\nNext step: Run analytical queries!")

if __name__ == "__main__":
    create_database()