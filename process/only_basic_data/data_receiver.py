import arxiv
import pandas as pd

# arXiv API'si için bir istemci (client) oluştur
client = arxiv.Client()

# Arama kriterlerini belirle
# Burada 'cat:econ.*' sorgusu, arXiv'in 'Economics' kategorisindeki
# (Genel Ekonomi, Ekonometri vb. alt dallar dahil) tüm makaleleri hedefler.
# 'q=Machine Learning' gibi eklemelerle konuyu daha da daraltabiliriz.
# Şimdilik en son 100 ekonomi makalesini çekelim.
search = arxiv.Search(
    query = "cat:econ.*", # Kategori: Ekonomi
    max_results = 100, # Sonuç sayısı (demo için 100, daha sonra artırılabilir)
    sort_by = arxiv.SortCriterion.SubmittedDate # En yeniye göre sırala
)

# Sonuçları almak için istemciyi kullan
results = client.results(search)

# Verileri yapılandırılmış bir listeye aktaralım
article_list = []
print("Veriler çekiliyor...")

for r in results:
    article_list.append({
        'id': r.entry_id,
        'title': r.title,
        'published_date': r.published, # Bu tam istediğimiz tarih verisi
        'authors': [a.name for a in r.authors],
        'primary_category': r.primary_category,
        'summary': r.summary
    })

# Veriyi bir Pandas DataFrame'e dönüştür (analiz için en ideal format)
df = pd.DataFrame(article_list)

# DataFrame'in yapısını ve ilk birkaç satırı kontrol et
print(f"Toplam {len(df)} makale başarıyla çekildi.")
print("\n--- İlk 5 Makale Verisi ---")
print(df.head())

# Tarih verisinin formatını gör
print("\n--- Veri Tipleri ---")
df.info()

# İsteğe bağlı: Veriyi ileride kullanmak üzere CSV olarak kaydet
df.to_csv("arxiv_econ_articles.csv", index=False)
print("\nVeriler 'arxiv_econ_articles.csv' dosyasına kaydedildi.")