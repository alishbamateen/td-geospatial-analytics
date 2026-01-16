# Banking Analytics: Geospatial Customer Demand & Branch Performance

**An end-to-end analytics solution using Python, SQL, and Tableau to analyze regional customer demand, forecast service needs, and recommend branch optimization strategies.**

![Python](https://img.shields.io/badge/Python-3.11-blue)
![SQL](https://img.shields.io/badge/SQL-SQLite-orange)
![Tableau](https://img.shields.io/badge/Tableau-Dashboard-green)

---

## 📋 Project Overview

### Business Problem
*"How can a bank identify regions with high customer demand but insufficient service coverage, and forecast future demand to support branch or resource planning?"*

This project addresses a critical challenge in banking operations: ensuring branches are located where customers need them most, while optimizing staffing levels to meet demand.

### Key Findings
- **9 underserved regions** identified with 100K-200K+ monthly transaction gaps
- **10 critically overloaded branches** operating at 1800+ transactions per staff
- **62.5% regional coverage rate** indicates significant expansion opportunities
- **2.47M monthly transaction gap** across all regions represents lost revenue

---

## 📊 Live Interactive Dashboard

Explore the full interactive Tableau dashboard: [View Live Dashboard](https://public.tableau.com/views/Book1_17685482509600/Dashboard1?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

### Preview of Dashboard:
<img width="621" height="768" alt="Screenshot 2026-01-16 at 2 32 59 AM" src="https://github.com/user-attachments/assets/1275988f-327d-44a0-b283-fe2965abd1c2" />


**Dashboard Features:**
- Filter by province
- Interactive map with branch details
- Real-time KPI metrics
- Click-through drill-downs


## 🗺️ Live Interactive Map

Explore the interactive branch map: [View Live Map](https://alishbamateen.github.io/td-geospatial-analytics/data/processed/branch_demand_map.html)

## 🎯 Business Impact

### Actionable Recommendations
1. **Immediate Expansion**: Open 3-4 branches in Richmond, BC and Hamilton, ON (highest demand gaps)
2. **Staffing Optimization**: Redistribute 15-20 staff from underutilized branches to overloaded locations
3. **Digital Strategy**: Focus on regions with <50% digital adoption to reduce in-branch load
4. **6-Month Forecast**: Projected 5-8% demand growth requires proactive capacity planning

### Expected Outcomes
- Reduce customer wait times by 30-40% in overloaded branches
- Capture $200K+ monthly transactions in underserved markets
- Improve staff efficiency and work-life balance
- Increase customer satisfaction scores

---

## 🛠️ Technical Stack

| Component | Technology |
|-----------|-----------|
| **Data Processing** | Python (pandas, numpy) |
| **Database** | SQLite |
| **Geospatial Analysis** | Folium, Haversine distance |
| **Forecasting** | Time series (Linear trend + Seasonality) |
| **Visualization** | Tableau, Matplotlib |
| **Version Control** | Git/GitHub |

---

## 📊 Project Structure

```
td-geospatial-analytics/
│
├── data/
│   ├── raw/                          # Generated datasets
│   │   ├── branches.csv
│   │   ├── regional_demand.csv
│   │   └── transactions_timeseries.csv
│   ├── processed/                    # Analysis outputs
│   │   ├── underserved_regions.csv
│   │   ├── overloaded_branches.csv
│   │   ├── expansion_recommendations.csv
│   │   └── branch_demand_map.html
│   └── td_banking.db                 # SQLite database
│
├── notebooks/
│   ├── generate_data.py              # Synthetic data creation
│   ├── 02_geospatial_analysis.py     # Spatial analysis & mapping
│   ├── 03_forecasting_analysis.py    # Demand forecasting
│   └── 04_tableau_data_prep.py       # Dashboard data prep
│
├── sql/
│   ├── setup_database.py             # Database schema & setup
│   ├── fix_branches.py               # Branch-region assignment
│   ├── queries.sql                   # Analytical SQL queries
│   └── test_queries.py               # Query validation
│
├── dashboard/
│   ├── tableau_branches.csv          # Tableau data sources
│   ├── tableau_regional_summary.csv
│   ├── tableau_timeseries.csv
│   ├── tableau_kpis.csv
│   ├── tableau_expansion_recommendations.csv
│   ├── tableau_province_summary.csv
│   └── TD_Banking_Analytics.twb      # Tableau workbook
│
└── README.md
```

---

## 🚀 Methodology

### Phase 1: Data Engineering
**Objective**: Create realistic banking datasets for analysis

**Approach**:
- Generated 150 branches across 4 Canadian provinces (ON, BC, AB, QC)
- Created 29 regional markets with demographic data
- Simulated 36 months of transaction history with seasonal patterns
- Assigned branches to regions based on demand-weighted distribution

**Tools**: Python (pandas, numpy)

**Key Outputs**:
- `branches.csv`: 150 branches with location, staffing, transaction volumes
- `regional_demand.csv`: 29 regions with population, income, digital adoption
- `transactions_timeseries.csv`: 1,044 monthly records (36 months × 29 regions)

---

### Phase 2: SQL Database & Analytics
**Objective**: Build queryable database with analytical views

**Approach**:
- Designed normalized schema with proper foreign keys and constraints
- Created indexes for query performance optimization
- Built analytical views for regional coverage and branch performance
- Wrote 10+ SQL queries answering key business questions

**Tools**: SQLite, SQL

**Sample Query** (Identify Underserved Regions):
```sql
SELECT 
    r.region_name,
    r.province,
    r.demand_score,
    r.avg_monthly_transactions AS regional_demand,
    COUNT(b.branch_id) AS branch_count,
    COALESCE(SUM(b.monthly_transactions), 0) AS branch_capacity,
    r.avg_monthly_transactions - COALESCE(SUM(b.monthly_transactions), 0) AS capacity_gap
FROM regional_demand r
LEFT JOIN branches b ON r.region_id = b.region_id
GROUP BY r.region_id
HAVING capacity_gap > 50000
ORDER BY capacity_gap DESC;
```

**Key Insights**:
- Richmond, BC: 161K capacity gap (highest priority)
- Hamilton, ON: 203K capacity gap (most severe)
- 9 total underserved regions identified

---

### Phase 3: Geospatial Analysis
**Objective**: Visualize geographic distribution of demand and capacity

**Approach**:
- Created interactive maps using Folium with multiple layers
- Calculated Haversine distances for accessibility analysis
- Color-coded branches by workload (Critical/High/Moderate/Normal)
- Highlighted underserved regions with warning indicators

**Tools**: Python (folium), HTML/JavaScript

**Deliverables**:
- Interactive HTML map with clickable branch markers
- Branch load status visualization (red = overloaded, green = normal)
- Regional demand heatmap overlay
- Distance-based accessibility metrics

**Key Finding**: Average branch spacing in underserved regions is 12-18km, exceeding optimal 8km radius

---

### Phase 4: Demand Forecasting
**Objective**: Predict future transaction volumes for capacity planning

**Approach**:
- Implemented linear trend analysis with seasonal adjustment
- Calculated monthly growth rates by province and region
- Forecasted 6 months ahead for high-priority regions
- Compared projected demand against current capacity

**Tools**: Python (numpy, matplotlib), Time Series Analysis

**Model**: 
```
Forecast = (Trend × Time) × Seasonal_Factor
where Trend = Linear regression slope
      Seasonal_Factor = Monthly average / baseline
```

**Results**:
- Ontario: +2.1% monthly growth
- British Columbia: +1.8% monthly growth  
- Alberta: +2.5% monthly growth (fastest growing)
- Quebec: +1.2% monthly growth

**6-Month Projections**:
- Richmond, BC: 232K → 268K transactions (+15.5%)
- Hamilton, ON: 261K → 295K transactions (+13%)
- Capacity gaps will increase 10-15% without intervention

---

### Phase 5: Interactive Dashboard
**Objective**: Communicate insights to non-technical stakeholders

**Approach**:
- Designed executive summary with 4 KPI cards
- Created province-level performance comparison chart
- Built interactive branch location map with filters
- Color-coded visualizations for immediate comprehension

**Tools**: Tableau Desktop

**Dashboard Features**:
- **KPI Cards**: Total Branches (150), Underserved Regions (9), Coverage Rate (62.5%), Transaction Gap (2.47M)
- **Province Chart**: Branch count with coverage ratio gradient (green = good, red = poor)
- **Branch Map**: Geographic view with load status color-coding and clickable tooltips
- **Interactivity**: Click province to filter map to that region

---

## 📈 Key Insights & Recommendations

### 1. Geographic Expansion Priorities

| Rank | Region | Province | Demand Gap | Recommended Action |
|------|--------|----------|------------|-------------------|
| 1 | Richmond | BC | 161K | Open 2-3 branches |
| 2 | Hamilton | ON | 203K | Open 3-4 branches |
| 3 | Toronto Central | ON | 180K | Open 2 branches |
| 4 | Surrey | BC | 207K | Open 2-3 branches |
| 5 | Brampton | ON | 119K | Open 1-2 branches |

### 2. Operational Efficiency

**Overloaded Branches** (>700 trans/staff):
- 10 branches identified operating at critical capacity
- Staff burnout risk in Vancouver Downtown, Quebec City, Montreal
- Recommendation: Hire 15-20 additional staff or redistribute from underutilized locations

**Underutilized Branches** (<400 trans/staff):
- 23 branches with excess capacity
- Opportunity to consolidate or repurpose for digital support

### 3. Digital Transformation Strategy

**Regional Digital Adoption**:
- High adopters (>70%): Toronto regions, Vancouver Downtown
- Low adopters (<50%): Quebec City, rural Alberta regions
- Recommendation: Target low-digital regions with mobile app campaigns to reduce in-branch traffic

### 4. Seasonal Planning

**Transaction Patterns**:
- Peak: November-December (+15% above baseline)
- Trough: January-February (-10% below baseline)
- Recommendation: Implement flexible staffing models for seasonal variations

---

## 💻 How to Run This Project

### Prerequisites
```bash
Python 3.11+
SQLite3
Tableau Desktop (for dashboard)
```

### Installation
```bash
# Clone repository
git clone https://github.com/alishbamateen/td-geospatial-analytics.git
cd td-geospatial-analytics

# Install dependencies
pip install pandas numpy folium matplotlib
```

### Execution Steps

**Step 1: Generate Data**
```bash
python generate_data.py
```

**Step 2: Set Up Database**
```bash
python sql/setup_database.py
python sql/fix_branches.py
```

**Step 3: Run Analysis**
```bash
# Geospatial analysis
python notebooks/02_geospatial_analysis.py

# Forecasting
python notebooks/03_forecasting_analysis.py

# Tableau data prep
python notebooks/04_tableau_data_prep.py
```

**Step 4: View Outputs**
- Open `data/processed/branch_demand_map.html` in browser for interactive map
- Open `dashboard/TD_Banking_Analytics.twb` in Tableau for full dashboard
- Review CSV outputs in `data/processed/` for detailed findings


