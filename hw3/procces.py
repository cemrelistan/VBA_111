import pandas as pd
import re
import json
import sys # Hata durumunda çıkmak için

# --- Config dosyasını oku ---
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        economy_config = config['Economy']
except FileNotFoundError:
    print("HATA: config.json dosyası bulunamadı. Lütfen dosyanın mevcut olduğundan emin olun.")
    sys.exit(1)
except KeyError:
    print("HATA: config.json 'Economy' anahtarını içermiyor.")
    sys.exit(1)

try:
    df = pd.read_csv(economy_config['data_file'])
    print(f"'{economy_config['data_file']}' dosyasından {len(df)} makale yüklendi.")
except FileNotFoundError:
    print(f"HATA: '{economy_config['data_file']}' veritabanı dosyası bulunamadı.")
    sys.exit(1)

def basic_clean(text):
    text = str(text).lower() # str() ekleyerek olası float hatalarını önle
    text = re.sub(r'[^a-z\s]', '', text) # Sadece harfleri ve boşlukları koru
    text = re.sub(r'\s+', ' ', text).strip() # Fazladan boşlukları kaldır
    return text

SEARCH_TERMS = [
    "machine learning",
    "artificial intelligence",
    "large language",
    "climate change",
    "renewable energy",
    "electric vehicle",
    "electric vehicles",
    "covid pandemic",
    "social distancing",
    "public health"
]

# 2. Gerekli Sütunları Hazırla (tek seferlik)
print("Metinler temizleniyor ve tarihler ayarlanıyor...")

# Başlık ve özeti birleştir
df['text'] = df['title'].astype(str) + ' ' + df['summary'].astype(str)

# 'basic_clean' fonksiyonunu uygula
df['basic_processed'] = df['text'].apply(basic_clean)

df['published_date'] = pd.to_datetime(df['published_date'])

df['period'] = df['published_date'].dt.to_period('Q')

# 3. Her terim için say ve CSV oluştur
print("\n--- Terimler için çeyreklik sayım başlıyor ---")
for term in SEARCH_TERMS:
    # Temrin basic_clean ile aynı şekilde işlenmiş halini kullan
    term_clean = basic_clean(term)
    print(f"\nAranacak Terim: '{term}' (temizlenmiş: '{term_clean}')")

    # Her döngüde 'term_count' sütununu yeniden oluştur
    df['term_count'] = df['basic_processed'].apply(lambda x: x.count(term_clean))

    # Çeyreklik olarak grupla ve topla
    quarterly_counts = df.groupby('period')['term_count'].sum()

    # Sonuçları göster (kısa özet)
    print(f"'{term}' Teriminin Çeyreklik Geçiş Sayısı (ilk 10):")
    print(quarterly_counts.head(10))

    # Sonucu CSV'ye kaydet
    output_csv_name = f"data/{term_clean.replace(' ', '_')}_quarterly_counts.csv"
    quarterly_counts.to_csv(output_csv_name, header=['count'])
    print(f"Sonuçlar '{output_csv_name}' dosyasına kaydedildi.")

print("\n--- Tüm terimler işlendi ---")