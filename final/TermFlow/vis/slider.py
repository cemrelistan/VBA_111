import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Yükselen Yıldızlar Matrisi", layout="wide")

st.title("🌟 Yükselen Yıldızlar (CAGR) - Temizlenmiş Veri")
st.markdown("""
Bu modül, verisetindeki hatalı (astronomik) sayıları temizler ve **Büyüme/Hacim** analizi yapar.
* **Otomatik Temizlik:** Yıllık kullanım sayısı **200,000**'i geçen (hatalı) veriler analizden atılır.
""")

# ---------------------------------------------------------
# 1. VERİ YÜKLEME VE KATI TEMİZLİK
# ---------------------------------------------------------
@st.cache_data
def load_and_clean_data(file_path="all_data_merged.csv"):
    if not os.path.exists(file_path):
        st.error(f"'{file_path}' bulunamadı.")
        return None

    try:
        df = pd.read_csv(file_path)
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Kelime sütunu bul
        term_col = next((c for c in ['bigram', 'term', 'keyword', 'unnamed: 0'] if c in df.columns), None)
        if term_col == 'unnamed: 0': 
            df.rename(columns={'unnamed: 0': 'bigram'}, inplace=True)
            term_col = 'bigram'
            
        if not term_col or 'category' not in df.columns:
            st.error("Gerekli sütunlar eksik.")
            return None

        # Yıl sütunlarını bul
        year_cols = [c for c in df.columns if c.isdigit() and 1990 <= int(c) <= 2030]
        
        # --- DEMİR YUMRUK TEMİZLİĞİ ---
        # 1. Her şeyi sayıya çevir (Hata verenleri NaN yap)
        for yc in year_cols:
            df[yc] = pd.to_numeric(df[yc], errors='coerce')
        
        # 2. NaN olanları 0 yap
        df[year_cols] = df[year_cols].fillna(0)

        # 3. MANTIK SINIRI (Hard Cap)
        # Bir kelime bir yılda 200.000'den fazla geçemez. (ArXiv'in yıllık kapasitesi belli)
        # Eğer bir satırda bile bu sınırı aşan sayı varsa, o kelimeyi komple çöpe at.
        # Çünkü o veri bozuktur.
        MAX_REALISTIC_COUNT = 200000 
        
        # Satır bazında kontrol: Herhangi bir yılı max sınırdan büyük olanları bulma
        mask_valid = (df[year_cols] <= MAX_REALISTIC_COUNT).all(axis=1)
        
        df_clean = df[mask_valid].copy()
        
        dropped_count = len(df) - len(df_clean)
        if dropped_count > 0:
            st.toast(f"🧹 Veri Temizliği: {dropped_count} adet hatalı (astronomik değerli) satır silindi.", icon="🗑️")

        return df_clean, year_cols

    except Exception as e:
        st.error(f"Hata: {e}")
        return None

# ---------------------------------------------------------
# 2. HESAPLAMA MOTORU
# ---------------------------------------------------------
def calculate_growth(df, category, start_year, end_year):
    cat_df = df[df['category'] == category].copy()
    s_col, e_col = str(start_year), str(end_year)
    
    if s_col not in cat_df.columns or e_col not in cat_df.columns:
        return None

    # Hacim Filtresi: Başlangıçta 0 olanları almayalım (Sonsuz büyüme sorunu)
    # Bitişte en az 5 kez geçsin
    cat_df = cat_df[(cat_df[s_col] > 0) & (cat_df[e_col] >= 5)]
    
    # CAGR Hesapla
    years = end_year - start_year
    if years < 1: years = 1
    
    cat_df['CAGR'] = ((cat_df[e_col] / cat_df[s_col]) ** (1/years)) - 1
    cat_df['Growth_Percent'] = cat_df['CAGR'] * 100
    cat_df['Volume'] = cat_df[e_col]
    
    # İkinci Temizlik: Aşırı uçuk büyüme oranlarını (%10.000 gibi) tıraşla
    # Bunlar genelde 1'den 1000'e çıkan kelimelerdir, grafiği bozar.
    cat_df = cat_df[cat_df['Growth_Percent'] < 5000] 
    
    return cat_df

# ---------------------------------------------------------
# 3. ARAYÜZ
# ---------------------------------------------------------
data_pack = load_and_clean_data()

if data_pack:
    df_clean, years = data_pack
    years_int = sorted([int(y) for y in years])
    
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        
        # Kategori
        cats = sorted(df_clean['category'].unique())
        sel_cat = st.selectbox("Alan Seç:", cats, index=0)
        
        st.divider()
        
        # Zaman
        min_y, max_y = years_int[0], years_int[-1]
        def_start = max_y - 10 if (max_y - 10) >= min_y else min_y
        
        rng = st.slider("Zaman Aralığı:", min_y, max_y, (def_start, max_y))
        start_y, end_y = rng
        
        if start_y >= end_y:
            st.error("Başlangıç yılı bitişten küçük olmalı.")
            st.stop()
            
        st.divider()
        
        # MANUEL X EKSENİ SINIRI (SENİN İSTEDİĞİN ÖZELLİK)
        st.subheader("🔍 Grafik Odaklanma")
        use_manual_limit = st.checkbox("X Eksenine (Hacim) Sınır Koy", value=False)
        
        x_limit = None
        if use_manual_limit:
            # Kullanıcıya max değeri seçtiriyoruz
            x_limit = st.number_input("Maksimum Hacim (X Ekseni):", min_value=100, value=10000, step=1000)

    # Hesapla
    res_df = calculate_growth(df_clean, sel_cat, start_y, end_y)
    
    if res_df is not None and not res_df.empty:
        
        # Grafik
        fig = px.scatter(
            res_df,
            x="Volume",
            y="Growth_Percent",
            hover_name="bigram",
            hover_data={"Volume": True, "Growth_Percent": ":.1f"},
            color="Growth_Percent",
            title=f"Growth-Share Matrisi: {sel_cat} ({start_y}-{end_y})",
            labels={"Volume": f"Toplam Hacim ({end_y})", "Growth_Percent": "Büyüme Hızı (%)"},
            color_continuous_scale="RdYlGn",
            height=650,
            log_x=True if not use_manual_limit else False # Manuel sınır varsa log kapatılabilir veya açık kalabilir
        )
        
        # Ortalama Çizgileri
        fig.add_hline(y=res_df['Growth_Percent'].median(), line_dash="dot", annotation_text="Ortalama Büyüme")
        
        # X EKSENİ SINIRLAMA
        if use_manual_limit and x_limit:
            fig.update_xaxes(range=[0, x_limit]) # Logaritmik değilse lineer sınır
            # Eğer log açıksa range logaritması alınmış olmalı ama basitlik için lineer yaptık yukarıda
            
        st.plotly_chart(fig, use_container_width=True)
        
        # Bilgi
        st.markdown(f"**Veri Notu:** {sel_cat} alanında, {start_y}-{end_y} arasında analiz edilen kelime sayısı: **{len(res_df)}**")
        
    else:
        st.warning("Veri yok veya filtreler çok sıkı.")