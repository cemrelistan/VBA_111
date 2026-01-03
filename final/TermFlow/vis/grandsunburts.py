import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI
# -----------------------------------------------------------------------------
st.set_page_config(page_title="ArXiv Bigram Analizi", layout="wide")

st.title("🔗 ArXiv Bigram (İkili Terim) Analizi")
st.markdown("""
Bu dashboard, yüklenen birleştirilmiş veri seti üzerinden akademik terimlerin **(Bigrams)** yıllara göre popülaritesini ve kategorik dağılımını analiz eder.
""")

# -----------------------------------------------------------------------------
# 2. VERİ YÜKLEME VE İŞLEME (TEK DOSYA - WIDE FORMAT)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=True)
def load_data(file_path="all_data_merged.csv"):
    if not os.path.exists(file_path):
        st.error(f"'{file_path}' dosyası bulunamadı! Lütfen dosyayı proje klasörüne ekleyin.")
        return None

    try:
        df = pd.read_csv(file_path)
        
        # Sütun isimlerini temizle (küçük harf, boşluksuz)
        df.columns = [str(c).lower().strip() for c in df.columns]

        # --- DÜZELTME 1: 'unnamed: 0' SÜTUNUNU 'bigram' YAP ---
        # Senin dosyanın özel durumu bu
        if 'unnamed: 0' in df.columns:
            df.rename(columns={'unnamed: 0': 'bigram'}, inplace=True)
        
        # Diğer olası isimleri de kontrol et
        elif 'term' in df.columns:
            df.rename(columns={'term': 'bigram'}, inplace=True)

        # Bigram sütunu yoksa hata ver
        if 'bigram' not in df.columns:
            st.error("Veri setinde kelime sütunu (bigram) bulunamadı.")
            return None

        # --- DÜZELTME 2: BOŞLUKLARI DOLDUR (NaN -> 0) ---
        # Yıl sütunlarındaki boşlukları 0 yapalım ki grafik kopmasın
        df.fillna(0, inplace=True)

        # --- DÜZELTME 3: WIDE TO LONG (YILLARI DÖNÜŞTÜRME) ---
        # Sadece sayısal yıl sütunlarını bul (Örn: 1990, 2020...)
        year_cols = [c for c in df.columns if c.isdigit() and 1900 <= int(c) <= 2030]
        
        if year_cols:
            # Sabit kalacak sütunlar (Bigram, Category, Total)
            # Eğer total veya category yoksa onları korumaya çalışma
            fixed_cols = [c for c in df.columns if c not in year_cols]
            
            # Melt işlemi: Yılları satıra indir
            df_long = df.melt(
                id_vars=fixed_cols, 
                value_vars=year_cols, 
                var_name='year', 
                value_name='count'
            )
            
            # Veri tipi düzeltme
            df_long['year'] = pd.to_numeric(df_long['year'], errors='coerce')
            df_long['count'] = pd.to_numeric(df_long['count'], errors='coerce')
            
            return df_long
        else:
            st.error("Yıl sütunları bulunamadı (1990-2030 arası).")
            return None

    except Exception as e:
        st.error(f"Dosya okunurken hata oluştu: {e}")
        return None

# -----------------------------------------------------------------------------
# 3. TOP 12 FİLTRELEME (TOTAL SÜTUNUNU KULLANARAK)
# -----------------------------------------------------------------------------
def filter_top_n_per_category(df, n=12):
    # Senin dosyalarda 'total' sütunu olduğu için işimiz çok kolay
    if 'total' in df.columns:
        # Tekilleştir: Her bigram için tek bir satır al
        unique_bigrams = df[['category', 'bigram', 'total']].drop_duplicates()
        
        # Her kategoride en yüksek 'total'e sahip n bigramı seç
        top_terms = unique_bigrams.groupby('category').apply(
            lambda x: x.nlargest(n, 'total')
        ).reset_index(drop=True)
        
        # Ana veriyi sadece bu seçilenler için filtrele
        merged_df = pd.merge(df, top_terms[['category', 'bigram']], on=['category', 'bigram'], how='inner')
        return merged_df
    else:
        # Total yoksa kendimiz hesaplarız
        total_counts = df.groupby(['category', 'bigram'])['count'].sum().reset_index()
        top_terms = total_counts.groupby('category').apply(
            lambda x: x.nlargest(n, 'count')
        ).reset_index(drop=True)
        merged_df = pd.merge(df, top_terms[['category', 'bigram']], on=['category', 'bigram'], how='inner')
        return merged_df

# -----------------------------------------------------------------------------
# 4. İSTATİSTİK HESAPLAMA
# -----------------------------------------------------------------------------
def calculate_statistics(df):
    stats = df.groupby(['category', 'bigram'])['count'].agg(
        Yıllık_Ortalama='mean',
        Standart_Sapma='std',
        Maksimum_Görülme='max'
    ).reset_index()
    
    # Toplamı ekle
    if 'total' in df.columns:
        totals = df[['category', 'bigram', 'total']].drop_duplicates()
        stats = pd.merge(stats, totals, on=['category', 'bigram'])
    else:
        totals = df.groupby(['category', 'bigram'])['count'].sum().reset_index()
        totals.rename(columns={'count': 'total'}, inplace=True)
        stats = pd.merge(stats, totals, on=['category', 'bigram'])
        
    return stats.round(2)

# -----------------------------------------------------------------------------
# UYGULAMA AKIŞI
# -----------------------------------------------------------------------------

# A. Veriyi Yükle
df_raw = load_data("all_data_merged.csv")

if df_raw is not None:
    # B. Filtrele (Her kategoriden en büyük 12 Bigram)
    df_filtered = filter_top_n_per_category(df_raw, n=12)
    
    # C. İstatistikleri Hazırla
    stats_df = calculate_statistics(df_filtered)

    # --- LAYOUT ---
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("🌞 Kategorik Bigram Dağılımı")
        
        # Sunburst verisi hazırlığı
        if 'total' in df_filtered.columns:
            # Sadece tekil bigramları al
            df_sun = df_filtered[['category', 'bigram', 'total']].drop_duplicates()
            val_col = 'total'
        else:
            df_sun = df_filtered.groupby(['category', 'bigram'])['count'].sum().reset_index()
            val_col = 'count'

        fig_sun = px.sunburst(
            df_sun,
            path=['category', 'bigram'],
            values=val_col,
            color=val_col,
            color_continuous_scale='RdBu_r',
            height=600
        )
        st.plotly_chart(fig_sun, use_container_width=True)

    with col2:
        st.subheader("📈 Trend Analizi")
        
        # Seçim Kutusu
        unique_options = df_filtered[['category', 'bigram']].drop_duplicates()
        unique_options['label'] = unique_options['category'] + " - " + unique_options['bigram']
        
        selected_label = st.selectbox(
            "İncelemek istediğiniz Bigram'ı seçin:",
            unique_options['label'].sort_values()
        )
        
        if selected_label:
            sel_cat, sel_term = selected_label.split(" - ")
            
            # Çizgi Grafik
            subset_trend = df_filtered[
                (df_filtered['category'] == sel_cat) & 
                (df_filtered['bigram'] == sel_term)
            ].sort_values('year')
            
            fig_line = px.line(
                subset_trend,
                x='year',
                y='count',
                markers=True,
                title=f"'{sel_term}' Zaman İçindeki Değişimi",
                labels={'count': 'Frekans', 'year': 'Yıl'}
            )
            st.plotly_chart(fig_line, use_container_width=True)
            
            # İstatistik Kartları
            stat_row = stats_df[
                (stats_df['category'] == sel_cat) & 
                (stats_df['bigram'] == sel_term)
            ].iloc[0]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam", f"{int(stat_row['total']):,}")
            c2.metric("Ortalama", stat_row['Yıllık_Ortalama'])
            c3.metric("Std Sapma", stat_row['Standart_Sapma'])

            # --- TABLO VE YORUM ---
            st.divider()
            st.subheader(f"📋 '{sel_cat}' Alanındaki En Popüler Terimler")
            cat_stats = stats_df[stats_df['category'] == sel_cat].sort_values(by='total', ascending=False)
            st.dataframe(cat_stats, use_container_width=True)

            st.info(f"💡 **Analiz:** '{sel_term}', {sel_cat} alanında toplam {int(stat_row['total']):,} kez kullanılarak literatürde önemli bir yer edinmiştir.")

else:
    st.info("Veri bekleniyor... Lütfen 'all_data_merged.csv' dosyasının app.py ile aynı klasörde olduğundan emin olun.")