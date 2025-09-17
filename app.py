import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Load CSV safely
@st.cache_data
def load_data(csv_file):
    try:
        df = pd.read_csv(csv_file)
    except:
        df = pd.read_csv(csv_file, encoding="latin1")
    df.columns = df.columns.str.strip()        # remove spaces
    df.columns = df.columns.str.lower()        # make lowercase
    return df

# File path (GitHub/raw URL or local for testing)
csv_path = "airockfalldata.csv"
data = load_data(csv_path)

# Show columns for debugging
st.write("✅ Columns detected:", list(data.columns))

# Get correct column names dynamically
location_col = [c for c in data.columns if "location" in c][0]
year_col = [c for c in data.columns if "year" in c][0]
rockfall_col = [c for c in data.columns if "rockfall" in c and "prob" not in c][0]
rockfall_prob_col = [c for c in data.columns if "rockfall_probability" in c][0]

# Sidebar filters
all_locations = sorted(data[location_col].unique())
all_years = sorted(data[year_col].unique())

with st.sidebar:
    st.header("Filters")
    selected_location = st.selectbox("Select Location", all_locations)
    selected_year = st.selectbox("Select Year", all_years)

# Filter data
filtered_data = data[(data[location_col] == selected_location) & 
                     (data[year_col] == selected_year)]

st.title("🌍 Environmental Data Dashboard")
st.header(f"📍 {selected_location} | Year: {selected_year}")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Sample Count", len(filtered_data))
with col2:
    rain_cols = [c for c in data.columns if c.endswith("r")]
    avg_rain = filtered_data[rain_cols].mean().mean()
    st.metric("Avg. Rainfall (mm)", f"{avg_rain:.2f}")
with col3:
    temp_cols = [c for c in data.columns if c.endswith("t")]
    avg_temp = filtered_data[temp_cols].mean().mean()
    st.metric("Avg. Temp (°C)", f"{avg_temp:.2f}")
with col4:
    rockfall_rate = (filtered_data[rockfall_col] == "Yes").mean() * 100
    st.metric("Rockfall Rate (%)", f"{rockfall_rate:.2f}")

# Map
if "latitude" in data.columns and "longitude" in data.columns:
    st.subheader("🗺 Location Map")
    st.map(filtered_data[['latitude','longitude']].dropna())
else:
    st.info("No latitude/longitude data available.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Rainfall & Temp", "Terrain", "Rockfall", "Data"])

months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
rainfall_cols = [m.lower()+'r' for m in months if m.lower()+'r' in data.columns]
temp_cols = [m.lower()+'t' for m in months if m.lower()+'t' in data.columns]

with tab1:
    st.subheader("Rainfall & Temperature Trends")
    rainfall_avg = filtered_data[rainfall_cols].mean()
    temp_avg = filtered_data[temp_cols].mean()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=rainfall_avg, name="Rainfall (mm)", marker_color="blue"))
    fig.add_trace(go.Scatter(x=months, y=temp_avg, name="Temp (°C)", yaxis="y2", line_color="red"))
    fig.update_layout(yaxis=dict(title="Rainfall"),
                      yaxis2=dict(title="Temperature", overlaying="y", side="right"))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Terrain Features")
    if "elevation" in data.columns:
        st.plotly_chart(px.histogram(filtered_data, x="elevation", nbins=30), use_container_width=True)
    if "slope_deg" in data.columns:
        st.plotly_chart(px.histogram(filtered_data, x="slope_deg", nbins=30), use_container_width=True)
    if "aspect_deg" in data.columns:
        st.plotly_chart(px.histogram(filtered_data, x="aspect_deg", nbins=30), use_container_width=True)

with tab3:
    st.subheader("Rockfall Insights")
    st.table(filtered_data[[rockfall_col, rockfall_prob_col]].describe())
    counts = filtered_data[rockfall_col].value_counts()
    st.plotly_chart(px.pie(names=counts.index, values=counts.values, title="Rockfall Distribution"), use_container_width=True)

with tab4:
    st.subheader("Raw Data")
    st.dataframe(filtered_data, height=400)
