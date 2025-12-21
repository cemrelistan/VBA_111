import pandas as pd
import re # Normal ifadeler (Regular Expressions) için
import nltk # Doğal Dil İşleme Kütüphanesi
from nltk.corpus import stopwords # Etkisiz kelimeler listesi için
from nltk.tokenize import word_tokenize # Metni kelimelere ayırmak için
from sklearn.feature_extraction.text import CountVectorizer # Kelime sayımı için
from collections import Counter # Sayma işlemleri için

# --- Veri Yükleme (Kullanıcının kodu) ---
df = pd.read_csv("arxiv_econ_articles.csv")

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


# 3. Stopword'süz Ham Frekans Analizi (Kullanıcının kodu)
print("\n--- Stopword'ler Temizlenmeden Önceki Durum ---")
all_words_raw = ' '.join(df['basic_processed']).split()
word_counts_raw = Counter(all_words_raw)
print("En sık kullanılan 20 kelime (gürültülü):")
print(word_counts_raw.most_common(20))


# 4. Stopword Listelerini Tanımlama (Kullanıcının kodu)
stop_words_en = set(stopwords.words('english'))
academic_stopwords = set([
    'paper', 'research', 'study', 'studies', 'analysis', 'analyze',
    'model', 'models', 'modeling', 'data', 'dataset', 'datasets',
    'results', 'result', 'method', 'methods', 'approach',
    'we', 'us', 'our', 'propose', 'present', 'show', 'shows',
    'find', 'findings', 'investigate', 'examine', 'using', 'based',
    'also', 'however', 'furthermore', 'moreover', 'abstract',
    'introduction', 'conclusion', 'section', 'figure', 'table',
    'economic', 'economics', 'financial', 'finance'
])
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

df['processed_text'] = df['text'].apply(lambda x: full_preprocess(x, final_stop_words))

print("\n--- Adım 7: Otomatik N-Gram (2-5 Gram) Frekans Analizi ---")

vectorizer_ngram = CountVectorizer(ngram_range=(2, 5)) # 2, 3, 4 ve 5-gram'ları ara

X_ngram = vectorizer_ngram.fit_transform(df['gürültüsüz_metin'].dropna())

sum_words = X_ngram.sum(axis=0)
words_freq = [(word, sum_words[0, idx]) for word, idx in vectorizer_ngram.vocabulary_.items() if sum_words[0, idx] > 1]
words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)

# Sonuçları bir DataFrame'e dönüştür
ngram_freq_df = pd.DataFrame(words_freq, columns=['N-Gram', 'Frekans'])

# Sonuçları yeni bir CSV'ye kaydet

all_words_clean = ' '.join(df['processed_text']).split()
word_counts_clean = Counter(all_words_clean)

counter_data = pd.DataFrame(word_counts_clean.most_common(), columns=['Kelime', 'Frekans'])


# Sadece işlenmiş veriyi yeni bir CSV'ye kaydet
counter_data.to_csv("common_words.csv", index=False)
ngram_freq_df.to_csv("otomatik_ngram_sayilari.csv", index=False)
print("İşlenmiş metinler 'arxiv_econ_articles_processed.csv' dosyasına kaydedildi.")