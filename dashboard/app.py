"""
Jharkhand Google Maps Business Analysis — Interactive Dashboard
Run locally:  streamlit run app.py
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ----------------------------------------------------------------------
# PAGE CONFIG & STYLE
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Jharkhand Business Opportunity Dashboard",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded",
)

C_PRIMARY, C_SECOND, C_MINT = "#028090", "#00A896", "#02C39A"
C_ACCENT, C_DARK, C_RED = "#F0A202", "#0B2545", "#D64550"

st.markdown(
    f"""
    <style>
        .kpi-card {{
            background: white; border-radius: 12px; padding: 18px 20px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 5px solid {C_PRIMARY};
        }}
        .kpi-value {{ font-size: 28px; font-weight: 700; color: {C_DARK}; }}
        .kpi-label {{ font-size: 13px; color: #6b7280; }}
        h1, h2, h3 {{ color: {C_DARK}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "Jharkhand_Cleaned_Dataset.csv")


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    return df


df_raw = load_data()

# ----------------------------------------------------------------------
# SIDEBAR — FILTERS
# ----------------------------------------------------------------------
st.sidebar.image(
    "https://cdn-icons-png.flaticon.com/512/854/854878.png", width=60
)
st.sidebar.title("🔎 Filters")

cities = st.sidebar.multiselect(
    "City", sorted(df_raw["City"].unique()), default=[]
)
categories = st.sidebar.multiselect(
    "Category", sorted(df_raw["Category"].unique()), default=[]
)
website_filter = st.sidebar.radio(
    "Website Status", ["All", "No Website Only", "Has Website Only"], index=0
)
rating_range = st.sidebar.slider(
    "Rating Range",
    float(df_raw["Rating"].min()),
    float(df_raw["Rating"].max()),
    (float(df_raw["Rating"].min()), float(df_raw["Rating"].max())),
)
opportunity_filter = st.sidebar.multiselect(
    "Opportunity Flag",
    sorted(df_raw["Opportunity_Flag"].unique()),
    default=[],
)

df = df_raw.copy()
if cities:
    df = df[df["City"].isin(cities)]
if categories:
    df = df[df["Category"].isin(categories)]
if website_filter == "No Website Only":
    df = df[df["Has_Website"] == "No"]
elif website_filter == "Has Website Only":
    df = df[df["Has_Website"] == "Yes"]
df = df[(df["Rating"] >= rating_range[0]) & (df["Rating"] <= rating_range[1])]
if opportunity_filter:
    df = df[df["Opportunity_Flag"].isin(opportunity_filter)]

st.sidebar.markdown("---")
st.sidebar.caption(f"Showing **{len(df)}** of {len(df_raw)} businesses")
st.sidebar.download_button(
    "⬇ Download filtered data (CSV)",
    df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_businesses.csv",
    mime="text/csv",
)

# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.title("📍 Jharkhand Business Opportunity Dashboard")
st.caption(
    "Google Maps business analysis — identifying businesses without a website "
    "as digital-growth opportunities across Jharkhand."
)

# ----------------------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------------------
TOTAL = len(df)
NO_WEB = int((df["Has_Website"] == "No").sum())
HAS_WEB = TOTAL - NO_WEB
HIGH_OPP = int((df["Opportunity_Flag"] == "High Opportunity").sum())
AVG_RATING_NOWEB = df.loc[df["Has_Website"] == "No", "Rating"].mean()
AVG_RATING_WEB = df.loc[df["Has_Website"] == "Yes", "Rating"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
kpis = [
    (k1, "Total Businesses", f"{TOTAL:,}"),
    (k2, "Without Website", f"{NO_WEB} ({NO_WEB/TOTAL*100:.1f}%)" if TOTAL else "0"),
    (k3, "High Opportunity", f"{HIGH_OPP}"),
    (k4, "Avg Rating (No Website)", f"{AVG_RATING_NOWEB:.2f}" if NO_WEB else "N/A"),
    (k5, "Avg Rating (Has Website)", f"{AVG_RATING_WEB:.2f}" if HAS_WEB else "N/A"),
]
for col, label, value in kpis:
    col.markdown(
        f'<div class="kpi-card"><div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("")

# ----------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🏙️ City & Category", "🗺️ Map", "🏆 Top Opportunities", "📋 Raw Data"]
)

# ---- TAB 1: OVERVIEW ----
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Website Coverage")
        donut = px.pie(
            names=["Has Website", "No Website"],
            values=[HAS_WEB, NO_WEB],
            hole=0.55,
            color_discrete_sequence=[C_PRIMARY, C_RED],
        )
        donut.update_traces(textinfo="percent+label")
        donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(donut, use_container_width=True)

    with c2:
        st.subheader("Rating Distribution by Website Status")
        band_order = ["Average (<3.5)", "Good (3.5-3.9)", "Very Good (4.0-4.4)", "Excellent (4.5-5.0)"]
        band = (
            df.groupby(["Rating_Band", "Has_Website"]).size().reset_index(name="Count")
        )
        fig = px.bar(
            band, x="Rating_Band", y="Count", color="Has_Website",
            category_orders={"Rating_Band": band_order},
            color_discrete_map={"Yes": C_PRIMARY, "No": C_RED}, barmode="stack",
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Opening Hours vs Website Status")
    def hours_open(hstr):
        if hstr == "24 Hours":
            return 24
        try:
            start, end = hstr.split("-")
            t1 = pd.to_datetime(start, format="%I%p")
            t2 = pd.to_datetime(end, format="%I%p")
            diff = (t2 - t1).total_seconds() / 3600
            return diff if diff > 0 else diff + 24
        except Exception:
            return np.nan

    df["Hours_Open"] = df["Opening_Hours"].apply(hours_open)
    hrs = df.groupby("Has_Website")["Hours_Open"].mean().reset_index()
    fig_h = px.bar(hrs, x="Has_Website", y="Hours_Open", color="Has_Website",
                    color_discrete_map={"Yes": C_PRIMARY, "No": C_RED}, text_auto=".1f")
    fig_h.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
    st.plotly_chart(fig_h, use_container_width=True)

# ---- TAB 2: CITY & CATEGORY ----
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("No-Website Count by City")
        city_summary = (
            df.groupby("City")
            .agg(Total=("Business_Name", "count"), No_Website=("Has_Website", lambda x: (x == "No").sum()))
            .reset_index()
        )
        city_summary = city_summary[city_summary["No_Website"] > 0].sort_values("No_Website")
        fig = px.bar(city_summary, x="No_Website", y="City", orientation="h", color_discrete_sequence=[C_SECOND])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("% Without Website by Category")
        cat_summary = (
            df.groupby("Category")
            .agg(Total=("Business_Name", "count"), No_Website=("Has_Website", lambda x: (x == "No").sum()))
            .reset_index()
        )
        cat_summary["Pct"] = (cat_summary["No_Website"] / cat_summary["Total"] * 100).round(1)
        cat_summary = cat_summary[(cat_summary["Total"] >= 5) & (cat_summary["No_Website"] > 0)].sort_values("Pct")
        fig = px.bar(cat_summary, x="Pct", y="Category", orientation="h", color_discrete_sequence=[C_RED])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="% without website")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("City × Category Heatmap (No-Website Count)")
    pivot = pd.pivot_table(
        df[df["Has_Website"] == "No"], index="City", columns="Category",
        values="Business_Name", aggfunc="count", fill_value=0,
    )
    if not pivot.empty:
        fig_hm = px.imshow(pivot, color_continuous_scale="YlOrRd", aspect="auto", text_auto=True)
        fig_hm.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_hm, use_container_width=True)
    else:
        st.info("No no-website businesses in the current filter selection.")

# ---- TAB 3: MAP ----
with tab3:
    st.subheader("Geographic Distribution")
    map_mode = st.radio("Show on map", ["Opportunity businesses only", "All filtered businesses"], horizontal=True)
    plot_df = df[df["Has_Website"] == "No"] if map_mode == "Opportunity businesses only" else df

    if len(plot_df) == 0:
        st.info("No businesses to display for the current filters.")
    else:
        center = [plot_df["Latitude"].mean(), plot_df["Longitude"].mean()]
        m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
        cluster = MarkerCluster().add_to(m)
        color_map = {"High Opportunity": "red", "Opportunity": "orange", "Has Website": "blue"}
        for _, row in plot_df.iterrows():
            popup = (
                f"<b>{row['Business_Name']}</b><br>{row['Category']} — {row['Locality']}, {row['City']}"
                f"<br>Rating: {row['Rating']} | {row['Opportunity_Flag']}"
                f"<br>Parking: {row['Parking']} | Delivery: {row['Delivery']}"
            )
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]], radius=6,
                color=color_map.get(row["Opportunity_Flag"], "gray"), fill=True, fill_opacity=0.85,
                popup=folium.Popup(popup, max_width=280),
            ).add_to(cluster)
        st_folium(m, use_container_width=True, height=550)

# ---- TAB 4: TOP OPPORTUNITIES ----
with tab4:
    st.subheader("Digital Opportunity Score — Ranked Outreach List")
    no_web = df[df["Has_Website"] == "No"].copy()
    if len(no_web) == 0:
        st.info("No opportunity businesses in the current filter selection.")
    else:
        cat_demand = df_raw.groupby("Category")["Business_Name"].count()
        cat_demand_norm = ((cat_demand - cat_demand.min()) / (cat_demand.max() - cat_demand.min())).to_dict()

        no_web["Rating_Norm"] = (no_web["Rating"] - df_raw["Rating"].min()) / (df_raw["Rating"].max() - df_raw["Rating"].min())
        no_web["Amenity_Gap_Score"] = ((no_web["Parking"] != "Yes").astype(int) + (no_web["Delivery"] != "Yes").astype(int)) / 2
        no_web["Category_Demand_Score"] = no_web["Category"].map(cat_demand_norm).fillna(0)
        no_web["Digital_Opportunity_Score"] = (
            0.5 * no_web["Rating_Norm"] + 0.3 * no_web["Amenity_Gap_Score"] + 0.2 * no_web["Category_Demand_Score"]
        ) * 100
        no_web["Digital_Opportunity_Score"] = no_web["Digital_Opportunity_Score"].round(1)

        ranked = no_web.sort_values("Digital_Opportunity_Score", ascending=False)[
            ["Business_Name", "Category", "City", "Locality", "Rating", "Parking", "Delivery", "Phone", "Digital_Opportunity_Score"]
        ]
        top_n = st.slider("Show top N", 5, min(50, len(ranked)), min(10, len(ranked)))
        st.dataframe(ranked.head(top_n), use_container_width=True, hide_index=True)
        st.download_button(
            "⬇ Download ranked opportunity list (CSV)",
            ranked.to_csv(index=False).encode("utf-8"),
            file_name="digital_opportunity_score.csv",
            mime="text/csv",
        )

        fig = px.bar(
            ranked.head(top_n).sort_values("Digital_Opportunity_Score"),
            x="Digital_Opportunity_Score", y="Business_Name", orientation="h",
            color_discrete_sequence=[C_MINT],
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=max(300, top_n * 30))
        st.plotly_chart(fig, use_container_width=True)

# ---- TAB 5: RAW DATA ----
with tab5:
    st.subheader("Filtered Dataset")
    st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Built with Streamlit · Data: Google Maps business listings (Jharkhand) · Python analysis pipeline")
