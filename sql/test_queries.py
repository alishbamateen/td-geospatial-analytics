"""
Test queries to validate the fixed database
Shows key insights that TD would care about
"""

import sqlite3
import pandas as pd

def run_test_queries():
    """Run analytical queries to test database"""
    
    conn = sqlite3.connect('data/td_banking.db')
    
    print("="*70)
    print("TD BANKING ANALYTICS - KEY INSIGHTS")
    print("="*70)
    
    # ============================================
    # Query 1: Underserved Regions
    # ============================================
    print("\n🔍 UNDERSERVED REGIONS (High demand, low coverage):\n")
    
    query1 = """
    SELECT 
        r.region_name,
        r.province,
        r.demand_score,
        r.avg_monthly_transactions as regional_demand,
        COUNT(b.branch_id) AS branch_count,
        COALESCE(SUM(b.monthly_transactions), 0) AS branch_capacity,
        r.avg_monthly_transactions - COALESCE(SUM(b.monthly_transactions), 0) AS capacity_gap
    FROM regional_demand r
    LEFT JOIN branches b ON r.region_id = b.region_id
    GROUP BY r.region_id, r.region_name, r.province, r.demand_score, r.avg_monthly_transactions
    HAVING capacity_gap > 50000
    ORDER BY capacity_gap DESC
    LIMIT 10
    """
    
    df1 = pd.read_sql_query(query1, conn)
    print(df1.to_string(index=False))
    
    # ============================================
    # Query 2: Branch Distribution by Province
    # ============================================
    print("\n\n📊 BRANCH DISTRIBUTION BY PROVINCE:\n")
    
    query2 = """
    SELECT 
        province,
        COUNT(DISTINCT region_id) as regions,
        COUNT(branch_id) AS branches,
        ROUND(AVG(staff_count), 1) AS avg_staff,
        SUM(monthly_transactions) AS total_capacity
    FROM branches
    GROUP BY province
    ORDER BY total_capacity DESC
    """
    
    df2 = pd.read_sql_query(query2, conn)
    print(df2.to_string(index=False))
    
    # ============================================
    # Query 3: Overloaded Branches
    # ============================================
    print("\n\n⚠️  OVERLOADED BRANCHES (>700 transactions per staff):\n")
    
    query3 = """
    SELECT 
        branch_id,
        region_name,
        province,
        staff_count,
        monthly_transactions,
        transactions_per_staff,
        CASE 
            WHEN transactions_per_staff > 900 THEN 'Critical'
            WHEN transactions_per_staff > 700 THEN 'High'
            ELSE 'Normal'
        END AS load_status
    FROM branches
    WHERE transactions_per_staff > 700
    ORDER BY transactions_per_staff DESC
    LIMIT 10
    """
    
    df3 = pd.read_sql_query(query3, conn)
    print(df3.to_string(index=False))
    
    # ============================================
    # Query 4: Regional Coverage Status
    # ============================================
    print("\n\n🎯 REGIONAL COVERAGE STATUS:\n")
    
    query4 = """
    SELECT 
        coverage_status,
        COUNT(*) as region_count,
        ROUND(AVG(demand_score), 2) as avg_demand_score,
        ROUND(AVG(branch_count), 1) as avg_branches
    FROM vw_regional_summary
    GROUP BY coverage_status
    ORDER BY 
        CASE coverage_status
            WHEN 'No Coverage' THEN 1
            WHEN 'Underserved' THEN 2
            WHEN 'Balanced' THEN 3
            WHEN 'Oversupplied' THEN 4
        END
    """
    
    df4 = pd.read_sql_query(query4, conn)
    print(df4.to_string(index=False))
    
    # ============================================
    # Query 5: Top Expansion Opportunities
    # ============================================
    print("\n\n🚀 TOP EXPANSION OPPORTUNITIES:\n")
    
    query5 = """
    SELECT 
        region_name,
        province,
        demand_score,
        population,
        branch_count,
        capacity_gap,
        coverage_status
    FROM vw_regional_summary
    WHERE coverage_status IN ('No Coverage', 'Underserved')
    ORDER BY demand_score DESC
    LIMIT 10
    """
    
    df5 = pd.read_sql_query(query5, conn)
    print(df5.to_string(index=False))
    
    # ============================================
    # Summary Stats
    # ============================================
    print("\n" + "="*70)
    print("📈 SUMMARY STATISTICS")
    print("="*70 + "\n")
    
    total_branches = pd.read_sql_query("SELECT COUNT(*) as cnt FROM branches", conn).iloc[0]['cnt']
    total_regions = pd.read_sql_query("SELECT COUNT(*) as cnt FROM regional_demand", conn).iloc[0]['cnt']
    underserved = pd.read_sql_query(
        "SELECT COUNT(*) as cnt FROM vw_regional_summary WHERE coverage_status = 'Underserved'", 
        conn
    ).iloc[0]['cnt']
    
    print(f"Total Branches: {total_branches}")
    print(f"Total Regions: {total_regions}")
    print(f"Underserved Regions: {underserved}")
    print(f"Coverage Rate: {(1 - underserved/total_regions)*100:.1f}%")
    
    conn.close()
    
    print("\n✅ All queries executed successfully!\n")

if __name__ == "__main__":
    run_test_queries()