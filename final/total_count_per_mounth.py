import pandas as pd

# Giriş ve Çıkış dosyaları
input_file = 'data/arxiv_cleaned_data.csv'
output_file = 'monthly_article_counts.csv'

print("Veri okunuyor...")

# Sadece tarih sütununu okuyoruz
df = pd.read_csv(input_file, usecols=['published_date'])

# Tarihi datetime formatına çevir (UTC=True, saat dilimi karmaşasını önler)
df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce', utc=True)

# Hatalı tarihleri temizle
df = df.dropna(subset=['published_date'])

# Tarihi indeks yap (Resample/Zaman serisi işlemi için şarttır)
df.set_index('published_date', inplace=True)

# Aylık bazda (MS: Month Start) örnekle ve say
# Eğer 'ME' (Month End) istersen ayın son gününü yazar.
monthly_counts = df.resample('MS').size()

# DataFrame'e çevir ve formatla
result_df = pd.DataFrame({
    'date': monthly_counts.index.strftime('%Y-%m'), # YYYY-AA formatı
    'count': monthly_counts.values
})

# CSV olarak kaydet
result_df.to_csv(output_file, index=False)

print(f"\nİşlem tamamlandı! Sonuç dosyası: {output_file}")
print(f"Toplam Ay Sayısı: {len(result_df)}")
print("\nSon 5 ayın verisi:")
print(result_df.tail())