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
        font=dict(
            family=FONT_BODY,
            size=13,
            color="white"          # Force all text to white
        ),

        title_font=dict(
            family=FONT_DISPLAY,
            size=16,
            color="white"
        ),

        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",

        margin=dict(t=30, b=30, l=10, r=10),

        height=height,

        showlegend=legend,

        legend=dict(
            font=dict(
                size=12,
                color="white"
            )
        ),

        hoverlabel=dict(
            font=dict(color="white")
        )
    )

    fig.update_xaxes(
        gridcolor=C_BORDER,
        zeroline=False,
        title_font=dict(color="white"),
        tickfont=dict(color="white")
    )

    fig.update_yaxes(
        gridcolor=C_BORDER,
        zeroline=False,
        title_font=dict(color="white"),
        tickfont=dict(color="white")
    )

    fig.update_annotations(
        font=dict(color="white")
    )

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
tab1, tab2, tab3, tab4, tab5,tab6,tab7 = st.tabs(
    ["📊  Overview", "🏙️  City & Category", "🗺️  Map", "🏆  Top Opportunities", "📋  Raw Data"," Ratings","Key Insights"]
)

# ---- TAB 1: OVERVIEW ----
with tab1:

    # ==========================================================
    # KPI CARDS
    # ==========================================================

    total_business = len(df)
    total_city = df["City"].nunique()
    total_category = df["Category"].nunique()
    avg_rating = df["Rating"].mean()

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric("Businesses", total_business)

    with k2:
        st.metric("Cities", total_city)

    with k3:
        st.metric("Categories", total_category)

    with k4:
        st.metric("Avg Rating", f"{avg_rating:.2f}")

    st.markdown("---")

    # ==========================================================
    # ROW 1
    # ==========================================================

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):

            st.markdown("### Website Coverage")

            donut = px.pie(
                names=["Has Website", "No Website"],
                values=[HAS_WEB, NO_WEB],
                hole=0.6,
                color_discrete_sequence=[C_TEAL, C_CORAL],
            )

            donut.update_traces(
                textinfo="percent+label",
                textfont_size=13
            )

            style_fig(donut, height=400, legend=False)

            st.plotly_chart(
                donut,
                use_container_width=True
            )

    with c2:
        with st.container(border=True):

            st.markdown("### Rating Distribution by Website Status")

            band_order = [
                "Average (<3.5)",
                "Good (3.5-3.9)",
                "Very Good (4.0-4.4)",
                "Excellent (4.5-5.0)"
            ]

            band = (
                df.groupby(
                    ["Rating_Band", "Has_Website"]
                )
                .size()
                .reset_index(name="Count")
            )

            fig = px.bar(
                band,
                x="Rating_Band",
                y="Count",
                color="Has_Website",
                category_orders={"Rating_Band": band_order},
                color_discrete_map={
                    "Yes": C_TEAL,
                    "No": C_CORAL
                },
                barmode="stack",
            )

            style_fig(fig, height=400)

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    # ==========================================================
    # ROW 2
    # ==========================================================

    c3, c4 = st.columns(2)

    with c3:
        with st.container(border=True):

            st.markdown("### Top 10 Cities")

            city = (
                df["City"]
                .value_counts()
                .reset_index()
            )

            city.columns = ["City", "Businesses"]

            fig = px.bar(
                city.head(10),
                x="City",
                y="Businesses",
                color="Businesses"
            )

            style_fig(fig, height=400)

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    with c4:
        with st.container(border=True):

            st.markdown("### Top Categories")

            cat = (
                df["Category"]
                .value_counts()
                .reset_index()
            )

            cat.columns = [
                "Category",
                "Businesses"
            ]

            fig = px.bar(
                cat.head(10),
                x="Category",
                y="Businesses",
                color="Businesses"
            )

            style_fig(fig, height=400)

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    # ==========================================================
    # ROW 3
    # ==========================================================

    c5, c6 = st.columns(2)

    with c5:
        with st.container(border=True):

            st.markdown("### Opening Hours vs Website Status")

            def hours_open(hstr):

                if hstr == "24 Hours":
                    return 24

                try:

                    start, end = hstr.split("-")

                    t1 = pd.to_datetime(
                        start,
                        format="%I%p"
                    )

                    t2 = pd.to_datetime(
                        end,
                        format="%I%p"
                    )

                    diff = (
                        t2 - t1
                    ).total_seconds() / 3600

                    return diff if diff > 0 else diff + 24

                except:

                    return np.nan

            df["Hours_Open"] = df["Opening_Hours"].apply(hours_open)

            hrs = (
                df.groupby("Has_Website")["Hours_Open"]
                .mean()
                .reset_index()
            )

            fig_h = px.bar(
                hrs,
                x="Has_Website",
                y="Hours_Open",
                color="Has_Website",
                color_discrete_map={
                    "Yes": C_TEAL,
                    "No": C_CORAL
                },
                text_auto=".1f"
            )

            style_fig(fig_h, height=360, legend=False)

            st.plotly_chart(
                fig_h,
                use_container_width=True
            )

    with c6:
        with st.container(border=True):

            st.markdown("### Ratings by Website Status")

            fig = px.box(
                df,
                x="Has_Website",
                y="Rating",
                color="Has_Website",
                color_discrete_map={
                    "Yes": C_TEAL,
                    "No": C_CORAL
                }
            )

            style_fig(fig, height=360)

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    # ==========================================================
    # OVERVIEW INSIGHTS
    # ==========================================================

    with st.container(border=True):

        st.markdown("## 📌 Dashboard Summary")

        st.markdown(f"""
### Overall Insights

- **Total Businesses:** **{len(df)}**

- **Cities Covered:** **{df['City'].nunique()}**

- **Categories Covered:** **{df['Category'].nunique()}**

- **Businesses with Website:** **{HAS_WEB}**

- **Businesses without Website:** **{NO_WEB}**

- **Website Coverage:** **{(HAS_WEB/len(df))*100:.1f}%**

- **Average Rating:** **{df['Rating'].mean():.2f}/5**

- **Top City:** **{df['City'].value_counts().idxmax()}**

- **Top Category:** **{df['Category'].value_counts().idxmax()}**

### Recommendations

- Prioritize businesses without websites for digital onboarding.

- Focus outreach in cities with the highest concentration of businesses.

- Encourage highly rated businesses to establish an online presence.

- Continue improving customer experience to increase business ratings.
""")
# ---- TAB 2: CITY & CATEGORY ----
with tab2:

    # ============================
    # KPI CARDS
    # ============================

    total_cities = df["City"].nunique()
    total_categories = df["Category"].nunique()

    top_city = df["City"].value_counts().idxmax()
    top_category = df["Category"].value_counts().idxmax()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Cities", total_cities)
    c2.metric("Categories", total_categories)
    c3.metric("Largest City", top_city)
    c4.metric("Largest Category", top_category)

    st.markdown("---")

    # ============================
    # ROW 1
    # ============================

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):

            st.markdown("### Businesses by City")

            city_count = (
                df.groupby("City")
                .size()
                .reset_index(name="Businesses")
                .sort_values("Businesses", ascending=False)
            )

            fig = px.bar(
                city_count,
                x="City",
                y="Businesses",
                color="Businesses",
                color_continuous_scale="Blues"
            )

            style_fig(fig, height=420)

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        with st.container(border=True):

            st.markdown("### Businesses by Category")

            cat_count = (
                df.groupby("Category")
                .size()
                .reset_index(name="Businesses")
                .sort_values("Businesses", ascending=False)
            )

            fig = px.bar(
                cat_count,
                x="Category",
                y="Businesses",
                color="Businesses",
                color_continuous_scale="Viridis"
            )

            style_fig(fig, height=420)

            st.plotly_chart(fig, use_container_width=True)

    # ============================
    # ROW 2
    # ============================

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.markdown("### No Website Businesses by City")

            city_summary = (
                df.groupby("City")
                .agg(
                    Total=("Business_Name", "count"),
                    No_Website=("Has_Website", lambda x: (x == "No").sum())
                )
                .reset_index()
            )

            city_summary = city_summary.sort_values("No_Website", ascending=False)

            fig = px.bar(
                city_summary,
                x="City",
                y="No_Website",
                color="No_Website",
                color_continuous_scale="Reds"
            )

            style_fig(fig, height=420)

            st.plotly_chart(fig, use_container_width=True)

    with col2:

        with st.container(border=True):

            st.markdown("### Website Coverage by Category (%)")

            cat_summary = (
                df.groupby("Category")
                .agg(
                    Total=("Business_Name", "count"),
                    Website=("Has_Website", lambda x: (x == "Yes").sum())
                )
                .reset_index()
            )

            cat_summary["Coverage"] = (
                cat_summary["Website"] /
                cat_summary["Total"] * 100
            ).round(1)

            fig = px.bar(
                cat_summary.sort_values("Coverage"),
                x="Coverage",
                y="Category",
                orientation="h",
                color="Coverage",
                color_continuous_scale="Greens"
            )

            style_fig(fig, height=420)

            st.plotly_chart(fig, use_container_width=True)

    # ============================
    # HEATMAP
    # ============================

    with st.container(border=True):

        st.markdown("### City × Category Heatmap")

        heat = pd.pivot_table(
            df,
            index="City",
            columns="Category",
            values="Business_Name",
            aggfunc="count",
            fill_value=0
        )

        fig = px.imshow(
            heat,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="YlOrRd"
        )

        style_fig(fig, height=500)

        st.plotly_chart(fig, use_container_width=True)

    # ============================
    # SUMMARY TABLES
    # ============================

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.markdown("### City Summary")

            city_table = (
                df.groupby("City")
                .agg(
                    Businesses=("Business_Name", "count"),
                    Website=("Has_Website", lambda x: (x=="Yes").sum()),
                    No_Website=("Has_Website", lambda x: (x=="No").sum())
                )
                .sort_values("Businesses", ascending=False)
            )

            st.dataframe(city_table, use_container_width=True)

    with col2:

        with st.container(border=True):

            st.markdown("### Category Summary")

            cat_table = (
                df.groupby("Category")
                .agg(
                    Businesses=("Business_Name", "count"),
                    Website=("Has_Website", lambda x: (x=="Yes").sum()),
                    No_Website=("Has_Website", lambda x: (x=="No").sum())
                )
                .sort_values("Businesses", ascending=False)
            )

            st.dataframe(cat_table, use_container_width=True)

    # ============================
    # KEY INSIGHTS
    # ============================

    st.markdown("---")

    st.subheader("📌 Key Insights")

    largest_city = city_table.index[0]
    largest_cat = cat_table.index[0]

    max_no_city = city_summary.sort_values(
        "No_Website",
        ascending=False
    ).iloc[0]

    max_no_cat = (
        cat_summary.assign(No_Website=cat_summary["Total"]-cat_summary["Website"])
        .sort_values("No_Website", ascending=False)
        .iloc[0]
    )

    st.markdown(f"""
### 🌆 City Insights

- **{largest_city}** has the highest number of businesses.
- **{max_no_city['City']}** has the largest number of businesses without websites (**{int(max_no_city['No_Website'])}**).
- Cities with lower website adoption present the greatest opportunity for digital transformation.

### 🏢 Category Insights

- **{largest_cat}** is the largest business category.
- **{max_no_cat['Category']}** has the greatest number of businesses without websites.
- Categories with low website coverage should be prioritized for website development and Google Business Profile optimization.

### 💡 Recommendations

- Prioritize outreach in cities having the highest concentration of businesses without websites.
- Focus first on categories with the lowest digital adoption.
- Businesses already offering quality services can benefit significantly from an online presence.
- Use the heatmap above to identify city–category combinations with the greatest digital opportunity.
""")
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

        st.header("🏆 Top Opportunity Businesses")

        no_web = df[df["Has_Website"] == "No"].copy()

        if len(no_web) == 0:
            st.info("No opportunity businesses found.")
            st.stop()

        # -------------------------------------------------------
        # Digital Opportunity Score
        # -------------------------------------------------------

        cat_demand = df.groupby("Category")["Business_Name"].count()

        cat_demand_norm = (
            (cat_demand - cat_demand.min()) /
            (cat_demand.max() - cat_demand.min())
        ).to_dict()

        no_web["Rating_Norm"] = (
            (no_web["Rating"] - df["Rating"].min()) /
            (df["Rating"].max() - df["Rating"].min())
        )

        no_web["Amenity_Gap_Score"] = (
            (no_web["Parking"] != "Yes").astype(int) +
            (no_web["Delivery"] != "Yes").astype(int)
        ) / 2

        no_web["Category_Demand_Score"] = (
            no_web["Category"]
            .map(cat_demand_norm)
            .fillna(0)
        )

        no_web["Digital_Opportunity_Score"] = (
            0.5 * no_web["Rating_Norm"] +
            0.3 * no_web["Amenity_Gap_Score"] +
            0.2 * no_web["Category_Demand_Score"]
        ) * 100

        no_web["Digital_Opportunity_Score"] = (
            no_web["Digital_Opportunity_Score"].round(1)
        )

        # -------------------------------------------------------
        # KPI Cards
        # -------------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Opportunity Businesses",
            len(no_web)
        )

        c2.metric(
            "Average Score",
            round(no_web["Digital_Opportunity_Score"].mean(),1)
        )

        c3.metric(
            "Highest Score",
            round(no_web["Digital_Opportunity_Score"].max(),1)
        )

        c4.metric(
            "80+ Score",
            (no_web["Digital_Opportunity_Score"]>=80).sum()
        )

        st.divider()

        # -------------------------------------------------------
        # Ranked Table
        # -------------------------------------------------------

        ranked = no_web.sort_values(
            "Digital_Opportunity_Score",
            ascending=False
        )

        top_n = st.slider(
            "Show Top Businesses",
            5,
            min(50,len(ranked)),
            min(10,len(ranked))
        )

        st.dataframe(
            ranked[
                [
                    "Business_Name",
                    "Category",
                    "City",
                    "Locality",
                    "Rating",
                    "Parking",
                    "Delivery",
                    "Digital_Opportunity_Score"
                ]
            ].head(top_n),
            hide_index=True,
            use_container_width=True
        )

        st.download_button(
            "⬇ Download CSV",
            ranked.to_csv(index=False).encode(),
            "top_opportunity_businesses.csv",
            "text/csv"
        )

        st.divider()

        # -------------------------------------------------------
        # Top Opportunity Businesses
        # -------------------------------------------------------

        fig = px.bar(
            ranked.head(top_n).sort_values("Digital_Opportunity_Score"),
            x="Digital_Opportunity_Score",
            y="Business_Name",
            orientation="h",
            color="Digital_Opportunity_Score",
            color_continuous_scale="Viridis"
        )

        style_fig(fig,height=max(350,top_n*35))

        st.plotly_chart(fig,use_container_width=True)

        # -------------------------------------------------------
        # Row 1
        # -------------------------------------------------------

        col1,col2=st.columns(2)

        with col1:

            city=no_web.groupby("City").size().reset_index(name="Businesses")

            fig=px.bar(
                city,
                x="City",
                y="Businesses",
                color="Businesses",
                title="Opportunity Businesses by City"
            )

            style_fig(fig,height=420)

            st.plotly_chart(fig,use_container_width=True)

        with col2:

            category=no_web.groupby("Category").size().reset_index(name="Businesses")

            fig=px.bar(
                category,
                x="Category",
                y="Businesses",
                color="Businesses",
                title="Opportunity Businesses by Category"
            )

            style_fig(fig,height=420)

            st.plotly_chart(fig,use_container_width=True)

        # -------------------------------------------------------
        # Row 2
        # -------------------------------------------------------

        col1,col2=st.columns(2)

        with col1:

            fig=px.histogram(
                no_web,
                x="Digital_Opportunity_Score",
                nbins=15,
                title="Opportunity Score Distribution"
            )

            style_fig(fig,height=400)

            st.plotly_chart(fig,use_container_width=True)

        with col2:

            fig=px.histogram(
                no_web,
                x="Rating",
                nbins=10,
                title="Ratings of Opportunity Businesses"
            )

            style_fig(fig,height=400)

            st.plotly_chart(fig,use_container_width=True)

        # -------------------------------------------------------
        # Row 3
        # -------------------------------------------------------

        col1,col2=st.columns(2)

        with col1:

            fig=px.pie(
                no_web,
                names="Parking",
                title="Parking Availability"
            )

            style_fig(fig,height=400)

            st.plotly_chart(fig,use_container_width=True)

        with col2:

            fig=px.pie(
                no_web,
                names="Delivery",
                title="Delivery Availability"
            )

            style_fig(fig,height=400)

            st.plotly_chart(fig,use_container_width=True)

        # -------------------------------------------------------
        # Heatmap
        # -------------------------------------------------------

        st.subheader("City × Category Opportunity Heatmap")

        heat=pd.pivot_table(
            no_web,
            index="City",
            columns="Category",
            values="Business_Name",
            aggfunc="count",
            fill_value=0
        )

        fig=px.imshow(
            heat,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="YlOrRd"
        )

        style_fig(fig,height=500)

        st.plotly_chart(fig,use_container_width=True)

        # -------------------------------------------------------
        # Insights
        # -------------------------------------------------------

        top_city = city.sort_values(
            "Businesses",
            ascending=False
        ).iloc[0]

        top_category = category.sort_values(
            "Businesses",
            ascending=False
        ).iloc[0]

        st.subheader("📌 Key Insights")

        st.markdown(f"""
### Top Opportunity Insights

- **{len(no_web)} businesses** currently do not have a website.

- Average Digital Opportunity Score is **{no_web['Digital_Opportunity_Score'].mean():.1f}**.

- **{(no_web['Digital_Opportunity_Score']>=80).sum()} businesses** have a score above **80**, making them the highest priority.

- **{top_city['City']}** has the highest number of opportunity businesses (**{top_city['Businesses']}**).

- **{top_category['Category']}** is the category with the greatest digital opportunity (**{top_category['Businesses']} businesses**).

### Recommendations

- Prioritize businesses with scores above **80**.

- Begin outreach in **{top_city['City']}**, where the concentration of opportunity businesses is highest.

- Focus on **{top_category['Category']}**, as it offers the largest potential for digital adoption.

- Businesses with good customer ratings but no website should be targeted first for maximum impact.
""")
# ---- TAB 5: RAW DATA ----
with tab5:
    with st.container(border=True):
        st.markdown("### Filtered Dataset")
        st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown(
    '<div class="footer-note">Built with Streamlit · Data: Google Maps business listings (Jharkhand) · Python analysis pipeline</div>',
    unsafe_allow_html=True,
)
#--tab 6 ratings
with tab6:

    st.header("⭐ Ratings Analysis")

    # ==============================
    # CHANGE THESE COLUMN NAMES
    # ==============================
    rating_col = "Rating"
    business_col = "Business_Name"
    category_col = "Category"
    city_col = "City"

    # Convert rating to numeric
    df[rating_col] = pd.to_numeric(df[rating_col], errors="coerce")

    # Remove missing ratings
    rating_df = df.dropna(subset=[rating_col])

    # ==============================
    # Rating Summary Cards
    # ==============================
    avg_rating = rating_df[rating_col].mean()
    highest_rating = rating_df[rating_col].max()
    lowest_rating = rating_df[rating_col].min()

    col1, col2, col3 = st.columns(3)

    col1.metric("⭐ Average Rating", f"{avg_rating:.2f}")
    col2.metric("🏆 Highest Rating", f"{highest_rating:.1f}")
    col3.metric("📉 Lowest Rating", f"{lowest_rating:.1f}")

    st.divider()

    # ==============================
    # Rating Distribution
    # ==============================
    st.subheader("📊 Rating Distribution")

    fig = px.histogram(
        rating_df,
        x=rating_col,
        nbins=10,
        title="Distribution of Business Ratings",
        color_discrete_sequence=["royalblue"]
    )

    fig.update_layout(
        xaxis_title="Rating",
        yaxis_title="Number of Businesses"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Average Rating by Category
    # ==============================
    st.subheader("📈 Average Rating by Category")

    cat_rating = (
        rating_df.groupby(category_col)[rating_col]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = px.bar(
        cat_rating,
        x=rating_col,
        y=category_col,
        orientation="h",
        color=rating_col,
        color_continuous_scale="Viridis",
        title="Average Rating by Category"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Average Rating by City
    # ==============================
    st.subheader("🏙 Average Rating by City")

    city_rating = (
        rating_df.groupby(city_col)[rating_col]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = px.bar(
        city_rating,
        x=city_col,
        y=rating_col,
        color=rating_col,
        color_continuous_scale="Blues",
        title="Average Rating by City"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Top Rated Businesses
    # ==============================
    st.subheader("🏆 Top 20 Highest Rated Businesses")

    top20 = (
        rating_df.sort_values(rating_col, ascending=False)
        [[business_col, category_col, city_col, rating_col]]
        .head(20)
    )

    st.dataframe(top20, use_container_width=True)

    st.divider()

    # ==============================
    # Rating Statistics
    # ==============================
    high_count = (rating_df[rating_col] >= 4.5).sum()
    good_count = ((rating_df[rating_col] >= 4.0) &
                  (rating_df[rating_col] < 4.5)).sum()
    average_count = ((rating_df[rating_col] >= 3.0) &
                     (rating_df[rating_col] < 4.0)).sum()
    low_count = (rating_df[rating_col] < 3.0).sum()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("🌟 4.5+ Ratings", high_count)
    c2.metric("👍 4.0–4.5", good_count)
    c3.metric("🙂 3.0–4.0", average_count)
    c4.metric("⚠ Below 3.0", low_count)

    st.divider()

    # ==============================
    # Key Insights
    # ==============================
    top_category = cat_rating.iloc[0]
    bottom_category = cat_rating.iloc[-1]

    top_city = city_rating.iloc[0]
    bottom_city = city_rating.iloc[-1]

    st.subheader("📌 Key Rating Insights")

    st.markdown(f"""
### ⭐ Overall Performance

- Average business rating is **{avg_rating:.2f}/5**.
- Highest observed rating is **{highest_rating:.1f}/5**.
- Lowest observed rating is **{lowest_rating:.1f}/5**.

### 📊 Rating Breakdown

- 🌟 **{high_count} businesses** have an excellent rating (4.5+).
- 👍 **{good_count} businesses** are rated between 4.0 and 4.5.
- 🙂 **{average_count} businesses** are rated between 3.0 and 4.0.
- ⚠ **{low_count} businesses** have ratings below 3.0.

### 🏆 Best Performing Category

**{top_category[category_col]}** has the highest average rating of **{top_category[rating_col]:.2f}**.

### 📉 Lowest Performing Category

**{bottom_category[category_col]}** has the lowest average rating of **{bottom_category[rating_col]:.2f}**.

### 🌆 Best Rated City

**{top_city[city_col]}** has the highest average business rating of **{top_city[rating_col]:.2f}**.

### 🏙 Lowest Rated City

**{bottom_city[city_col]}** has the lowest average business rating of **{bottom_city[rating_col]:.2f}**.

### 💡 Recommendations

- Focus improvement efforts on businesses with ratings below **4.0**.
- Encourage highly rated businesses to strengthen their online presence and collect more customer reviews.
- Analyze practices of top-rated categories and cities to identify strategies that can be adopted by lower-performing businesses.
- Regular monitoring of customer feedback can help improve service quality and maintain high ratings.
""")
#--tab 7 key insights
with tab7:
    with st.container(border=True):
        st.markdown("""
## 📌 Key Insights & Final Recommendations

### 1. Prioritize Restaurants & Cafes for Outreach
These categories have the highest share of businesses without websites (8.9% and 6.0% respectively) and would benefit most from an online presence through menus, reviews, and online ordering.

### 2. Focus on Jamshedpur and Dhanbad
These two cities together account for **83%** of all businesses without websites, making them the highest-impact locations for digital outreach.

### 3. Target High Opportunity Businesses First
Begin with the **16 High Opportunity businesses** that have ratings above **4.0** but still lack websites, as they offer the highest ROI for digital adoption.

### 4. Promote Existing Amenities Online
Nearly half of the businesses already provide facilities such as parking or delivery. A website or Google Business Profile can immediately showcase these services.

### 5. Recommend Cost-Effective Digital Solutions
Instead of expensive custom websites, suggest a **Google Business Profile** along with a **single-page, mobile-friendly website** containing:
- Contact Details
- Business Hours
- Location Map
- Services/Menu
- Customer Reviews

### 6. Avoid Fully Digitized Categories
Schools, Banks, Grocery Stores, and Supermarkets already have complete website coverage. Outreach efforts should instead focus on underserved sectors.

### 7. Improve Service Alongside Digital Presence
Businesses without websites have a lower average rating (**3.90**) compared to businesses with websites (**4.23**). Combining digital onboarding with basic service improvements can produce better business outcomes.

### 8. Use the Digital Opportunity Score
The **Digital Opportunity Score** combines ratings, amenities, and category demand into a single ranking, making it the most reliable list for prioritizing outreach.

### 9. Plan Field Visits Using the Interactive Map
Opportunity businesses are geographically clustered. Visiting businesses locality-by-locality is significantly more efficient than random visits.

### 10. Differentiate Strategies by Market Saturation
For highly digitized category-city combinations, businesses should compete through better website quality and SEO rather than simply having a website.

---


        """)