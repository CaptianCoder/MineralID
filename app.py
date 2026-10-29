import streamlit as st
import pandas as pd
import json
import re

#    streamlit run /Users/josiahfriesen/Desktop/Youth-game/app.py


@st.cache_data
def load_data():
    with open('minerals.json', 'r') as f:
        data = json.load(f)
    
    # Helper function to extract numbers from messy strings (like Kyanite's hardness)
    def extract_number(val):
        if isinstance(val, (int, float)):
            return float(val)
        # Find all numbers in the string and take the first one
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
        if nums:
            return float(nums[0])
        return 0.0

    # Flatten and clean the data for Pandas
    for mineral in data:
        # Clean hardness
        mineral['hardness'] = extract_number(mineral.get('hardness', 0))
        
        # Clean refractive indices
        ri = mineral.get('refractive_indices', {})
        mineral['n_alpha'] = extract_number(ri.get('alpha', ri.get('omega', ri.get('n', 0))))
        mineral['n_beta'] = extract_number(ri.get('beta', ri.get('epsilon', ri.get('n', 0))))
        mineral['n_gamma'] = extract_number(ri.get('gamma', ri.get('n', 0)))
        
        # Calculate an average RI for easy filtering
        valid_ris = [v for v in [mineral['n_alpha'], mineral['n_beta'], mineral['n_gamma']] if v > 0]
        mineral['avg_ri'] = sum(valid_ris) / len(valid_ris) if valid_ris else 0.0

    return pd.DataFrame(data)

df = load_data()

# --- GUI Layout ---
st.set_page_config(page_title="Optical Mineralogy App", layout="wide")
st.title("Optical Mineralogy Search")
st.markdown("Search and filter common rock-forming minerals based on physical and optical properties.")

# --- Sidebar Filters ---
st.sidebar.header("Search & Filters")

# 1. Search by Name
search_query = st.sidebar.text_input("Search by Mineral Name", "").strip()

# 2. Filter by Optical Class
optical_classes = ["All"] + sorted(df['optical_class'].dropna().unique().tolist())
selected_class = st.sidebar.selectbox("Optical Class", optical_classes)

# 3. Filter by Refractive Index Range
min_ri = float(df['avg_ri'].min())
max_ri = float(df['avg_ri'].max())
ri_range = st.sidebar.slider(
    "Average Refractive Index Range", 
    min_value=min_ri, 
    max_value=max_ri, 
    value=(min_ri, max_ri),
    step=0.01
)

# 4. Filter by Hardness
min_hardness = float(df['hardness'].min())
max_hardness = float(df['hardness'].max())
hardness_range = st.sidebar.slider(
    "Mohs Hardness Range", 
    min_value=min_hardness, 
    max_value=max_hardness, 
    value=(min_hardness, max_hardness),
    step=0.5
)

# --- Apply Filters ---
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search_query, case=False, na=False)]

if selected_class != "All":
    filtered_df = filtered_df[filtered_df['optical_class'] == selected_class]

filtered_df = filtered_df[
    (filtered_df['avg_ri'] >= ri_range[0]) & 
    (filtered_df['avg_ri'] <= ri_range[1]) &
    (filtered_df['hardness'] >= hardness_range[0]) & 
    (filtered_df['hardness'] <= hardness_range[1])
]

# --- Main Content Area ---
st.subheader(f"Results: {len(filtered_df)} minerals found")

# Display results in a table
display_cols = ['name', 'optical_class', 'avg_ri', 'hardness', 'relief', 'color_hand_sample']
st.dataframe(filtered_df[display_cols], use_container_width=True)

# --- Detail View ---
st.markdown("---")
st.subheader("Mineral Details")

if not filtered_df.empty:
    selected_mineral_name = st.selectbox("Select a mineral to view full properties", filtered_df['name'].tolist())
    
    if selected_mineral_name:
        mineral_data = filtered_df[filtered_df['name'] == selected_mineral_name].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"### {mineral_data['name']}")
            st.markdown(f"**Formula:** `{mineral_data['formula']}`")
            st.markdown(f"**Crystal System:** {mineral_data['crystal_system']}")
            st.markdown(f"**Optical Class:** {mineral_data['optical_class']}")
            st.markdown(f"**Relief:** {mineral_data['relief']}")
            st.markdown(f"**Pleochroism:** {mineral_data['pleochroism']}")
            
        with col2:
            st.markdown("### Optical Data")
            st.markdown(f"**Birefringence (δ):** {mineral_data['birefringence']}")
            st.markdown(f"**2V Angle:** {mineral_data['2V_angle'] if mineral_data['2V_angle'] else 'N/A'}")
            st.markdown(f"**Extinction:** {mineral_data['extinction']}")
            st.markdown(f"**Twinning:** {mineral_data['twinning']}")
            st.markdown(f"**Note:** {mineral_data['note']}")
            
        with col3:
            st.markdown("### Physical Properties")
            st.markdown(f"**Hand Sample Color:** {mineral_data['color_hand_sample']}")
            st.markdown(f"**Hardness:** {mineral_data['hardness']}")
            st.markdown(f"**Cleavage:** {mineral_data['cleavage']}")
            st.markdown(f"**Occurrence:** {mineral_data['occurrence']}")
else:
    st.warning("No minerals match your current filter criteria. Try adjusting the sliders.")