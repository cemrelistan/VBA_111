import csv
import os
from tqdm import tqdm

# Giriş dosyası (Senin temizlediğin dosya)
input_file = 'data/arxiv_cleaned_data.csv'

# Çıktı klasörü (Dosyalar buraya kaydedilecek)
output_dir = 'arxiv_domain_data'
os.makedirs(output_dir, exist_ok=True)

# --- 1. Kategori Gruplama Ayarları (Mapping) ---
# ArXiv'deki kodları senin anlayacağın dosya isimlerine eşliyoruz.
# Buraya ekleme çıkarma yapabilirsin.
DOMAIN_MAP = {
    # Bilgisayar Bilimi
    'cs': 'computer_science',
    
    # Ekonomi & Finans
    'econ': 'economics',
    'q-fin': 'finance',
    
    # İstatistik & Matematik
    'stat': 'statistics',
    'math': 'mathematics',
    
    # Mühendislik
    'eess': 'electrical_engineering',
    
    # Biyoloji
    'q-bio': 'quantitative_biology',
    
    # Fizik (ArXiv'de fizik çok parçalıdır, hepsini 'physics' altında topladım)
    # Eğer ayrı olsun istersen bunları ayrı ayrı tanımlayabilirsin.
    'physics': 'physics',
    'astro-ph': 'physics',
    'cond-mat': 'physics',
    'gr-qc': 'physics',
    'hep-ex': 'physics',
    'hep-lat': 'physics',
    'hep-ph': 'physics',
    'hep-th': 'physics',
    'math-ph': 'physics',
    'nucl-ex': 'physics',
    'nucl-th': 'physics',
    'quant-ph': 'physics',
    'nlin': 'physics' # Nonlinear Sciences genelde fizikle ilişkilidir
}

def get_target_files(categories_str):
    """
    Bir makalenin kategorilerine bakarak hangi dosyalara yazılacağını belirler.
    Geriye dosya isimlerinin (domainlerin) listesini döndürür.
    """
    if not categories_str:
        return []
    
    targets = set()
    # Kategoriler boşlukla ayrılmıştır: "cs.AI stat.ML"
    cats = categories_str.split(' ')
    
    for cat in cats:
        # Ana prefix'i al (cs.AI -> cs, hep-ph -> hep-ph)
        prefix = cat.split('.')[0]
        
        # Mapping tablosundan hangi dosyaya gideceğini bul
        if prefix in DOMAIN_MAP:
            targets.add(DOMAIN_MAP[prefix])
        else:
            # Listede olmayan (nadir) kategoriler için 'other' diyebiliriz
            # veya prefix ismiyle kaydedebiliriz.
            pass 
            
    return list(targets)

# --- 2. İşlem Başlıyor ---

print("Dosya ayrıştırma işlemi başlıyor...")

# Dosya yazıcılarını (Writers) dinamik olarak açacağız
file_handles = {} # { 'economics': file_object }
csv_writers = {}  # { 'economics': csv_writer }

try:
    with open(input_file, 'r', encoding='utf-8') as f_in:
        reader = csv.reader(f_in)
        header = next(reader) # Başlığı oku
        
        # tqdm ile ilerleme çubuğu
        for row in tqdm(reader, desc="Ayrıştırılıyor"):
            
            # row[6] -> 'all_categories' sütunu (Scriptindeki sıraya göre değişebilir, kontrol et!)
            # Eğer temizleme kodunda son sütuna koyduysan index -1'dir.
            categories_str = row[-1] 
            
            target_domains = get_target_files(categories_str)
            
            for domain in target_domains:
                # Eğer bu domain için dosya henüz açılmadıysa aç
                if domain not in file_handles:
                    path = os.path.join(output_dir, f"arxiv_{domain}.csv")
                    f_out = open(path, 'w', encoding='utf-8', newline='')
                    writer = csv.writer(f_out)
                    writer.writerow(header) # Başlığı yaz
                    
                    file_handles[domain] = f_out
                    csv_writers[domain] = writer
                
                # İlgili dosyaya satırı yaz
                csv_writers[domain].writerow(row)

finally:
    # Açık olan tüm dosyaları kapat
    print("\nDosyalar kapatılıyor...")
    for f in file_handles.values():
        f.close()

print(f"İşlem tamam! Dosyalar '{output_dir}' klasöründe.")