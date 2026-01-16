-- ============================================
-- TD BANKING ANALYTICS - SQL QUERIES
-- Key business questions answered through SQL
-- ============================================

-- ============================================
-- QUERY 1: Regional Transaction Aggregation
-- Business Question: Which regions have highest transaction volumes?
-- ============================================

SELECT 
    province,
    region_name,
    SUM(avg_monthly_transactions) AS total_monthly_transactions,
    AVG(digital_adoption_rate) AS avg_digital_adoption,
    SUM(population) AS total_population
FROM regional_demand
GROUP BY province, region_name
ORDER BY total_monthly_transactions DESC
LIMIT 10;


-- ============================================
-- QUERY 2: Branch Performance by Province
-- Business Question: How are branches performing across provinces?
-- ============================================

SELECT 
    province,
    COUNT(branch_id) AS branch_count,
    AVG(staff_count) AS avg_staff,
    SUM(monthly_transactions) AS total_transactions,
    AVG(transactions_per_staff) AS avg_transactions_per_staff,
    ROUND(SUM(monthly_transactions) * 1.0 / COUNT(branch_id), 0) AS avg_transactions_per_branch
FROM branches
GROUP BY province
ORDER BY total_transactions DESC;


-- ============================================
-- QUERY 3: Identify Underserved Regions
-- Business Question: Which high-demand regions lack sufficient branch coverage?
-- ============================================

SELECT 
    r.province,
    r.region_name,
    r.population,
    r.avg_monthly_transactions,
    r.demand_score,
    COUNT(b.branch_id) AS branch_count,
    r.avg_monthly_transactions / NULLIF(COUNT(b.branch_id), 0) AS transactions_per_branch,
    CASE 
        WHEN COUNT(b.branch_id) = 0 THEN 'No Coverage'
        WHEN r.avg_monthly_transactions / COUNT(b.branch_id) > 100000 THEN 'Severely Underserved'
        WHEN r.avg_monthly_transactions / COUNT(b.branch_id) > 50000 THEN 'Underserved'
        ELSE 'Adequate Coverage'
    END AS coverage_status
FROM regional_demand r
LEFT JOIN branches b ON r.province = b.province
GROUP BY r.province, r.region_name, r.population, 
         r.avg_monthly_transactions, r.demand_score
HAVING coverage_status IN ('No Coverage', 'Severely Underserved', 'Underserved')
ORDER BY r.demand_score DESC;


-- ============================================
-- QUERY 4: Branch Capacity vs Regional Demand
-- Business Question: Are branches operating beyond capacity?
-- ============================================

SELECT 
    b.province,
    b.branch_id,
    b.branch_type,
    b.staff_count,
    b.monthly_transactions,
    b.transactions_per_staff,
    r.avg_monthly_transactions AS regional_demand,
    CASE 
        WHEN b.transactions_per_staff > 800 THEN 'Overloaded'
        WHEN b.transactions_per_staff > 600 THEN 'High Utilization'
        WHEN b.transactions_per_staff > 400 THEN 'Normal'
        ELSE 'Underutilized'
    END AS capacity_status
FROM branches b
JOIN regional_demand r ON b.province = r.province
WHERE b.transactions_per_staff > 700
ORDER BY b.transactions_per_staff DESC
LIMIT 20;


-- ============================================
-- QUERY 5: Time Series - Transaction Growth by Province
-- Business Question: How have transactions grown over time?
-- ============================================

SELECT 
    province,
    year,
    month,
    SUM(transactions) AS total_transactions,
    SUM(in_branch_transactions) AS in_branch_total,
    SUM(digital_transactions) AS digital_total,
    ROUND(100.0 * SUM(digital_transactions) / SUM(transactions), 2) AS digital_percentage
FROM transactions_timeseries
GROUP BY province, year, month
ORDER BY province, year, month;


-- ============================================
-- QUERY 6: Seasonal Transaction Patterns
-- Business Question: Which months have highest transaction volumes?
-- ============================================

SELECT 
    month,
    CASE month
        WHEN 1 THEN 'January'
        WHEN 2 THEN 'February'
        WHEN 3 THEN 'March'
        WHEN 4 THEN 'April'
        WHEN 5 THEN 'May'
        WHEN 6 THEN 'June'
        WHEN 7 THEN 'July'
        WHEN 8 THEN 'August'
        WHEN 9 THEN 'September'
        WHEN 10 THEN 'October'
        WHEN 11 THEN 'November'
        WHEN 12 THEN 'December'
    END AS month_name,
    AVG(transactions) AS avg_transactions,
    MIN(transactions) AS min_transactions,
    MAX(transactions) AS max_transactions
FROM transactions_timeseries
GROUP BY month
ORDER BY month;


-- ============================================
-- QUERY 7: Digital vs In-Branch Adoption by Region
-- Business Question: Where is digital banking growing fastest?
-- ============================================

SELECT 
    r.region_name,
    r.province,
    r.digital_adoption_rate,
    AVG(t.digital_transactions) AS avg_digital_monthly,
    AVG(t.in_branch_transactions) AS avg_inbranch_monthly,
    ROUND(100.0 * AVG(t.digital_transactions) / 
          (AVG(t.digital_transactions) + AVG(t.in_branch_transactions)), 2) AS digital_share_pct
FROM regional_demand r
JOIN transactions_timeseries t ON r.region_id = t.region_id
GROUP BY r.region_name, r.province, r.digital_adoption_rate
ORDER BY digital_share_pct DESC
LIMIT 15;


-- ============================================
-- QUERY 8: Province-Level Summary Dashboard
-- Business Question: Executive summary by province
-- ============================================

SELECT 
    r.province,
    COUNT(DISTINCT r.region_id) AS region_count,
    COUNT(DISTINCT b.branch_id) AS branch_count,
    SUM(r.population) AS total_population,
    ROUND(AVG(r.median_income), 0) AS avg_median_income,
    SUM(b.monthly_transactions) AS total_branch_capacity,
    SUM(r.avg_monthly_transactions) AS total_regional_demand,
    SUM(r.avg_monthly_transactions) - SUM(b.monthly_transactions) AS demand_gap,
    ROUND(AVG(r.digital_adoption_rate) * 100, 1) AS avg_digital_adoption_pct
FROM regional_demand r
LEFT JOIN branches b ON r.province = b.province
GROUP BY r.province
ORDER BY total_regional_demand DESC;


-- ============================================
-- QUERY 9: High-Value Target Regions for Expansion
-- Business Question: Where should we open new branches?
-- ============================================

SELECT 
    r.region_name,
    r.province,
    r.population,
    r.median_income,
    r.demand_score,
    r.avg_monthly_transactions,
    COUNT(b.branch_id) AS current_branches,
    ROUND(r.avg_monthly_transactions / NULLIF(COUNT(b.branch_id), 0), 0) AS demand_per_branch,
    CASE 
        WHEN r.demand_score > 3 AND COUNT(b.branch_id) < 3 THEN 'High Priority'
        WHEN r.demand_score > 2 AND COUNT(b.branch_id) < 5 THEN 'Medium Priority'
        ELSE 'Low Priority'
    END AS expansion_priority
FROM regional_demand r
LEFT JOIN branches b ON r.province = b.province
GROUP BY r.region_name, r.province, r.population, 
         r.median_income, r.demand_score, r.avg_monthly_transactions
HAVING expansion_priority IN ('High Priority', 'Medium Priority')
ORDER BY r.demand_score DESC, current_branches ASC;


-- ============================================
-- QUERY 10: Recent Transaction Trends (Last 6 Months)
-- Business Question: What are the most recent trends?
-- ============================================

SELECT 
    region_name,
    province,
    date,
    transactions,
    digital_transactions,
    in_branch_transactions,
    LAG(transactions, 1) OVER (PARTITION BY region_name ORDER BY date) AS prev_month_transactions,
    ROUND(100.0 * (transactions - LAG(transactions, 1) OVER (PARTITION BY region_name ORDER BY date)) / 
          NULLIF(LAG(transactions, 1) OVER (PARTITION BY region_name ORDER BY date), 0), 2) AS month_over_month_growth_pct
FROM transactions_timeseries
WHERE date >= '2023-07-01'
ORDER BY region_name, date DESC
LIMIT 50;