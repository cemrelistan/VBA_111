import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# ---------------------------------------------------------
# 1. SAYFA AYARLARI
# ---------------------------------------------------------
st.set_page_config(
    page_title="ArXiv Trend Analizi",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 ArXiv Konu Trendleri (Multi-Series Line Chart)")
st.markdown("""
Bu grafik, D3.js 'Multiple Series Line Chart' tarzında hazırlanmıştır. 
Hangi konunun hangi dönemde zirve yaptığını net bir şekilde görebilirsiniz.
""")

# ---------------------------------------------------------
# 2. VERİ YÜKLEME VE BİRLEŞTİRME FONKSİYONU
# ---------------------------------------------------------
@st.cache_data
def load_and_merge_data(folder_path="data"):
    # Klasördeki tüm .csv dosyalarını bul
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    if not all_files:
        return None

    df_list = []
    
    for filename in all_files:
        try:
            # CSV dosyasını oku
            df = pd.read_csv(filename)
            
            # Sütun isimlerini kontrol et ve standartlaştır (küçük harf yap)
            df.columns = [c.lower() for c in df.columns]
            
            # Eğer dosya boşsa veya gerekli sütunlar yoksa atla
            if 'period' not in df.columns or 'count' not in df.columns:
                continue

            # Dosya isminden "Konu Adını" çıkar
            # Örnek: "data/artificial_intelligence_quarterly_counts.csv" -> "Artificial Intelligence"
            base_name = os.path.basename(filename) # dosya adı
            topic_slug = base_name.replace("_quarterly_counts.csv", "").replace(".csv", "")
            topic_name = topic_slug.replace("_", " ").title() # Alt tireleri boşluk yap, Baş Harfi Büyüt
            
            # Veriye 'Topic' sütunu ekle (Bu çizgi rengi olacak)
            df['topic'] = topic_name
            
            df_list.append(df)
            
        except Exception as e:
            st.error(f"Hata: {filename} dosyası okunurken sorun oluştu. {e}")
            continue

    if df_list:
        # Tüm küçük tabloları alt alta birleştir (Long Format)
        main_df = pd.concat(df_list, ignore_index=True)
        return main_df
    else:
        return None

# ---------------------------------------------------------
# 3. VERİYİ İŞLEME VE GÖRSELLEŞTİRME
# ---------------------------------------------------------

# Veriyi yükle (data klasöründen)
# Eğer 'data' klasörün yoksa kod hata vermesin diye kontrol ediyoruz:
if not os.path.exists("data"):
    os.makedirs("data")
    st.warning("⚠️ 'data' klasörü oluşturuldu. Lütfen CSV dosyalarınızı bu klasörün içine atıp sayfayı yenileyin.")
    st.stop()

df = load_and_merge_data("data")

if df is not None:
    # --- A. FİLTRELEME (SIDEBAR) ---
    st.sidebar.header("Filtreler")
    
    # Konu Seçimi
    all_topics = sorted(df['topic'].unique())
    selected_topics = st.sidebar.multiselect(
        "Görüntülenecek Konuları Seçin:", 
        all_topics, 
        default=all_topics # Varsayılan olarak hepsi seçili
    )
    
    # Seçilenlere göre veriyi süz
    filtered_df = df[df['topic'].isin(selected_topics)]
    
    # Sıralama (Period'un düzgün görünmesi için)
    filtered_df = filtered_df.sort_values(by='period')

    # --- B. GRAFİK OLUŞTURMA (D3 Style) ---
    if not filtered_df.empty:
        # Plotly Line Chart
        fig = px.line(
            filtered_df, 
            x="period", 
            y="count", 
            color="topic",              # Her konu ayrı renk
            markers=True,               # Noktaları göster (D3 tarzı için opsiyonel, veri azsa güzel durur)
            title="Dönemsel Makale Sayıları (Çeyrek Bazlı)",
            template="plotly_white",    # D3 benzeri temiz beyaz arka plan
            labels={"period": "Dönem (Yıl-Çeyrek)", "count": "Makale Sayısı", "topic": "Konu Başlığı"},
            hover_data={"period": True, "count": True, "topic": False} # Mouse üzerine gelince ne yazsın
        )

        # Grafiği Özelleştirme (Daha profesyonel görünüm)
        fig.update_layout(
            hovermode="x unified",  # Mouse ile gezince tüm çizgilerin değerini aynı anda gösterir (Çok önemli!)
            legend=dict(
                orientation="h",    # Lejantı yatay yap
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                showgrid=False,     # Dikey çizgileri kaldır (Daha temiz görünüm)
            ),
            yaxis=dict(
                showgrid=True,      # Yatay çizgiler kalsın (Değeri okumak için)
                gridcolor='lightgray'
            )
        )
        
        # Çizgileri biraz kalınlaştır ve yumuşat
        fig.update_traces(line=dict(width=3), mode='lines+markers')

        # Ekrana Bas
        st.plotly_chart(fig, use_container_width=True)

        # --- C. ANALİZ METNİ (OTOMATİK) ---
        st.subheader("💡 Hızlı Analiz")
        # En son dönemdeki lideri bul
        last_period = filtered_df['period'].max()
        last_data = filtered_df[filtered_df['period'] == last_period]
        if not last_data.empty:
            leader = last_data.loc[last_data['count'].idxmax()]
            st.info(f"Son dönem ({last_period}) verilerine göre en popüler konu **{leader['topic']}** ({leader['count']} makale).")

    else:
        st.warning("Lütfen sol taraftan en az bir konu seçin.")
else:
    st.error("Veri bulunamadı! 'data' klasörüne CSV dosyalarını yüklediğinizden emin olun.")