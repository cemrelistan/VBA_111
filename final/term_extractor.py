import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
import os
import glob
from tqdm import tqdm

# --- Gerekli NLTK verilerini indir (Sadece ilk seferde çalışır) ---
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# --- AYARLAR ---
INPUT_FOLDER = 'arxiv_domain_data'   # CSV'lerin olduğu klasör
OUTPUT_MAIN_FOLDER = 'analysis_results' # Sonuçların gideceği ana klasör

# Akademik Stopwords (Her alanda geçen gereksiz kelimeler)
ACADEMIC_STOPWORDS = {
    'paper', 'study', 'result', 'method', 'using', 'proposed', 'based', 
    'analysis', 'data', 'model', 'approach', 'results', 'show', 'new', 
    'system', 'used', 'performance', 'however', 'also', 'propose', 
    'algorithm', 'problem', 'time', 'two', 'one', 'different'
}

# Standart İngilizce Stopwords
stop_words_en = set(stopwords.words('english'))
# Genişletilmiş Stopwords (Tekil kelime analizi için daha katı filtre)
extended_stop_words = stop_words_en.union(ACADEMIC_STOPWORDS)

# ---------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------

def clean_text(text):
    """Temel temizlik: Küçük harf, sadece harfler, fazla boşlukları sil."""
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text) # Sadece a-z ve boşluk kalsın
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def preprocess_for_ngrams(text):
    """N-Gram (Öbek) analizi için hafif temizlik (stopword'ler kalabilir veya standart atılır)"""
    # N-gramlarda "of", "the" gibi kelimeler bazen yapıyı tutar (örn: "state of the art")
    # Ancak biz temiz terim istiyorsak standartları atalım.
    words = text.split()
    filtered = [w for w in words if w not in stop_words_en and len(w) > 2]
    return " ".join(filtered)

def preprocess_for_unigrams(text):
    """Tekil kelime analizi için katı temizlik (akademik kelimeler de atılır)"""
    words = text.split()
    filtered = [w for w in words if w not in extended_stop_words and len(w) > 2]
    return " ".join(filtered)

def analyze_yearly_trends(df, text_column, ngram_range=(1,1), min_freq=2):
    """
    Belirtilen metin sütununu yıllara göre analiz eder.
    Geriye index'i terimler, sütunları yıllar olan bir DataFrame döner.
    """
    yearly_counts = {}
    all_terms = set()
    
    # Yılları sırala
    years = sorted(df['year'].unique())
    
    for year in years:
        # O yıla ait metinleri al
        corpus = df[df['year'] == year][text_column].dropna()
        
        if len(corpus) < 5: # Çok az makale varsa atla
            continue
            
        try:
            # CountVectorizer çok hızlıdır
            vectorizer = CountVectorizer(ngram_range=ngram_range, min_df=min_freq)
            X = vectorizer.fit_transform(corpus)
            
            # Kelime frekanslarını topla
            sum_words = X.sum(axis=0)
            words_freq = {word: sum_words[0, idx] for word, idx in vectorizer.vocabulary_.items()}
            
            yearly_counts[year] = words_freq
            all_terms.update(words_freq.keys())
            
        except ValueError:
            # "Empty vocabulary" hatası alırsak (hiç kelime kalmadıysa) devam et
            continue

    # Sonuç tablosunu oluştur
    result_df = pd.DataFrame(index=sorted(list(all_terms)))
    
    for year in years:
        if year in yearly_counts:
            result_df[year] = result_df.index.map(yearly_counts[year]).fillna(0).astype(int)
        else:
            result_df[year] = 0
            
    # Toplam sütunu ekle ve sırala
    result_df['Total'] = result_df.sum(axis=1)
    result_df = result_df.sort_values(by='Total', ascending=False)
    
    return result_df

# ---------------------------------------------------------
# ANA İŞLEM DÖNGÜSÜ
# ---------------------------------------------------------

def main():
    # Çıktı klasörünü oluştur
    if not os.path.exists(OUTPUT_MAIN_FOLDER):
        os.makedirs(OUTPUT_MAIN_FOLDER)
    
    # Tüm kategori dosyalarını bul
    csv_files = glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))
    
    print(f"Toplam {len(csv_files)} kategori dosyası bulundu. Analiz başlıyor...\n")
    
    for file_path in tqdm(csv_files, desc="Kategoriler İşleniyor"):
        # Dosya adından kategori ismini çıkar (örn: arxiv_economics.csv -> economics)
        filename = os.path.basename(file_path)
        category_name = filename.replace('arxiv_', '').replace('.csv', '')
        
        # Bu kategori için özel klasör oluştur
        category_out_dir = os.path.join(OUTPUT_MAIN_FOLDER, category_name)
        if not os.path.exists(category_out_dir):
            os.makedirs(category_out_dir)
            
        # 1. Veriyi Oku
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Hata: {filename} okunamadı. {e}")
            continue
            
        if df.empty:
            continue

        # 2. Ön İşleme (Tarih ve Metin Birleştirme)
        df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')
        df = df.dropna(subset=['published_date']) # Tarihi olmayanları at
        df['year'] = df['published_date'].dt.year
        
        # Başlık ve Özeti Birleştirip Temizle
        df['text_raw'] = df['title'].fillna('') + ' ' + df['summary'].fillna('')
        df['text_clean'] = df['text_raw'].apply(clean_text)
        
        # A) Tekil Kelimeler (Unigrams) için Hazırlık
        # (Daha sıkı stopword filtresi uygulanır)
        df['text_unigrams'] = df['text_clean'].apply(preprocess_for_unigrams)
        
        # B) Terim Öbekleri (N-grams: Machine Learning, Interest Rate vb.) için Hazırlık
        # (Sadece standart stopword'ler atılır, yapı bozulmasın diye)
        df['text_ngrams'] = df['text_clean'].apply(preprocess_for_ngrams)
        
        # 3. Analizleri Çalıştır ve Kaydet
        
        # --- Analiz 1: Tekil Kelimeler (Keywords) ---
        # Örn: "inflation", "blockchain", "virus"
        df_uni = analyze_yearly_trends(df, 'text_unigrams', ngram_range=(1, 1), min_freq=5)
        df_uni.head(1000).to_csv(os.path.join(category_out_dir, "keywords_yearly.csv"))
        
        # --- Analiz 2: İkili Terimler (Bigrams) ---
        # Örn: "machine learning", "monetary policy", "supply chain"
        df_bi = analyze_yearly_trends(df, 'text_ngrams', ngram_range=(2, 2), min_freq=3)
        df_bi.head(1000).to_csv(os.path.join(category_out_dir, "bigrams_yearly.csv"))
        
        # --- Analiz 3: Üçlü Terimler (Trigrams) ---
        # Örn: "deep neural network", "stochastic differential equations"
        df_tri = analyze_yearly_trends(df, 'text_ngrams', ngram_range=(3, 3), min_freq=3)
        df_tri.head(1000).to_csv(os.path.join(category_out_dir, "trigrams_yearly.csv"))

    print(f"\n✅ Tüm işlemler tamamlandı! Sonuçlar '{OUTPUT_MAIN_FOLDER}' klasöründe.")

if __name__ == "__main__":
    main()