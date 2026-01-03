import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Scatterplot Matrix", layout="wide")
st.title("🧩 Etkileşimli İlişki Matrisi (Scatterplot Matrix)")
st.markdown("Farklı disiplinler arasındaki terim geçişkenliğini analiz etmek için aşağıdan **en az 2 kategori** seçin.")

# ---------------------------------------------------------
# 1. VERİYİ YÜKLE VE PIVOT ET (ÇAPRAZ TABLO)
# ---------------------------------------------------------
@st.cache_data
def load_and_pivot_data(file_path="all_data_merged.csv"):
    if not os.path.exists(file_path):
        st.error(f"❌ HATA: '{file_path}' dosyası bulunamadı.")
        return None

    try:
        df = pd.read_csv(file_path)
        # Sütun isimlerini temizle
        df.columns = [str(c).lower().strip() for c in df.columns]

        # 1. Kelime Sütununu Bul
        # 'bigram', 'term', 'keyword', 'unnamed: 0' olabilir
        term_col = None
        possible_names = ['bigram', 'term', 'keyword', 'word', 'unnamed: 0']
        for name in possible_names:
            if name in df.columns:
                term_col = name
                break
        
        # Eğer unnamed: 0 ise adını bigram yapalım
        if term_col == 'unnamed: 0':
            df.rename(columns={'unnamed: 0': 'bigram'}, inplace=True)
            term_col = 'bigram'

        if not term_col:
            st.error("❌ Veri setinde kelime sütunu (bigram/term) bulunamadı.")
            st.write("Mevcut sütunlar:", df.columns.tolist())
            return None

        # 2. Sayı Sütununu Bul
        # 'total' varsa onu kullan, yoksa hata
        if 'total' not in df.columns:
            # Belki hesaplamamız gerekir?
            numeric_cols = df.select_dtypes(include=['number']).columns
            # Yıl sütunlarını topla
            df['total'] = df[numeric_cols].sum(axis=1)

        # 3. Kategori Sütunu Var mı?
        if 'category' not in df.columns:
            st.error("❌ Veri setinde 'category' sütunu bulunamadı. Pivot işlemi yapılamaz.")
            return None

        # --- PIVOT İŞLEMİ ---
        # Amaç: Kategorileri sütun haline getirmek.
        # Satır: Bigram | Sütunlar: CS, Physics, Econ... | Değer: Total
        pivot_df = df.pivot_table(
            index=term_col, 
            columns='category', 
            values='total', 
            aggfunc='sum'
        ).fillna(0) # Boşluklara 0 yaz

        # Toplam büyüklüğü de bir sütun olarak ekle (Renk/Boyut için)
        pivot_df['Grand_Total'] = pivot_df.sum(axis=1)
        
        # İndeksi sütuna çevir (Grafik için lazım)
        pivot_df = pivot_df.reset_index()
        
        return pivot_df, term_col

    except Exception as e:
        st.error(f"❌ Veri işlenirken hata oluştu: {e}")
        return None

# ---------------------------------------------------------
# 2. GÖRSELLEŞTİRME ARAYÜZÜ
# ---------------------------------------------------------
data_result = load_and_pivot_data()

if data_result:
    pivot_df, term_name = data_result
    
    # Kategorileri al (Grand_Total ve bigram hariç)
    available_categories = [c for c in pivot_df.columns if c not in ['Grand_Total', term_name]]
    
    # SOL PANEL: KATEGORİ SEÇİMİ
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        selected_cats = st.multiselect(
            "Karşılaştırılacak Alanlar:",
            available_categories,
            default=available_categories[:3] if len(available_categories) >= 3 else available_categories
        )
        st.info("💡 Tavsiye: Karmaşayı önlemek için aynı anda en fazla 4-5 alan seçin.")

    # ORTA PANEL: GRAFİK
    if len(selected_cats) > 1:
        
        # Sadece seçilen kategorilerde verisi olan (hepsi 0 olmayan) kelimeleri al
        # Bu işlem grafiğin (0,0) noktasındaki yığılmayı azaltır
        mask = pivot_df[selected_cats].sum(axis=1) > 0
        filtered_df = pivot_df[mask]

        fig = px.scatter_matrix(
            filtered_df,
            dimensions=selected_cats,  # Seçilen kategoriler eksen olur
            color="Grand_Total",       # Renk, kelimenin genel popülaritesini gösterir
            hover_name=term_name,      # Üzerine gelince kelime yazar
            height=900,                # Grafik yüksekliği
            width=1000,
            opacity=0.6,               # Noktalar hafif şeffaf olsun ki yoğunluk görülsün
            color_continuous_scale="Viridis", # Renk paleti
            title=f"Scatterplot Matrix: {', '.join(selected_cats)}"
        )
        
        # Grafik Ayarları
        fig.update_traces(diagonal_visible=False) # Köşegenleri (Histogram) kapat, sade olsun
        fig.update_layout(dragmode='select')      # Seçim yapmaya izin ver
        
        st.plotly_chart(fig, use_container_width=True)
        
        # YORUM KILAVUZU
        st.success("""
        **Nasıl Okunmalı?**
        * **Köşegen (Diagonal) Çizgi:** Eğer noktalar X ve Y ekseninin ortasından geçen hayali bir çizgi üzerindeyse, o kelime **iki alanda da eşit popülerliktedir.**
        * **Eksene Yapışık Noktalar:** Noktalar bir kenara yapışıksa, o kelime sadece o alana özgüdür.
        * **Rengi Sarı/Parlak Olanlar:** Genel toplamda en çok kullanılan terimlerdir.
        """)
        
    else:
        st.warning("⚠️ Lütfen sol menüden veya yukarıdan **en az 2 kategori** seçin.")