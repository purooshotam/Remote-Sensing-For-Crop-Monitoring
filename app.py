import streamlit as st
import ee
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from datetime import date

try:
    ee.Initialize()
except:
    ee.Authenticate()
    ee.Initialize()


st.set_page_config(
    page_title="AgroOrbit – Crop Monitoring",
    page_icon="🌿",
    layout="wide"
)

st.markdown(
    """
    # 🌿 **AgroOrbit**
    ### Smart Crop Monitoring using NDVI
    """
)
st.caption("Remote Sensing • Sentinel-2 • Google Earth Engine")
st.markdown("---")

st.sidebar.markdown("## ⚙️ Control Panel")

start_date = st.sidebar.date_input(
    "📅 Start Date",
    value=date(2023, 7, 1)
)

end_date = st.sidebar.date_input(
    "📅 End Date",
    value=date(2024, 6, 30)
)

if start_date >= end_date:
    st.sidebar.error("End date must be after start date")
    st.stop()

with st.expander("📘 About AgroOrbit"):
    st.write("""
    **AgroOrbit** is a web-based crop monitoring platform that allows users to
    select an area on the map and analyze crop health using NDVI.
    Sentinel-2 harmonized satellite imagery is processed using Google Earth Engine.
    """)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🗺️ Select Area for NDVI Calculation")

    m = folium.Map(
        location=[10.8, 78.5],
        zoom_start=7,
        tiles="OpenStreetMap"
    )

    Draw(
        draw_options={
            "polygon": True,
            "rectangle": True,
            "circle": False,
            "marker": False,
            "polyline": False,
            "circlemarker": False
        },
        edit_options={"edit": True}
    ).add_to(m)

    map_data = st_folium(m, height=500, width=900)

if (
    map_data is None
    or "all_drawings" not in map_data
    or map_data["all_drawings"] is None
    or len(map_data["all_drawings"]) == 0
):
    st.info("🖊️ Please draw a polygon or rectangle on the map to calculate NDVI.")
    st.stop()

geometry = map_data["all_drawings"][0]["geometry"]
roi = ee.Geometry(geometry)

collection = ee.ImageCollection("COPERNICUS/S2_HARMONIZED") \
    .filterBounds(roi) \
    .filterDate(str(start_date), str(end_date)) \
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))

image_count = collection.size().getInfo()

if image_count == 0:
    st.error("❌ No Sentinel-2 images available for the selected area and date.")
    st.stop()

image = collection.median()

ndvi = image.normalizedDifference(["B8", "B4"])

ndvi_stats = ndvi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=roi,
    scale=10,
    maxPixels=1e9
)

mean_ndvi = ndvi_stats.get("nd").getInfo() if ndvi_stats.get("nd") else None

with col2:
    st.markdown("### 📊 NDVI Analysis (Selected Area)")

    if mean_ndvi is not None:
        st.metric("Mean NDVI", f"{mean_ndvi:.3f}")

        if mean_ndvi > 0.6:
            st.success("🌿 Crop Health: Healthy Vegetation")
        elif mean_ndvi > 0.3:
            st.warning("🌾 Crop Health: Moderate Vegetation")
        else:
            st.error("🚨 Crop Health: Poor / Stressed Vegetation")
    else:
        st.warning("NDVI value could not be calculated.")

    st.markdown("""
    **NDVI Interpretation**
    - **> 0.6** → Healthy crops  
    - **0.3 – 0.6** → Moderate growth  
    - **< 0.3** → Poor vegetation
    """)

st.markdown("---")
st.caption("🌿 AgroOrbit | NDVI-Based Crop Monitoring via Web Application| CMRIT")
