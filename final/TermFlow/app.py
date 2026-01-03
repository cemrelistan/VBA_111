import streamlit as st
import os
from data_loader import DataLoader
from plot_manager import PlotManager

# --- PAGE SETTINGS ---
st.set_page_config(page_title="TermFlow AI", layout="wide", page_icon="📈")

# CSS (TermFlow Theme)
st.markdown("""
<style>
    .main-title { font-size: 3rem; font-weight: 800; background: -webkit-linear-gradient(left, #00f2c3, #0098f0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    div.stButton > button { background-color: #00f2c3; color: black; border-radius: 5px; font-weight: bold;}
    div[data-testid="stMetric"] { background-color: #1E1E1E; padding: 10px; border-radius: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
loader = DataLoader()
plotter = PlotManager()

# Load Data
with st.spinner("Loading Data Warehouse..."):
    df = loader.load_main_data()
    df_domain = loader.load_domain_stats()

if df is None:
    st.error("Data could not be loaded! Check 'data/all_data_merged.csv' file.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=200)
    st.title("TermFlow")
    page = st.radio("Navigation", ["🚀 Dashboard (Overview)", "🧭 Trend Explorer (Discovery)", "🔍 Deep Dive (Search)"])
    st.markdown("---")
    st.info(f"📚 Dataset: **{len(df):,}** Terms")

# --- PAGE 1: DASHBOARD (STATIC IMAGES) ---
if page == "🚀 Dashboard (Overview)":
    st.markdown('<p class="main-title">Overview</p>', unsafe_allow_html=True)
    st.write("Static summary of the biggest trends in the scientific world.")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("☁️ Global Word Cloud")
        if os.path.exists("assets/cloud_map.png"):
            st.image("assets/cloud_map.png", use_container_width=True)
        else:
            st.warning("Image not found: assets/cloud_map.png")
            
    with col2:
        st.subheader("📅 Seasonality")
        if os.path.exists("assets/mounth_of_year.png"):
            st.image("assets/mounth_of_year.png", use_container_width=True)

    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📚 Total Category Distribution")
        if os.path.exists("assets/total_category.png"):
            st.image("assets/total_category.png", use_container_width=True)
    with c2:
        st.subheader("📊 Category Counters")
        if os.path.exists("assets/counter_by_category.png"):
            st.image("assets/counter_by_category.png", use_container_width=True)

# --- PAGE 2: EXPLORER (INTERACTIVE CHARTS) ---
elif page == "🧭 Trend Explorer (Discovery)":
    st.header("Data Mining and Discovery")
    
    # ADDED 4th TAB: Stability Analysis
    tab1, tab2, tab3, tab4 = st.tabs(["🌟 Rising Stars", "🧩 Relation Network", "⚖️ Normalized Trends", "📊 Stability Analysis"])
    
    with tab1:
        st.markdown("**Growth vs Volume:** Which terms are both highly discussed and growing fast?")
        cat_select = st.selectbox("Select Field:", df['category'].unique())
        # Auto-detect year range
        years = [int(c) for c in df.columns if c.isdigit()]
        min_y, max_y = min(years), max(years)
        
        y_range = st.slider("Year Range", min_y, max_y, (max_y-5, max_y))
        
        if st.button("Generate Matrix"):
            fig = plotter.plot_growth_matrix(df, cat_select, y_range[0], y_range[1])
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("**Cross-Disciplinary Flow:** How popular is a term in two different fields?")
        col_cat1, col_cat2 = st.columns(2)
        categories = df['category'].unique().tolist()
        with col_cat1:
            cat1 = st.selectbox("1st Field:", categories, index=0)
        with col_cat2:
            cat2 = st.selectbox("2nd Field:", categories, index=1 if len(categories) > 1 else 0)
        
        if cat1 != cat2:
            fig = plotter.plot_relation_scatter(df, cat1, cat2)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Please select two different fields.")

    with tab3:
        if df_domain is not None:
            st.markdown("**True Popularity:** Trends normalized by article count.")
            norm_cat = st.selectbox("Field:", df['category'].unique(), key="norm_cat")
            fig = plotter.plot_normalized_trend(df, df_domain, norm_cat)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Normalized data (domain_yearly_stats.csv) not found.")

    # --- NEW TAB FOR STANDARD DEVIATION ---
# --- TAB 4: STABILITY DISTRIBUTION (ŞAPKA GRAFİĞİ) ---
    with tab4:
        st.markdown("**Volatility Distribution (Bell Curve):** How represents the market stability?")
        st.markdown("""
        * **Peak of the Hat (Center):** Most terms behave like this (Average stability).
        * **Right Tail (Uç Kısım):** Highly volatile/trendy terms (Risky & Fast).
        * **Left Tail (Sol Kısım):** Very static/boring terms.
        """)
        
        vol_cat = st.selectbox("Select Field for Stability:", df['category'].unique(), key="vol_cat")
        
        if st.button("Analyze Distribution"):
            # PlotManager'daki güncellediğimiz fonksiyonu çağırıyor
            fig_vol = plotter.plot_volatility_analysis(df, vol_cat)
            if fig_vol:
                st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.warning("Not enough data to create a distribution curve.")

# --- PAGE 3: DEEP DIVE (SEARCH) ---
elif page == "🔍 Deep Dive (Search)":
    st.header("Detailed Term Analysis")
    
    all_terms = df['bigram'].unique().tolist()
    search_term = st.selectbox("Search Term:", options=all_terms, index=None, placeholder="E.g.: machine learning")
    
    if search_term:
        st.divider()
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # Trend and Regression
            fig_trend = plotter.plot_prediction(df, search_term)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.warning("Not enough data for this term.")
        
        with c2:
            # Category Distribution (Sunburst)
            fig_sun = plotter.plot_sunburst(df, search_term)
            st.plotly_chart(fig_sun, use_container_width=True)