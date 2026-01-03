import pandas as pd

# Giriş ve Çıkış
input_file = 'data/arxiv_cleaned_data.csv'
output_file = 'domain_yearly_stats.csv'

# Resimdeki klasör yapısına göre Eşleştirme Sözlüğü (Mapping)
# ArXiv kodlarını senin klasör isimlerine çeviriyoruz.
DOMAIN_MAP = {
    'cs': 'computer_science',
    'econ': 'economics',
    'eess': 'electrical_engineering',
    'q-fin': 'finance',
    'math': 'mathematics',
    'q-bio': 'quantitative_biology',
    'stat': 'statistics',
    # Fizik alt dalları çoktur, hepsini 'physics' çatısında topluyoruz
    'physics': 'physics', 'astro-ph': 'physics', 'cond-mat': 'physics', 
    'gr-qc': 'physics', 'hep-ex': 'physics', 'hep-lat': 'physics', 
    'hep-ph': 'physics', 'hep-th': 'physics', 'math-ph': 'physics', 
    'nucl-ex': 'physics', 'nucl-th': 'physics', 'quant-ph': 'physics', 
    'nlin': 'physics'
}

print("Veri işleniyor...")

# 1. Veriyi Oku
df = pd.read_csv(input_file, usecols=['id', 'published_date', 'all_categories'])

# 2. Tarihi Yıla Çevir
df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce', utc=True)
df = df.dropna(subset=['published_date'])
df['year'] = df['published_date'].dt.year.astype(int)

# 3. Kategorileri Ayır ve Eşleştir
# Önce boşluktan bölerek listeye çevir: "cs.AI stat.ML" -> ["cs.AI", "stat.ML"]
df['categories_list'] = df['all_categories'].str.split(' ')

# Listeyi satırlara patlat (Explode)
df_exploded = df.explode('categories_list')

# Kategori kodunun sadece başını al (cs.AI -> cs)
df_exploded['prefix'] = df_exploded['categories_list'].str.split('.').str[0]

# Prefix'i senin Domain ismine çevir (Mapping)
df_exploded['domain'] = df_exploded['prefix'].map(DOMAIN_MAP)

# Mapping'de olmayanları (varsa) temizle
df_exploded = df_exploded.dropna(subset=['domain'])

# 4. TEKRARLARI ÖNLEME (Önemli!)
# Bir makale hem 'cs.AI' hem 'cs.LG' ise 'computer_science' altında 2 kere sayılmamalı.
# Bu yüzden aynı makaleID ve aynı Domain ikilisini teke düşürüyoruz.
df_unique_domains = df_exploded.drop_duplicates(subset=['id', 'domain'])

# 5. PIVOT TABLO OLUŞTUR
pivot_df = df_unique_domains.pivot_table(
    index='domain', 
    columns='year', 
    values='id', 
    aggfunc='count', 
    fill_value=0
)

# 6. Toplam Sayıya Göre Sırala
pivot_df['Total'] = pivot_df.sum(axis=1)
pivot_df = pivot_df.sort_values(by='Total', ascending=False)
pivot_df = pivot_df.drop(columns=['Total'])

# Kaydet
pivot_df.to_csv(output_file)

print(f"\n✅ İşlem tamamlandı! Dosya: {output_file}")
print("\n--- Son 5 Yılın Özeti ---")
print(pivot_df[pivot_df.columns[-5:]])