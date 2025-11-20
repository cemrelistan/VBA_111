import arxiv
from arxiv import HTTPError
import pandas as pd
import time 
from datetime import datetime
import os # Dosya varlığını kontrol etmek için

# ----------------------------------------------------------------
# Parametreler
# ----------------------------------------------------------------
YILLAR = list(range(2020, 2026)) # [2020, 2021, 2022, 2023, 2024, 2025]
KATEGORI = "cat:econ.*"
MAKS_PER_QUARTER = 10000 # Her çeyrek için 100 makale
OUTPUT_FILENAME = "econ.csv" # Verilerin birikeceği dosya

# Çeyrek (Quarter) tanımları: (başlangıç_suffix, bitiş_suffix)
QUARTERS = [
    ("01010000", "03312359"), # Q1 (Ocak - Mart)
    ("04010000", "06302359"), # Q2 (Nisan - Haziran)
    ("07010000", "09302359"), # Q3 (Temmuz - Eylül)
    ("10010000", "12312359")  # Q4 (Ekim - Aralık)
]

# --- API İstemcisi ---
# Her API isteği (sayfa) arasında 5 saniye bekle.
# Her çeyrek için 100 makale (max_results=100) ve sayfa boyutu 100 (page_size=100)
# olacağı için, bu ayar her *çeyrek* arasında 5 saniye beklememizi sağlar.
client = arxiv.Client(page_size=100, delay_seconds=5)

# --- CSV Başlık Kontrolü ---
# Eğer dosya varsa, tekrar başlık yazmayacağız (mode='a' append)
# Eğer dosya yoksa, ilk yazmada başlık ekleyeceğiz (mode='w' write)
# os.path.exists() ile dosyanın var olup olmadığını kontrol edebiliriz,
# ama daha kolayı, bir 'is_first_write' bayrağı tutmaktır.
# Ancak en temizi: 'mode' ve 'header' parametrelerini dinamik yönetmektir.
is_first_write = not os.path.exists(OUTPUT_FILENAME)


print(f"Kademeli veri çekme işlemi başlatılıyor.")
print(f"Veriler '{OUTPUT_FILENAME}' dosyasına eklenecek.")
if is_first_write:
    print("Dosya bulunamadı, yeni dosya oluşturulacak ve başlık (header) eklenecek.")
else:
    print("Dosya bulundu, yeni veriler dosyanın sonuna eklenecek.")

# ----------------------------------------------------------------
# Ana Veri Çekme Döngüsü
# ----------------------------------------------------------------
now = datetime.now()
current_year = now.year
current_quarter = (now.month - 1) // 3 + 1 # 1, 2, 3, veya 4

for year in YILLAR:
    
    # Gelecek yılları tamamen atla
    if year > current_year:
        print(f"\n--- YIL: {year} (Gelecek yıl, atlanıyor) ---")
        continue

    print(f"\n--- YIL: {year} ---")

    for i, (q_start, q_end) in enumerate(QUARTERS):
        quarter_num = i + 1
        quarter_name = f"Q{quarter_num}"
        
        # Gelecek çeyrekleri atla
        if year == current_year and quarter_num > current_quarter:
            print(f"   --- Çeyrek: {year}-{quarter_name} (Gelecek çeyrek, atlanıyor) ---")
            continue

        print(f"   --- Çeyrek: {year}-{quarter_name} işleniyor... ---")

        # Tarih aralığını belirle
        start_date = f"{year}{q_start}"
        end_date = f"{year}{q_end}"
        
        query_string = f"{KATEGORI} AND submittedDate:[{start_date} TO {end_date}]"
        
        search = arxiv.Search(
            query = query_string,
            max_results = MAKS_PER_QUARTER,
            sort_by = arxiv.SortCriterion.SubmittedDate,
            sort_order = arxiv.SortOrder.Descending # O çeyreğin en yeni 100 makalesi
        )

        try:
            results = client.results(search)
            
            quarterly_papers_list = []
            
            # API isteğini burada tetikle (generator'ü tüket)
            for r in results:
                quarterly_papers_list.append({
                    'id': r.entry_id,
                    'title': r.title,
                    'published_date': r.published,
                    'authors': [a.name for a in r.authors],
                    'primary_category': r.primary_category,
                    'summary': r.summary
                })
            
            if not quarterly_papers_list:
                print(f"   -> {year}-{quarter_name} için makale bulunamadı.")
                continue # Bir sonraki çeyreğe geç

            print(f"   -> {len(quarterly_papers_list)} adet makale bulundu.")

            # --- KONTROL NOKTASI: CSV'ye Kaydet ---
            df_quarter = pd.DataFrame(quarterly_papers_list)
            
            if is_first_write:
                # Dosya yoksa, 'write' modunda (w) aç ve başlığı ekle
                df_quarter.to_csv(OUTPUT_FILENAME, index=False, mode='w', encoding='utf-8-sig')
                is_first_write = False # Bayrağı kapat
                print(f"   -> CSV dosyası oluşturuldu ve veriler eklendi.")
            else:
                # Dosya varsa, 'append' modunda (a) aç ve başlık (header) ekleme
                df_quarter.to_csv(OUTPUT_FILENAME, index=False, mode='a', header=False, encoding='utf-8-sig')
                print(f"   -> CSV dosyasına {len(df_quarter)} yeni veri eklendi.")

        except HTTPError as e:
            # Rate limit veya sunucu hatası
            print(f"   !!! HATA ({year}-{quarter_name}): HTTP Hatası {e.status_code}.")
            print(f"   Sunucu meşgul. Bu çeyrek atlanıyor. Bir sonraki denenecek...")
            continue # Bu çeyreği atla, döngüye devam et
        
        except Exception as e:
            # Diğer olası hatalar (örn. internet koptu)
            print(f"   !!! BEKLENMEDİK HATA ({year}-{quarter_name}): {e}")
            print(f"   Bu çeyrek atlanıyor. Bir sonraki denenecek...")
            continue # Bu çeyreği atla, döngüye devam et

print(f"\n--- Veri Çekme İşlemi Tamamlandı! ---")
print(f"Tüm veriler '{OUTPUT_FILENAME}' dosyasında.")