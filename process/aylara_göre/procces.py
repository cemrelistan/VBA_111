import pandas as pd
import re # Normal ifadeler (Regular Expressions) için
import nltk # Doğal Dil İşleme Kütüphanesi
from nltk.corpus import stopwords # Etkisiz kelimeler listesi için
from nltk.tokenize import word_tokenize 
from sklearn.feature_extraction.text import CountVectorizer
from collections import Counter 
import json

# --- Config dosyasını oku ---
with open('config.json', 'r') as f:
    config = json.load(f)
    economy_config = config['Economy']

# --- Veri Yükleme (Kullanıcının kodu) ---
df = pd.read_csv(economy_config['data_file'])

# --- NLTK Modüllerini Yükleme (Kullanıcının kodu) ---
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("NLTK 'stopwords' modülü indiriliyor...")
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("NLTK 'punkt' modülü indiriliyor...")
    nltk.download('punkt')


# 1. Başlık ve Özeti Birleştir (Kullanıcının kodu)
df['text'] = df['title'] + ' ' + df['summary']

# 2. Temel Temizleme Fonksiyonu (Kullanıcının kodu)
def basic_clean(text):
    text = str(text).lower() # str() ekleyerek olası float hatalarını önle
    text = re.sub(r'[^a-z\s]', '', text) # Sadece harfleri ve boşlukları koru
    text = re.sub(r'\s+', ' ', text).strip() # Fazladan boşlukları kaldır
    return text

df['basic_processed'] = df['text'].apply(basic_clean)

# 4. Stopword Listelerini Tanımlama (Kullanıcının kodu)
stop_words_en = set(stopwords.words('english'))
academic_stopwords = set(economy_config['academic_stopwords'])

final_stop_words = stop_words_en.union(academic_stopwords)
print(f"\nToplam {len(final_stop_words)} adet etkisiz kelime (stopword) tanımlandı.")


# 5. Tam Kapsamlı Ön İşleme Fonksiyonu (Kullanıcının kodu)
def full_preprocess(text, stop_words_set):
    text = basic_clean(text)
    tokens = word_tokenize(text)
    filtered_tokens = [
        word for word in tokens 
        if word not in stop_words_set and len(word) > 2
    ]
    return ' '.join(filtered_tokens)

# 6. Metin Sütunlarını Oluşturma
print("Metinler temizleniyor (stopword'ler kaldırılıyor)...")
# 'gürültüsüz_metin': Sadece standart stopword'ler çıkarılır. (N-gram analizi için ideal)
df['gürültülü_metin'] = df['text'].apply(lambda x: full_preprocess(x, stop_words_en))
# 'processed_text': Hem standart hem akademik stopword'ler çıkarılır. (Tekil kelime analizi için)
df['processed_text'] = df['text'].apply(lambda x: full_preprocess(x, final_stop_words))

# 'published_date' sütununu datetime formatına çevir ve 'year' sütunu oluştur
df['published_date'] = pd.to_datetime(df['published_date'])
df['year'] = df['published_date'].dt.year

# Yıllara göre n-gram frekanslarını saklamak için bir sözlük
yearly_ngram_counts = {}
all_ngrams = set()

# Her bir yıl için n-gram analizi yap
for year in sorted(df['year'].unique()):
    # O yıla ait metinleri seç
    corpus_year = df[df['year'] == year]['gürültülü_metin'].dropna()
    
    if corpus_year.empty:
        continue
        
    # CountVectorizer ile n-gram'ları say
    vectorizer_ngram = CountVectorizer(ngram_range=(2, 5))
    X_ngram = vectorizer_ngram.fit_transform(corpus_year)
    
    # Frekansı 1'den büyük olanları al
    sum_words = X_ngram.sum(axis=0)
    words_freq = {
        word: sum_words[0, idx] 
        for word, idx in vectorizer_ngram.vocabulary_.items() 
        if sum_words[0, idx] > 1
    }
    
    # Yılın sonuçlarını ve bulunan tüm n-gram'ları kaydet
    yearly_ngram_counts[year] = words_freq
    all_ngrams.update(words_freq.keys())

# Sonuçları birleştirmek için bir DataFrame oluştur
ngram_yearly_df = pd.DataFrame(index=sorted(list(all_ngrams)))

# Her yıl için sütun ekle
for year, counts in sorted(yearly_ngram_counts.items()):
    ngram_yearly_df[year] = ngram_yearly_df.index.map(counts).fillna(0).astype(int)

# Toplam frekans sütunu ekle
ngram_yearly_df['Total'] = ngram_yearly_df.sum(axis=1)

# Toplama göre sırala
ngram_yearly_df = ngram_yearly_df.sort_values(by='Total', ascending=False)

# Sonuçları CSV'ye kaydet
ngram_yearly_df.to_csv("ngram_yillik_sayilari.csv", index_label='N-Gram')
print("Yıllık n-gram sayıları 'ngram_yillik_sayilari.csv' dosyasına kaydedildi.")


# -----------------------------------------------------------------------------------
# ADIM 8: YILLIK TEKİL KELİME FREKANS ANALİZİ
# -----------------------------------------------------------------------------------
print("\n--- Yıllık Tekil Kelime Frekans Analizi Yapılıyor... ---")

# Yıllara göre kelime frekanslarını saklamak için bir sözlük
yearly_word_counts = {}
all_words = set()

# Her bir yıl için kelime sayımı yap
for year in sorted(df['year'].unique()):
    # O yıla ait metinleri birleştir
    corpus_year = ' '.join(df[df['year'] == year]['processed_text'].dropna())
    
    if not corpus_year:
        continue
        
    # Kelimeleri say
    word_counts = Counter(corpus_year.split())
    
    # Yılın sonuçlarını ve bulunan tüm kelimeleri kaydet
    yearly_word_counts[year] = word_counts
    all_words.update(word_counts.keys())

# Sonuçları birleştirmek için bir DataFrame oluştur
word_yearly_df = pd.DataFrame(index=sorted(list(all_words)))

# Her yıl için sütun ekle
for year, counts in sorted(yearly_word_counts.items()):
    word_yearly_df[year] = word_yearly_df.index.map(counts).fillna(0).astype(int)

# Toplam frekans sütunu ekle
word_yearly_df['Total'] = word_yearly_df.sum(axis=1)

# Sadece toplamda 1'den fazla geçen kelimeleri tut
word_yearly_df = word_yearly_df[word_yearly_df['Total'] > 1]

# Toplama göre sırala
word_yearly_df = word_yearly_df.sort_values(by='Total', ascending=False)

# Sonuçları CSV'ye kaydet
word_yearly_df.to_csv("common_words_yillik.csv", index_label='Kelime')
print("Yıllık tekil kelime sayıları 'common_words_yillik.csv' dosyasına kaydedildi.")