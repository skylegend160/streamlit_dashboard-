import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

try:
    from streamlit_javascript import st_javascript
    from geopy.distance import geodesic
    JS_AVAILABLE = True
except ImportError:
    JS_AVAILABLE = False

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import os

try:
    from streamlit_javascript import st_javascript
    from geopy.distance import geodesic
    JS_AVAILABLE = True
except ImportError:
    JS_AVAILABLE = False

@st.cache_data
def load_data_from_gdrive(url):
    csv_file = st.experimental_get_query_params().get("csv_url", [url])[0]
    return pd.read_csv(csv_file)

# Load data from Google Drive link (publicly shared CSV)
gdrive_csv_url = "https://drive.google.com/uc?export=download&id=1_0xS8VgqX1Sjzl6MSdYkAeewtcKAncrk"
data = load_data_from_gdrive(gdrive_csv_url)

st.set_page_config(page_title="Environmental Data Dashboard", layout="wide")
st.title("🌍 Advanced Environmental Data Dashboard")

# Location auto detection & selectbox
all_locations = sorted(data['location'].unique())
all_years = sorted(data['YEAR'].unique())

user_lat, user_lon = None, None
auto_location = None
location_status = ""

if JS_AVAILABLE:
    user_location = st_javascript("navigator.geolocation.getCurrentPosition(pos => [pos.coords.latitude, pos.coords.longitude])")
    st.write("Debug: User location from JS", user_location)
    if user_location and isinstance(user_location, list) and len(user_location) == 2:
        user_lat, user_lon = user_location
        location_status = f"Detected latitude: {user_lat:.4f}, longitude: {user_lon:.4f}"
        def find_closest(lat, lon, df):
            df = df.dropna(subset=["latitude", "longitude"]).copy()
            df["distance_km"] = np.sqrt((df["latitude"] - lat) ** 2 + (df["longitude"] - lon) ** 2)
            closest_row = df.loc[df["distance_km"].idxmin()]
            return closest_row["location"]
        try:
            auto_location = find_closest(user_lat, user_lon, data)
            if auto_location not in all_locations:
                auto_location = None
        except Exception:
            auto_location = None
    else:
        location_status = "Location permission denied or unavailable."
else:
    location_status = "Geolocation disabled (missing dependencies)."

# Sidebar filters
with st.sidebar:
    st.header("Filters & Info")
    st.markdown(f"*Location detection status:* {location_status}")
    selected_location = st.selectbox("Select Location (Zone)", all_locations,
                                     index=all_locations.index(auto_location) if auto_location else 0)
    selected_year = st.selectbox("Select Year", all_years)

# Filter data accordingly
filtered_data = data[(data['location'] == selected_location) & (data['YEAR'] == selected_year)]

st.header(f"📍 Dashboard for Location: {selected_location} | Year: {selected_year}")

# Quick summary metrics
col1, col2, col3, col4 = st.columns([1.5,1.5,1.5,2])
with col1:
    st.metric("Sample Count", len(filtered_data))
with col2:
    avg_rain = filtered_data[[m+'r' for m in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']]].mean().mean()
    st.metric("Avg. Monthly Rainfall (mm)", f"{avg_rain:.2f}")
with col3:
    avg_temp = filtered_data[[m+'t' for m in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']]].mean().mean()
    st.metric("Avg. Monthly Temperature (°C)", f"{avg_temp:.2f}")
with col4:
    rockfall_rate = (filtered_data['rockfall'] == 'Yes').mean() * 100
    st.metric("Rockfall Rate (%)", f"{rockfall_rate:.2f}")

# Map
if "latitude" in filtered_data.columns and "longitude" in filtered_data.columns:
    st.subheader("🗺 Location Map")
    map_data = filtered_data[['latitude','longitude']].drop_duplicates()
    st.map(map_data)
else:
    st.info("Latitude/Longitude data not available for this zone.")

# Tabs for interactive charts and data
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Rainfall & Temperature", "Elevation & Terrain", "Rockfall Insights", "Data Table", "Data Download"])

months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
rainfall_cols = [m+'r' for m in months]
temp_cols = [m+'t' for m in months]

with tab1:
    st.subheader("Average Monthly Rainfall & Temperature")
    rainfall_avg = filtered_data[rainfall_cols].mean()
    temp_avg = filtered_data[temp_cols].mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=rainfall_avg, name='Rainfall (mm)', marker_color='blue'))
    fig.add_trace(go.Scatter(x=months, y=temp_avg, name='Temperature (°C)', mode='lines+markers', yaxis='y2', line_color='red'))
    fig.update_layout(
        yaxis=dict(title='Rainfall (mm)', side='left'),
        yaxis2=dict(title='Temperature (°C)', overlaying='y', side='right'),
        title="Monthly Rainfall & Temperature",
        legend=dict(x=0, y=1.1, orientation='h')
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Elevation, Slope, and Aspect Distributions")
    fig1 = px.histogram(filtered_data, x='elevation', nbins=30, title='Elevation Distribution', labels={'elevation':'Elevation (m)'})
    fig2 = px.histogram(filtered_data, x='slope_deg', nbins=30, title='Slope Distribution', labels={'slope_deg':'Slope (deg)'})
    fig3 = px.histogram(filtered_data, x='aspect_deg', nbins=30, title='Aspect Distribution', labels={'aspect_deg':'Aspect (deg)'})
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Rockfall and Probability Summary")
    desc = filtered_data[['rockfall', 'rockfall_probability']].describe()
    st.table(desc.style.format("{:.2f}"))
    # Rockfall 'Yes' percentage pie chart
    rockfall_counts = filtered_data['rockfall'].value_counts()
    fig_pie = px.pie(names=rockfall_counts.index, values=rockfall_counts.values, title="Rockfall Occurrence Distribution", labels={'label': 'Rockfall', 'value': 'Count'})
    st.plotly_chart(fig_pie, use_container_width=True)

with tab4:
    st.subheader("Raw Data Table")
    st.dataframe(filtered_data.reset_index(drop=True), height=400)

with tab5:
    st.subheader("Download Filtered Data")
    csv = filtered_data.to_csv(index=False).encode()
    st.download_button(label="Download CSV", data=csv, file_name=f"{selected_location}_{selected_year}_data.csv", mime='text/csv')
