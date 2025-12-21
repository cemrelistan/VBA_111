import arxiv
import pandas as pd
import time # API'ye saygılı olmak için bekleme ekliyoruz
from datetime import datetime # Geçerli yılı otomatil almak için

# ----------------------------------------------------------------
# Yıllık sorgu için parametreleri belirle
# ----------------------------------------------------------------
# Hangi yılları istiyoruz? (Örn: Son 5 yıl)
current_year = datetime.now().year 
# (Context: 2025 yılındayız, 2021-2025 arası 5 yıllık bir trend iyidir)
YILLAR = list(range(2020, 2026)) # [2021, 2022, 2023, 2024, 2025]
MAKS_SONUC_PER_YIL = 100 # Her yıl için 100 makale
KATEGORI = "cat:econ.*" # Ekonomi kategorisi

print(f"Hedeflenen Yıllar: {YILLAR}")
print(f"Yıl Başına Makale: {MAKS_SONUC_PER_YIL}")
print(f"Kategori: {KATEGORI}")

# arXiv API'si için bir istemci (client) oluştur
client = arxiv.Client()

# Tüm yıllardan gelen makaleleri toplayacağımız ana liste
tum_makaleler_listesi = []

# ----------------------------------------------------------------
# Yıllar boyunca döngüye gir ve verileri çek
# ----------------------------------------------------------------
for year in YILLAR:
    print(f"\n--- {year} yılı için veriler çekiliyor... ---")
    
    # Yılın başlangıç ve bitiş tarihlerini formatla (YYYYMMDDHHMM)
    start_date = f"{year}01010000" # Yılın ilk günü, 00:00
    end_date = f"{year}12312359" # Yılın son günü, 23:59
    
    # arXiv sorgusunu oluştur: Kategori VE Tarih Aralığı
    query_string = f"{KATEGORI} AND submittedDate:[{start_date} TO {end_date}]"
    
    # Arama kriterlerini belirle
    search = arxiv.Search(
        query = query_string,
        max_results = MAKS_SONUC_PER_YIL,
        sort_by = arxiv.SortCriterion.SubmittedDate # Yılın en son gönderilen 100 makalesi
    )

    # Sonuçları almak için istemciyi kullan
    results = client.results(search)

    # Gelen sonuçları ana listeye ekle
    count_this_year = 0
    for r in results:
        tum_makaleler_listesi.append({
            'id': r.entry_id,
            'title': r.title,
            'published_date': r.published, # Bu tam istediğimiz tarih verisi
            'authors': [a.name for a in r.authors],
            'primary_category': r.primary_category,
            'summary': r.summary
        })
        count_this_year += 1

    print(f"-> {year} yılından {count_this_year} adet makale eklendi.")
    
    # API'ye saygı: Her sorgu arasında 3 saniye bekle
    # (Çok hızlı sorgu yaparsak IP adresimiz geçici olarak engellenebilir)
    print("API sorgu limiti için 3 saniye bekleniyor...")
    time.sleep(3)

# ----------------------------------------------------------------
# Tüm verileri tek bir DataFrame'e dönüştür
# ----------------------------------------------------------------
print("\n--- Tüm veriler DataFrame'e dönüştürülüyor... ---")
df = pd.DataFrame(tum_makaleler_listesi)

# DataFrame'in yapısını ve ilk birkaç satırı kontrol et
print(f"Toplam {len(df)} makale başarıyla çekildi.")

# Doğrulama: Yıllara göre dağılımı kontrol edelim
if not df.empty:
    # 'published_date' sütununu datetime objesine çevir
    df['published_date'] = pd.to_datetime(df['published_date'])
    # 'year' adında yeni bir sütun oluştur
    df['year'] = df['published_date'].dt.year
    print("\nÇekilen verilerin yıllara göre dağılımı:")
    print(df['year'].value_counts().sort_index())
else:
    print("Hiç makale bulunamadı.")


print("\n--- İlk 5 Makale Verisi (Genel) ---")
print(df.head())

# Tarih verisinin formatını gör
print("\n--- Veri Tipleri ---")
df.info()

# İsteğe bağlı: Veriyi ileride kullanmak üzere CSV olarak kaydet
# Dosya adını 'YILLIK' olarak değiştirdim ki eski dosyanızın üzerine yazmasın
output_filename = "arxiv_econ_articles_YILLIK.csv"
df.to_csv(output_filename, index=False)
print(f"\nTüm veriler '{output_filename}' dosyasına kaydedildi.")