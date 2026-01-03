import arxiv
from arxiv import HTTPError
import pandas as pd
import time 
from datetime import datetime
import os
import json
import calendar

# ----------------------------------------------------------------
# Parametreler
# ----------------------------------------------------------------
YILLAR = list(range(2014, 2027))  # 2012'den 2026'ya kadar
KATEGORI = "cat:econ.*"
MAKS_PER_MONTH = 10000  # Her ay için maksimum makale sayısı
OUTPUT_FILENAME = "econ.csv"  # Verilerin birikeceği dosya
CHECKPOINT_FILENAME = "checkpoint_log.json"  # Checkpoint log dosyası

# Ay tanımları: Her ayın son günü dinamik olarak hesaplanacak
MONTHS = list(range(1, 13))  # 1-12 arası aylar

# --- API İstemcisi ---
# Ban yememek için delay_seconds artırıldı
client = arxiv.Client(page_size=100, delay_seconds=5)

# ----------------------------------------------------------------
# Checkpoint Fonksiyonları
# ----------------------------------------------------------------
def load_checkpoint():
    """Checkpoint dosyasını yükle ve son kaldığı yeri döndür"""
    if os.path.exists(CHECKPOINT_FILENAME):
        try:
            with open(CHECKPOINT_FILENAME, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
                print(f"Checkpoint bulundu: {checkpoint}")
                return checkpoint
        except (json.JSONDecodeError, Exception) as e:
            print(f"Checkpoint dosyası okunamadı: {e}")
            return None
    return None

def save_checkpoint(year, month):
    """Checkpoint kaydet - son başarıyla tamamlanan ay"""
    checkpoint = {
        "last_year": year,
        "last_month": month,
        "timestamp": datetime.now().isoformat(),
        "status": "completed"
    }
    with open(CHECKPOINT_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=4, ensure_ascii=False)
    print(f"   -> CHECKPOINT kaydedildi: {year}-{month:02d}")

def get_month_date_range(year, month):
    """Belirli bir ay için başlangıç ve bitiş tarihlerini döndür"""
    # Ayın son gününü al
    last_day = calendar.monthrange(year, month)[1]
    
    # ArXiv formatında tarihler: YYYYMMDDhhmm
    start_date = f"{year}{month:02d}010000"
    end_date = f"{year}{month:02d}{last_day}2359"
    
    return start_date, end_date

def should_skip_month(year, month, checkpoint):
    """Bu ay atlanmalı mı kontrol et (checkpoint'e göre)"""
    if checkpoint is None:
        return False
    
    last_year = checkpoint.get("last_year", 0)
    last_month = checkpoint.get("last_month", 0)
    
    # Eğer bu yıl/ay, checkpoint'teki yıl/aydan önce veya eşitse atla
    if year < last_year:
        return True
    if year == last_year and month <= last_month:
        return True
    
    return False

# ----------------------------------------------------------------
# CSV Kaydetme Fonksiyonu
# ----------------------------------------------------------------
is_first_write = not os.path.exists(OUTPUT_FILENAME)

def save_to_csv(papers_list):
    """Makale listesini CSV'ye kaydet"""
    global is_first_write
    
    if not papers_list:
        return
    
    df = pd.DataFrame(papers_list)
    
    if is_first_write:
        df.to_csv(OUTPUT_FILENAME, index=False, mode='w', encoding='utf-8-sig')
        is_first_write = False
        print(f"   -> CSV dosyası oluşturuldu ve {len(df)} veri eklendi.")
    else:
        df.to_csv(OUTPUT_FILENAME, index=False, mode='a', header=False, encoding='utf-8-sig')
        print(f"   -> CSV dosyasına {len(df)} yeni veri eklendi.")

# ----------------------------------------------------------------
# Ana Program
# ----------------------------------------------------------------
print("=" * 60)
print("ArXiv Ekonomi Makaleleri Veri Çekme - 1991'den Günümüze")
print("=" * 60)
print(f"Veriler '{OUTPUT_FILENAME}' dosyasına kaydedilecek.")
print(f"Checkpoint dosyası: '{CHECKPOINT_FILENAME}'")

# Checkpoint kontrolü
checkpoint = load_checkpoint()
if checkpoint:
    print(f"\nKaldığı yerden devam ediliyor: {checkpoint['last_year']}-{checkpoint['last_month']:02d} sonrası")
else:
    print("\nYeni başlangıç - 1991'den itibaren çekilecek.")

if is_first_write:
    print("CSV dosyası bulunamadı, yeni dosya oluşturulacak.")
else:
    print("Mevcut CSV dosyasına veri eklenecek.")

print("=" * 60)

# ----------------------------------------------------------------
# Ana Veri Çekme Döngüsü (Aylık)
# ----------------------------------------------------------------
now = datetime.now()
current_year = now.year
current_month = now.month

total_papers_collected = 0

for year in YILLAR:
    
    # Gelecek yılları tamamen atla
    if year > current_year:
        print(f"\n--- YIL: {year} (Gelecek yıl, atlanıyor) ---")
        continue

    print(f"\n{'='*40}")
    print(f"YIL: {year}")
    print(f"{'='*40}")

    for month in MONTHS:
        
        # Gelecek ayları atla
        if year == current_year and month > current_month:
            print(f"   {year}-{month:02d} (Gelecek ay, atlanıyor)")
            continue
        
        # Checkpoint kontrolü - zaten çekilmiş ayları atla
        if should_skip_month(year, month, checkpoint):
            print(f"   {year}-{month:02d} (Checkpoint'te mevcut, atlanıyor)")
            continue

        print(f"\n   --- {year}-{month:02d} işleniyor... ---")

        # Tarih aralığını belirle
        start_date, end_date = get_month_date_range(year, month)
        
        query_string = f"{KATEGORI} AND submittedDate:[{start_date} TO {end_date}]"
        
        search = arxiv.Search(
            query=query_string,
            max_results=MAKS_PER_MONTH,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        try:
            results = client.results(search)
            
            monthly_papers_list = []
            
            # API isteğini burada tetikle (generator'ü tüket)
            for r in results:
                monthly_papers_list.append({
                    'id': r.entry_id,
                    'title': r.title,
                    'published_date': r.published,
                    'authors': [a.name for a in r.authors],
                    'primary_category': r.primary_category,
                    'summary': r.summary
                })
            
            if not monthly_papers_list:
                print(f"   -> {year}-{month:02d} için makale bulunamadı.")
            else:
                print(f"   -> {len(monthly_papers_list)} adet makale bulundu.")
                total_papers_collected += len(monthly_papers_list)
                
                # CSV'ye kaydet
                save_to_csv(monthly_papers_list)
            
            # --- CHECKPOINT KAYDET ---
            # Her ayın sonunda checkpoint kaydet (makale olsun veya olmasın)
            save_checkpoint(year, month)
            
            # Rate limiting için ek bekleme (her ay arasında)
            print(f"   -> Sonraki ay için 3 saniye bekleniyor...")
            time.sleep(3)

        except HTTPError as e:
            print(f"   !!! HTTP HATASI ({year}-{month:02d}): Hata kodu {e.status_code}")
            if e.status_code == 429:
                print(f"   Rate limit aşıldı! 60 saniye bekleniyor...")
                time.sleep(60)
            else:
                print(f"   Sunucu hatası. 30 saniye bekleniyor...")
                time.sleep(30)
            # Bu ayı atla, checkpoint KAYDETME (tekrar denenecek)
            continue
        
        except Exception as e:
            print(f"   !!! BEKLENMEDİK HATA ({year}-{month:02d}): {e}")
            print(f"   10 saniye bekleniyor ve devam ediliyor...")
            time.sleep(10)
            # Bu ayı atla, checkpoint KAYDETME (tekrar denenecek)
            continue

print("\n" + "=" * 60)
print("VERİ ÇEKME İŞLEMİ TAMAMLANDI!")
print("=" * 60)
print(f"Toplam çekilen makale sayısı: {total_papers_collected}")
print(f"Veriler '{OUTPUT_FILENAME}' dosyasında.")
print(f"Son checkpoint: '{CHECKPOINT_FILENAME}' dosyasında.")