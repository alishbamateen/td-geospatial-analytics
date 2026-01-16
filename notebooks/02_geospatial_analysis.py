"""
TD Geospatial Analytics - Phase 3: Geospatial Analysis
Creates interactive maps and spatial insights
Save this as: notebooks/02_geospatial_analysis.ipynb (or run as .py)
"""

import pandas as pd
import sqlite3
import folium
from folium import plugins
import numpy as np

# ============================================
# 1. LOAD DATA FROM DATABASE
# ============================================

print("📊 Loading data from database...\n")

conn = sqlite3.connect('data/td_banking.db')

# Load branches
df_branches = pd.read_sql_query("""
    SELECT 
        b.*,
        CASE 
            WHEN b.transactions_per_staff > 900 THEN 'Critical'
            WHEN b.transactions_per_staff > 700 THEN 'High'
            WHEN b.transactions_per_staff > 500 THEN 'Moderate'
            ELSE 'Normal'
        END AS load_status
    FROM branches b
""", conn)

# Load regional summary
df_regions = pd.read_sql_query("""
    SELECT * FROM vw_regional_summary
""", conn)

# Load underserved regions
df_underserved = pd.read_sql_query("""
    SELECT * FROM vw_regional_summary
    WHERE coverage_status = 'Underserved'
    ORDER BY demand_score DESC
""", conn)

conn.close()

print(f"✓ Loaded {len(df_branches)} branches")
print(f"✓ Loaded {len(df_regions)} regions")
print(f"✓ Identified {len(df_underserved)} underserved regions\n")

# ============================================
# 2. CREATE BASE MAP (CENTERED ON CANADA)
# ============================================

print("🗺️  Creating interactive map...\n")

# Center map on Canada
center_lat = 50.0
center_lon = -95.0

# Create base map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=4,
    tiles='OpenStreetMap'
)

# ============================================
# 3. ADD BRANCH MARKERS (COLOR-CODED BY LOAD)
# ============================================

print("📍 Adding branch locations...")

# Define colors for load status
load_colors = {
    'Critical': 'red',
    'High': 'orange',
    'Moderate': 'lightblue',
    'Normal': 'green'
}

# Create feature groups for layer control
branch_group = folium.FeatureGroup(name='Branches (by Load Status)')

for idx, branch in df_branches.iterrows():
    color = load_colors.get(branch['load_status'], 'gray')
    
    # Create popup content
    popup_html = f"""
    <div style="font-family: Arial; width: 200px;">
        <h4>{branch['branch_id']}</h4>
        <b>Region:</b> {branch['region_name']}<br>
        <b>Province:</b> {branch['province']}<br>
        <b>Type:</b> {branch['branch_type']}<br>
        <b>Staff:</b> {branch['staff_count']}<br>
        <b>Monthly Trans:</b> {branch['monthly_transactions']:,}<br>
        <b>Trans/Staff:</b> {branch['transactions_per_staff']:.0f}<br>
        <b>Load Status:</b> <span style="color: {color}; font-weight: bold;">{branch['load_status']}</span>
    </div>
    """
    
    folium.CircleMarker(
        location=[branch['latitude'], branch['longitude']],
        radius=6,
        popup=folium.Popup(popup_html, max_width=250),
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.7,
        weight=2
    ).add_to(branch_group)

branch_group.add_to(m)

print(f"   ✓ Added {len(df_branches)} branch markers")

# ============================================
# 4. ADD REGIONAL CENTERS WITH DEMAND INFO
# ============================================

print("\n🎯 Adding regional demand markers...")

# Calculate average lat/lon for each region based on branches
region_centers = df_branches.groupby('region_id').agg({
    'latitude': 'mean',
    'longitude': 'mean',
    'region_name': 'first',
    'province': 'first'
}).reset_index()

# Merge with regional data
region_centers = region_centers.merge(df_regions, on='region_id', how='left')

# Create region group
region_group = folium.FeatureGroup(name='Regional Demand Centers')

for idx, region in region_centers.iterrows():
    # Size based on demand score
    radius = min(region['demand_score'] * 5, 20)
    
    # Color based on coverage status
    status_colors = {
        'Underserved': '#ff6b6b',
        'Balanced': '#51cf66',
        'Oversupplied': '#339af0',
        'No Coverage': '#ff0000'
    }
    color = status_colors.get(region['coverage_status'], 'gray')
    
    popup_html = f"""
    <div style="font-family: Arial; width: 220px;">
        <h4>{region['region_name_x']}</h4>
        <b>Province:</b> {region['province_x']}<br>
        <b>Population:</b> {region['population']:,}<br>
        <b>Demand Score:</b> {region['demand_score']:.2f}<br>
        <b>Branches:</b> {region['branch_count']}<br>
        <b>Regional Demand:</b> {region['regional_demand']:,}<br>
        <b>Branch Capacity:</b> {region['total_branch_capacity']:,}<br>
        <b>Capacity Gap:</b> {region['capacity_gap']:,}<br>
        <b>Status:</b> <span style="color: {color}; font-weight: bold;">{region['coverage_status']}</span>
    </div>
    """
    
    folium.Circle(
        location=[region['latitude'], region['longitude']],
        radius=radius * 1000,  # Convert to meters
        popup=folium.Popup(popup_html, max_width=250),
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.3,
        weight=2
    ).add_to(region_group)

region_group.add_to(m)

print(f"   ✓ Added {len(region_centers)} regional centers")

# ============================================
# 5. HIGHLIGHT UNDERSERVED REGIONS
# ============================================

print("\n⚠️  Highlighting underserved regions...")

underserved_group = folium.FeatureGroup(name='Underserved Regions (Priority)')

# Get centers for underserved regions
underserved_centers = region_centers[
    region_centers['coverage_status'] == 'Underserved'
].copy()

for idx, region in underserved_centers.iterrows():
    # Larger, pulsing markers for underserved areas
    folium.Marker(
        location=[region['latitude'], region['longitude']],
        popup=f"""
        <div style="font-family: Arial; width: 200px;">
            <h4 style="color: red;">⚠️ UNDERSERVED</h4>
            <b>{region['region_name_x']}</b><br>
            <b>Demand Score:</b> {region['demand_score']:.2f}<br>
            <b>Capacity Gap:</b> {region['capacity_gap']:,}<br>
            <b>Current Branches:</b> {region['branch_count']}<br>
            <hr>
            <b style="color: green;">Expansion Opportunity</b>
        </div>
        """,
        icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
    ).add_to(underserved_group)

underserved_group.add_to(m)

print(f"   ✓ Highlighted {len(underserved_centers)} underserved regions")

# ============================================
# 6. CREATE HEATMAP OF TRANSACTION DEMAND
# ============================================

print("\n🔥 Creating demand heatmap...")

# Prepare data for heatmap (weight by demand)
heat_data = []
for idx, region in region_centers.iterrows():
    heat_data.append([
        region['latitude'],
        region['longitude'],
        region['demand_score']
    ])

# Add heatmap layer
heatmap_group = folium.FeatureGroup(name='Demand Heatmap', show=False)
plugins.HeatMap(
    heat_data,
    min_opacity=0.3,
    radius=50,
    blur=40,
    gradient={
        0.0: 'blue',
        0.5: 'yellow',
        1.0: 'red'
    }
).add_to(heatmap_group)

heatmap_group.add_to(m)

print("   ✓ Heatmap layer created")

# ============================================
# 7. ADD LEGEND
# ============================================

legend_html = """
<div style="position: fixed; 
            bottom: 50px; right: 50px; width: 220px; height: auto; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:14px; padding: 10px; border-radius: 5px;">
    <h4 style="margin-top: 0;">Legend</h4>
    <p><b>Branch Load Status:</b></p>
    <p><span style="color: red;">●</span> Critical (>900 trans/staff)</p>
    <p><span style="color: orange;">●</span> High (700-900)</p>
    <p><span style="color: lightblue;">●</span> Moderate (500-700)</p>
    <p><span style="color: green;">●</span> Normal (<500)</p>
    <hr>
    <p><b>Regional Status:</b></p>
    <p><span style="color: #ff6b6b;">●</span> Underserved</p>
    <p><span style="color: #51cf66;">●</span> Balanced</p>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

# ============================================
# 8. ADD LAYER CONTROL
# ============================================

folium.LayerControl().add_to(m)

# ============================================
# 9. SAVE MAP
# ============================================

output_path = 'data/processed/branch_demand_map.html'
m.save(output_path)

print(f"\n✅ Interactive map saved to: {output_path}")
print("   Open this file in your browser to explore!\n")

# ============================================
# 10. SPATIAL ANALYSIS - DISTANCE CALCULATIONS
# ============================================

print("="*70)
print("📏 SPATIAL ANALYSIS - KEY METRICS")
print("="*70 + "\n")

# Calculate average distance between branches (simplified)
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

# For each region, find average distance to branches
print("🎯 Regional Branch Accessibility:\n")

for idx, region in underserved_centers.head(5).iterrows():
    region_branches = df_branches[df_branches['region_id'] == region['region_id']]
    
    if len(region_branches) > 0:
        # Calculate distances from region center to each branch
        distances = []
        for _, branch in region_branches.iterrows():
            dist = haversine_distance(
                region['latitude'], region['longitude'],
                branch['latitude'], branch['longitude']
            )
            distances.append(dist)
        
        avg_dist = np.mean(distances)
        print(f"{region['region_name_x']:20} | Branches: {len(region_branches)} | Avg Distance: {avg_dist:.2f} km")

# ============================================
# 11. EXPORT INSIGHTS TO CSV
# ============================================

print("\n💾 Exporting analysis results...\n")

# Export underserved regions
df_underserved.to_csv('data/processed/underserved_regions.csv', index=False)
print("   ✓ underserved_regions.csv")

# Export branch performance
df_branches[df_branches['load_status'].isin(['Critical', 'High'])].to_csv(
    'data/processed/overloaded_branches.csv', index=False
)
print("   ✓ overloaded_branches.csv")

# Create expansion recommendations
expansion_recommendations = underserved_centers[['region_name_x', 'province_x', 'demand_score', 
                                                 'capacity_gap', 'branch_count']].copy()
expansion_recommendations.columns = ['Region', 'Province', 'Demand_Score', 'Capacity_Gap', 'Current_Branches']
expansion_recommendations['Recommended_Action'] = expansion_recommendations.apply(
    lambda x: f"Add 2-3 branches" if x['Capacity_Gap'] > 150000 
    else f"Add 1-2 branches" if x['Capacity_Gap'] > 100000 
    else "Add 1 branch or mobile service", axis=1
)

expansion_recommendations.to_csv('data/processed/expansion_recommendations.csv', index=False)
print("   ✓ expansion_recommendations.csv")

print("\n" + "="*70)
print("✅ GEOSPATIAL ANALYSIS COMPLETE!")
print("="*70)
print("\nNext Steps:")
print("1. Open branch_demand_map.html in your browser")
print("2. Review CSV outputs in data/processed/")
print("3. Move to Phase 4: Forecasting\n")