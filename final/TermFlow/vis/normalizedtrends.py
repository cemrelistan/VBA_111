import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Normalize Edilmiş Trend Analizi", layout="wide")
st.title("📈 Gerçek Popülarite Analizi: Alanlara Göre Normalizasyon")
st.markdown("""
Bu dashboard, kelime sayılarını **o yıl o alanda yayınlanan toplam makale sayısına** oranlayarak "Hype"ı temizler.
Grafikler, **her 10.000 makale başına düşen kullanım sıklığını** gösterir.
""")

# ---------------------------------------------------------
# 1. VERİ YÜKLEME VE BİRLEŞTİRME MOTORU
# ---------------------------------------------------------
@st.cache_data
def load_and_merge_data():
    # Dosya yolları
    files = {
        "words": "all_data_merged.csv",
        "domains": "domain_yearly_stats.csv"
    }
    
    # Dosyalar var mı kontrol et
    if not os.path.exists(files['words']) or not os.path.exists(files['domains']):
        st.error("Gerekli CSV dosyaları (all_data_merged.csv veya domain_yearly_stats.csv) bulunamadı.")
        return None

    try:
        # --- A. KELİME VERİSİNİ YÜKLE (WORDS) ---
        df_words = pd.read_csv(files['words'])
        df_words.columns = [str(c).lower().strip() for c in df_words.columns]
        
        # 'Unnamed: 0' veya benzeri sütunu 'bigram' yap
        term_col = None
        for col in ['unnamed: 0', 'bigram', 'term', 'keyword']:
            if col in df_words.columns:
                df_words.rename(columns={col: 'bigram'}, inplace=True)
                term_col = 'bigram'
                break
        
        if not term_col: return None

        # Wide to Long (Yılları satıra indir)
        year_cols = [c for c in df_words.columns if c.isdigit() and 1990 <= int(c) <= 2030]
        fixed_cols = [c for c in df_words.columns if c not in year_cols]
        
        df_words_long = df_words.melt(id_vars=fixed_cols, value_vars=year_cols, var_name='year', value_name='word_count')
        df_words_long['year'] = pd.to_numeric(df_words_long['year'])
        df_words_long['word_count'] = pd.to_numeric(df_words_long['word_count']).fillna(0)

        # --- B. ALAN İSTATİSTİKLERİNİ YÜKLE (DOMAINS) ---
        df_domains = pd.read_csv(files['domains'])
        df_domains.columns = [str(c).lower().strip() for c in df_domains.columns]
        
        # Domain sütununu bul
        if 'domain' in df_domains.columns:
            df_domains.rename(columns={'domain': 'category'}, inplace=True)
        
        # Wide to Long (Domain verisi için)
        d_year_cols = [c for c in df_domains.columns if c.isdigit() and 1990 <= int(c) <= 2030]
        d_fixed_cols = [c for c in df_domains.columns if c not in d_year_cols]
        
        df_domains_long = df_domains.melt(id_vars=d_fixed_cols, value_vars=d_year_cols, var_name='year', value_name='total_papers')
        df_domains_long['year'] = pd.to_numeric(df_domains_long['year'])
        df_domains_long['total_papers'] = pd.to_numeric(df_domains_long['total_papers']).fillna(1) # 0'a bölünmeyi önlemek için 1

        # --- C. BİRLEŞTİRME (MERGE) ---
        # Category ve Year üzerinden eşleştir
        # Önce kategori isimlerini temizleyelim ki eşleşme hatası olmasın
        df_words_long['category'] = df_words_long['category'].astype(str).str.lower().str.strip()
        df_domains_long['category'] = df_domains_long['category'].astype(str).str.lower().str.strip()

        merged_df = pd.merge(df_words_long, df_domains_long, on=['category', 'year'], how='inner')

        # --- D. NORMALİZASYON HESAPLAMASI ---
        # Formül: (Kelime Sayısı / Toplam Makale) * 10,000
        merged_df['normalized_freq'] = (merged_df['word_count'] / merged_df['total_papers']) * 10000
        
        return merged_df

    except Exception as e:
        st.error(f"Veri işleme hatası: {e}")
        return None

# ---------------------------------------------------------
# 2. GÖRSELLEŞTİRME ARAYÜZÜ
# ---------------------------------------------------------

df = load_and_merge_data()

if df is not None:
    # Benzersiz kategorileri bul
    categories = sorted(df['category'].unique())
    
    # 8 Kategori için Sekmeler (Tabs) Oluştur
    tabs = st.tabs([cat.title().replace("_", " ") for cat in categories])

    for i, category in enumerate(categories):
        with tabs[i]:
            # --- BU KATEGORİNİN VERİSİNİ AL ---
            cat_data = df[df['category'] == category]
            
            # --- TOP 5 KELİMEYİ BUL ---
            # Neye göre Top 5? Toplam 'Normalized Score'a göre mi, yoksa Ham Sayıya göre mi?
            # Genelde popülarite Ham Sayı ile belirlenir, trend Normalize ile gösterilir.
            total_counts = cat_data.groupby('bigram')['word_count'].sum().sort_values(ascending=False)
            top_5_words = total_counts.head(5).index.tolist()
            
            # Sadece bu 5 kelimenin verisini filtrele
            plot_data = cat_data[cat_data['bigram'].isin(top_5_words)]
            
            # --- GRAFİK ÇİZ ---
            fig = px.line(
                plot_data,
                x='year',
                y='normalized_freq',
                color='bigram',
                markers=True,
                title=f"{category.title()} Alanında En Popüler 5 Terimin Gerçek Trendi",
                labels={
                    'normalized_freq': 'Yoğunluk (10.000 Makale Başına)',
                    'year': 'Yıl',
                    'bigram': 'Terim'
                },
                template="plotly_white",
                height=500
            )
            
            # Çizgileri biraz kalınlaştır ve hover detaylarını ayarla
            fig.update_traces(line=dict(width=3))
            fig.update_layout(hovermode="x unified") # Mouse ile gelince hepsini göster
            
            st.plotly_chart(fig, use_container_width=True)
            
            # --- AÇIKLAMA KUTUSU ---
            st.info(f"""
            💡 **Analiz:**
            Yukarıdaki grafik, **{category.title()}** alanında en çok geçen 5 terimin, literatür hacmine göre düzeltilmiş popülaritesini gösterir.
            Eğer bir çizgi aşağı iniyorsa, bu terimin sayısı artsa bile **alana olan hakimiyeti azalıyor** demektir.
            """)
            
            # --- İSTEĞE BAĞLI: HAM VERİ TABLOSU ---
            with st.expander(f"{category.title()} İçin Veri Tablosunu Göster"):
                pivot_view = plot_data.pivot(index='year', columns='bigram', values='normalized_freq')
                st.dataframe(pivot_view.style.format("{:.2f}"))

else:
    st.warning("Veriler yüklenemedi. Lütfen CSV dosyalarının proje klasöründe olduğundan emin olun.")