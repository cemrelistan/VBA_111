import json
import csv
from tqdm import tqdm # İlerleme çubuğu için

# Dosya isimleri
input_file = 'data/arxiv-metadata-oai-snapshot.json'
output_file = 'data/arxiv_cleaned_data.csv'

def format_authors(authors_parsed):
    """
    JSON'daki [['Soyad', 'Ad', ''], ...] yapısını 
    ['Ad Soyad', ...] listesine çevirir.
    """
    author_list = []
    for author in authors_parsed:
        # author[1] = Ad, author[0] = Soyad
        full_name = f"{author[1]} {author[0]}".strip()
        author_list.append(full_name)
    return str(author_list) # CSV'ye string olarak liste formatında yazar

def clean_text(text):
    """
    Metindeki satır sonlarını (enter) boşlukla değiştirir.
    CSV formatının bozulmaması için önemlidir.
    """
    if text:
        return text.replace('\n', ' ').strip()
    return ""

# CSV Başlıkları
headers = [
    'id', 
    'title', 
    'summary', 
    'published_date', 
    'authors', 
    'primary_category', 
    'all_categories' # Ekstra istediğin tüm kategoriler
]

print("Dönüştürme işlemi başlıyor... Bu işlem dosya boyutuna göre birkaç dakika sürebilir.")

# Dosyaları açıyoruz
with open(input_file, 'r', encoding='utf-8') as f_in, \
     open(output_file, 'w', encoding='utf-8', newline='') as f_out:
    
    writer = csv.writer(f_out)
    writer.writerow(headers) # Başlığı yaz
    
    # tqdm ile dosya satırlarını sarmalayarak ilerleme çubuğu gösteriyoruz
    # total=2400000 yaklaşık makale sayısıdır, sadece görsel tahmin içindir.
    for line in tqdm(f_in, total=2400000, desc="İşleniyor"):
        try:
            paper = json.loads(line)
            
            # --- 1. ID ve URL Oluşturma ---
            paper_id = paper.get('id', '')
            # Örnekteki gibi v1 ekleyerek tam link oluşturuyoruz
            arxiv_url = f"http://arxiv.org/abs/{paper_id}v1"
            
            # --- 2. Tarih (İlk versiyon tarihi) ---
            # published_date genellikle versions listesinin ilk elemanıdır
            versions = paper.get('versions', [])
            pub_date = versions[0]['created'] if versions else paper.get('update_date')
            
            # --- 3. Kategoriler ---
            # categories string'i boşlukla ayrılmıştır: "hep-ph astro-ph"
            cats_str = paper.get('categories', '')
            cats_list = cats_str.split(' ')
            primary_cat = cats_list[0] if cats_list else ''
            
            # --- 4. Yazarlar ---
            authors_formatted = format_authors(paper.get('authors_parsed', []))
            
            # --- 5. Başlık ve Özet Temizliği ---
            title_clean = clean_text(paper.get('title', ''))
            summary_clean = clean_text(paper.get('abstract', ''))
            
            # Satırı CSV'ye yaz
            writer.writerow([
                arxiv_url,
                title_clean,
                summary_clean,
                pub_date,
                authors_formatted,
                primary_cat,
                cats_str # Tüm kategoriler (boşlukla ayrılmış ham hali)
            ])
            
        except Exception as e:
            # Nadir de olsa bozuk bir satır varsa atla ve hatayı bas
            print(f"Hata oluşan satır ID: {paper.get('id', 'Unknown')} - Hata: {e}")
            continue

print(f"\nİşlem tamamlandı! Dosya şurada: {output_file}")