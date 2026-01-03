import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os

# ---------------------------------------------------------
# 1. VERİYİ YÜKLEME VE BİRLEŞTİRME FONKSİYONU
# ---------------------------------------------------------
def get_aggregated_frequencies(file_path="all_data_merged.csv"):
    if not os.path.exists(file_path):
        print(f"'{file_path}' dosyası bulunamadı!")
        return None

    try:
        df = pd.read_csv(file_path)
        
        # Sütun isimlerini temizle (küçük harf, boşluksuz)
        df.columns = [str(c).lower().strip() for c in df.columns]

        # --- A. KELİME SÜTUNUNU BUL ---
        possible_names = ['bigram', 'term', 'keyword', 'word', 'ngram', 'unnamed: 0']
        term_col = None
        for name in possible_names:
            if name in df.columns:
                term_col = name
                break
        
        if not term_col:
            print("Veri setinde kelime sütunu (bigram/term) bulunamadı.")
            return None

        # --- B. SAYI SÜTUNUNU BUL ---
        count_col = 'total' if 'total' in df.columns else 'count'
        
        if count_col not in df.columns:
            numeric_cols = df.select_dtypes(include=['number']).columns
            df['calculated_total'] = df[numeric_cols].sum(axis=1)
            count_col = 'calculated_total'

        # --- C. AGGREGATION (BİRLEŞTİRME) ---
        aggregated_df = df.groupby(term_col)[count_col].sum().reset_index()
        frequencies = dict(zip(aggregated_df[term_col], aggregated_df[count_col]))
        
        return frequencies

    except Exception as e:
        print(f"Veri işlenirken hata oluştu: {e}")
        return None

# ---------------------------------------------------------
# 2. GÖRSELLEŞTİRME
# ---------------------------------------------------------
if __name__ == "__main__":
    freq_data = get_aggregated_frequencies("data/all_data_merged.csv")

    if freq_data and len(freq_data) > 0:
        # --- WORD CLOUD AYARLARI ---
        wc = WordCloud(
            width=800, 
            height=500,
            background_color="white", 
            colormap="tab10",
            max_words=150,
            contour_width=0,
            prefer_horizontal=0.9,
            relative_scaling=0.5
        )
        
        # Veriden bulutu oluştur
        wc.generate_from_frequencies(freq_data)
        
        # Matplotlib ile çiz
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title("Word Cloud", fontsize=14)
        
        plt.tight_layout()
        plt.savefig("wordcloud_output.png", dpi=150, bbox_inches='tight')
        plt.show()
        
        print("Grafik 'wordcloud_output.png' olarak kaydedildi.")
    else:
        print("Veri yüklenemedi. Lütfen 'all_data_merged.csv' dosyasını kontrol edin.")