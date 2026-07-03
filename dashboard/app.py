"""
Jharkhand Google Maps Business Analysis — Interactive Dashboard
Run locally:  streamlit run app.py
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from folium import Element
from streamlit_folium import st_folium

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Jharkhand Business Opportunity Dashboard",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# DESIGN TOKENS
# ----------------------------------------------------------------------
C_INK       = "#0B2545"
C_INK_SOFT  = "#4A5578"
C_TEAL      = "#028090"
C_TEAL_DARK = "#015663"
C_MINT      = "#02C39A"
C_CORAL     = "#D64550"
C_AMBER     = "#F0A202"
C_BG        = "#F4F6F9"
C_SURFACE   = "#FFFFFF"
C_BORDER    = "#E3E7EF"

FONT_DISPLAY = "Sora, 'Segoe UI', sans-serif"
FONT_BODY    = "Inter, 'Segoe UI', sans-serif"

# ----------------------------------------------------------------------
# GLOBAL CSS  (kept intentionally simple/robust — no nested custom divs
# for repeated elements, to avoid rendering glitches across Streamlit
# versions. Only the hero banner and KPI cards use raw HTML, each once.)
# ----------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{ font-family: {FONT_BODY}; }}

        [data-testid="stAppViewContainer"] > .main {{ background: {C_BG}; }}
        .block-container {{ padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1300px; }}

        /* Sidebar */
        [data-testid="stSidebar"] {{ background: {C_INK}; }}
        [data-testid="stSidebar"] * {{ color: #E9EDF5 !important; }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] {{
            background: #16305C; border-radius: 8px; border: 1px solid #24406F;
        }}
        [data-testid="stSidebar"] hr {{ border-color: #24406F; }}

        /* Hero */
        .hero {{
            background: linear-gradient(120deg, {C_INK} 0%, {C_TEAL_DARK} 100%);
            border-radius: 18px; padding: 34px 40px; margin-bottom: 22px;
            box-shadow: 0 10px 30px rgba(11,37,69,0.25);
        }}
        .hero-eyebrow {{
            display: inline-block; font-size: 12.5px; font-weight: 700;
            letter-spacing: 0.12em; text-transform: uppercase; color: {C_MINT};
            background: rgba(2,195,154,0.12); border: 1px solid rgba(2,195,154,0.35);
            padding: 5px 12px; border-radius: 999px; margin-bottom: 14px;
        }}
        .hero-title {{
            font-family: {FONT_DISPLAY}; font-size: 34px; font-weight: 800;
            color: #FFFFFF; margin: 0 0 8px 0; letter-spacing: -0.01em;
        }}
        .hero-sub {{ font-size: 15px; color: #C7D2E5; max-width: 720px; line-height: 1.55; margin: 0; }}

        /* KPI cards */
        .kpi-card {{
            background: {C_SURFACE}; border-radius: 14px; padding: 20px 20px 18px 20px;
            border: 1px solid {C_BORDER}; box-shadow: 0 2px 10px rgba(11,37,69,0.05);
            position: relative; overflow: hidden; height: 100%;
        }}
        .kpi-card::before {{
            content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px;
            background: var(--accent, {C_TEAL});
        }}
        .kpi-icon {{ font-size: 20px; margin-bottom: 10px; display: block; }}
        .kpi-value {{ font-family: {FONT_DISPLAY}; font-size: 30px; font-weight: 800; color: {C_INK}; line-height: 1.1; }}
        .kpi-label {{ font-size: 13px; font-weight: 500; color: {C_INK_SOFT}; margin-top: 6px; }}

        /* Section headings (plain markdown ### rendered as h3 — styled globally) */
        .block-container h3 {{
            font-family: {FONT_DISPLAY}; font-weight: 700; color: {C_INK};
            margin-top: 28px; margin-bottom: 10px; font-size: 19px;
        }}

        /* Pill tab nav */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 6px; background: {C_SURFACE}; padding: 6px; border-radius: 14px; border: 1px solid {C_BORDER};
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 46px; border-radius: 10px; font-family: {FONT_DISPLAY}; font-weight: 700;
            font-size: 14px; color: {C_INK_SOFT}; padding: 0 18px;
        }}
        .stTabs [aria-selected="true"] {{ background: {C_INK} !important; color: #FFFFFF !important; }}
        .stTabs [data-baseweb="tab-highlight"] {{ background: transparent; }}
        .stTabs [data-baseweb="tab-border"] {{ display: none; }}

        /* Chart / content panels */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {C_SURFACE}; border-radius: 14px; border: 1px solid {C_BORDER} !important;
        }}

        /* Misc */
        .stDataFrame {{ border-radius: 12px; overflow: hidden; border: 1px solid {C_BORDER}; }}
        .footer-note {{
            text-align: center; color: {C_INK_SOFT}; font-size: 12.5px;
            margin-top: 30px; padding-top: 16px; border-top: 1px solid {C_BORDER};
        }}
        .legend-chip {{
            display: inline-flex; align-items: center; gap: 6px; font-size: 13px;
            color: {C_INK_SOFT}; margin-right: 18px;
        }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def style_fig(fig, height=420, legend=True):
    fig.update_layout(
        font=dict(family=FONT_BODY, size=13, color=C_INK_SOFT),
        title_font=dict(family=FONT_DISPLAY, size=16, color=C_INK),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=10, r=10),
        height=height,
        showlegend=legend,
        legend=dict(font=dict(size=12)),
    )
    fig.update_xaxes(gridcolor=C_BORDER, zeroline=False)
    fig.update_yaxes(gridcolor=C_BORDER, zeroline=False)
    return fig


# ----------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "Jharkhand_Cleaned_Dataset.csv")


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


df_raw = load_data()

# ----------------------------------------------------------------------
# SIDEBAR — FILTERS
# ----------------------------------------------------------------------
st.sidebar.markdown(
    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>"
    "<span style='font-size:26px;'>📍</span>"
    "<span style='font-family:Sora,sans-serif;font-weight:800;font-size:18px;'>Jharkhand Biz</span>"
    "</div>",
    unsafe_allow_html=True,
)
st.sidebar.caption("Google Maps opportunity explorer")
st.sidebar.divider()

with st.sidebar.container(border=True):
    st.markdown("**🏙️ Location**")
    cities = st.multiselect("City", sorted(df_raw["City"].unique()), default=[])
    categories = st.multiselect("Category", sorted(df_raw["Category"].unique()), default=[])

with st.sidebar.container(border=True):
    st.markdown("**🌐 Digital Status**")
    website_filter = st.radio("Website Status", ["All", "No Website Only", "Has Website Only"], index=0)
    opportunity_filter = st.multiselect(
        "Opportunity Flag", sorted(df_raw["Opportunity_Flag"].unique()), default=[]
    )

with st.sidebar.container(border=True):
    st.markdown("**⭐ Rating**")
    rating_range = st.slider(
        "Rating Range",
        float(df_raw["Rating"].min()), float(df_raw["Rating"].max()),
        (float(df_raw["Rating"].min()), float(df_raw["Rating"].max())),
        label_visibility="collapsed",
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

st.sidebar.divider()
st.sidebar.caption(f"Showing **{len(df)}** of {len(df_raw)} businesses")
st.sidebar.download_button(
    "⬇ Download filtered data (CSV)",
    df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_businesses.csv",
    mime="text/csv",
    use_container_width=True,
)

# ----------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-eyebrow">📍 Jharkhand · Google Maps Data</div>
        <div class="hero-title">Business Opportunity Dashboard</div>
        <p class="hero-sub">Identifying businesses without a website across Jharkhand and ranking
        them by digital-growth opportunity — rating, amenities, and category demand combined
        into a single, actionable outreach list.</p>
    </div>
    """,
    unsafe_allow_html=True,
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

kpis = [
    ("🏬", "Total Businesses", f"{TOTAL:,}", C_TEAL),
    ("🌐", "Without Website", f"{NO_WEB} ({NO_WEB/TOTAL*100:.1f}%)" if TOTAL else "0", C_CORAL),
    ("🎯", "High Opportunity", f"{HIGH_OPP}", C_AMBER),
    ("⭐", "Avg Rating (No Website)", f"{AVG_RATING_NOWEB:.2f}" if NO_WEB else "N/A", C_CORAL),
    ("✅", "Avg Rating (Has Website)", f"{AVG_RATING_WEB:.2f}" if HAS_WEB else "N/A", C_MINT),
]
cols = st.columns(5)
for col, (icon, label, value, accent) in zip(cols, kpis):
    col.markdown(
        f'<div class="kpi-card" style="--accent:{accent}">'
        f'<span class="kpi-icon">{icon}</span>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊  Overview", "🏙️  City & Category", "🗺️  Map", "🏆  Top Opportunities", "📋  Raw Data"]
)

# ---- TAB 1: OVERVIEW ----
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("### Website Coverage")
            donut = px.pie(
                names=["Has Website", "No Website"], values=[HAS_WEB, NO_WEB], hole=0.6,
                color_discrete_sequence=[C_TEAL, C_CORAL],
            )
            donut.update_traces(textinfo="percent+label", textfont_size=13)
            style_fig(donut, height=400, legend=False)
            st.plotly_chart(donut, use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("### Rating Distribution by Website Status")
            band_order = ["Average (<3.5)", "Good (3.5-3.9)", "Very Good (4.0-4.4)", "Excellent (4.5-5.0)"]
            band = df.groupby(["Rating_Band", "Has_Website"]).size().reset_index(name="Count")
            fig = px.bar(
                band, x="Rating_Band", y="Count", color="Has_Website",
                category_orders={"Rating_Band": band_order},
                color_discrete_map={"Yes": C_TEAL, "No": C_CORAL}, barmode="stack",
            )
            style_fig(fig, height=400)
            st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("### Opening Hours vs Website Status")

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
                        color_discrete_map={"Yes": C_TEAL, "No": C_CORAL}, text_auto=".1f")
        style_fig(fig_h, height=360, legend=False)
        st.plotly_chart(fig_h, use_container_width=True)

# ---- TAB 2: CITY & CATEGORY ----
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("### No-Website Count by City")
            city_summary = (
                df.groupby("City")
                .agg(Total=("Business_Name", "count"), No_Website=("Has_Website", lambda x: (x == "No").sum()))
                .reset_index()
            )
            city_summary = city_summary[city_summary["No_Website"] > 0].sort_values("No_Website")
            fig = px.bar(city_summary, x="No_Website", y="City", orientation="h", color_discrete_sequence=[C_TEAL])
            style_fig(fig, height=400, legend=False)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("### % Without Website by Category")
            cat_summary = (
                df.groupby("Category")
                .agg(Total=("Business_Name", "count"), No_Website=("Has_Website", lambda x: (x == "No").sum()))
                .reset_index()
            )
            cat_summary["Pct"] = (cat_summary["No_Website"] / cat_summary["Total"] * 100).round(1)
            cat_summary = cat_summary[(cat_summary["Total"] >= 5) & (cat_summary["No_Website"] > 0)].sort_values("Pct")
            fig = px.bar(cat_summary, x="Pct", y="Category", orientation="h", color_discrete_sequence=[C_CORAL])
            style_fig(fig, height=400, legend=False)
            fig.update_layout(xaxis_title="% without website")
            st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("### City × Category Heatmap (No-Website Count)")
        pivot = pd.pivot_table(
            df[df["Has_Website"] == "No"], index="City", columns="Category",
            values="Business_Name", aggfunc="count", fill_value=0,
        )
        if not pivot.empty:
            fig_hm = px.imshow(pivot, color_continuous_scale=[[0, "#F4F6F9"], [1, C_CORAL]], aspect="auto", text_auto=True)
            style_fig(fig_hm, height=440)
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("No no-website businesses in the current filter selection.")

# ---- TAB 3: MAP ----
with tab3:
    with st.container(border=True):
        st.markdown("### Geographic Distribution")
        map_mode = st.radio("Show on map", ["Opportunity businesses only", "All filtered businesses"], horizontal=True)

        st.markdown(
            '<span class="legend-chip"><span class="legend-dot" style="background:#D64550;"></span>High Opportunity</span>'
            '<span class="legend-chip"><span class="legend-dot" style="background:#F0A202;"></span>Opportunity</span>'
            '<span class="legend-chip"><span class="legend-dot" style="background:#028090;"></span>Has Website</span>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        plot_df = df[df["Has_Website"] == "No"] if map_mode == "Opportunity businesses only" else df

        if len(plot_df) == 0:
            st.info("No businesses to display for the current filters.")
        else:
            center = [plot_df["Latitude"].mean(), plot_df["Longitude"].mean()]
            m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
            cluster = MarkerCluster().add_to(m)
            color_map = {"High Opportunity": "#D64550", "Opportunity": "#F0A202", "Has Website": "#028090"}
            for _, row in plot_df.iterrows():
                popup_html = f"""
                <div style="font-family:sans-serif; min-width:190px;">
                    <div style="font-size:13px; font-weight:700; color:#0B2545;">{row['Business_Name']}</div>
                    <div style="font-size:11.5px; color:#4A5578; margin:3px 0;">{row['Category']} — {row['Locality']}, {row['City']}</div>
                    <div style="font-size:11.5px;">⭐ {row['Rating']} | {row['Opportunity_Flag']}</div>
                    <div style="font-size:11.5px; color:#4A5578;">🅿️ {row['Parking']} &nbsp; 🚚 {row['Delivery']}</div>
                </div>
                """
                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]], radius=7, weight=2,
                    color=color_map.get(row["Opportunity_Flag"], "gray"),
                    fill=True, fill_color=color_map.get(row["Opportunity_Flag"], "gray"), fill_opacity=0.85,
                    popup=folium.Popup(popup_html, max_width=260),
                ).add_to(cluster)
            st_folium(m, use_container_width=True, height=580)

# ---- TAB 4: TOP OPPORTUNITIES ----
with tab4:
    with st.container(border=True):
        st.markdown("### Digital Opportunity Score — Ranked Outreach List")
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

            st.markdown(f"### Top {top_n} by Score")
            fig = px.bar(
                ranked.head(top_n).sort_values("Digital_Opportunity_Score"),
                x="Digital_Opportunity_Score", y="Business_Name", orientation="h",
                color_discrete_sequence=[C_MINT],
            )
            style_fig(fig, height=max(320, top_n * 34), legend=False)
            st.plotly_chart(fig, use_container_width=True)

# ---- TAB 5: RAW DATA ----
with tab5:
    with st.container(border=True):
        st.markdown("### Filtered Dataset")
        st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown(
    '<div class="footer-note">Built with Streamlit · Data: Google Maps business listings (Jharkhand) · Python analysis pipeline</div>',
    unsafe_allow_html=True,
)