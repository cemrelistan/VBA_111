import boto3
from botocore import UNSIGNED
from botocore.config import Config
import json
import gzip
import pandas as pd
import os
import glob
import time
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

# --- YENİ EKLENEN KÜTÜPHANE ---
from langdetect import detect, DetectorFactory, LangDetectException

# Deterministik sonuçlar için seed ayarı (Her seferinde aynı sonucu versin)
DetectorFactory.seed = 0

# --- AYARLAR ---
FINAL_FILENAME = "openalex_clean_english.csv"
TEMP_DIR = "temp_chunks_clean"
MAX_FILES = None   # Deneme için 50. Hepsini indirmek için None yap.
WORKER_COUNT = 6 # Bilgisayarının gücüne göre 4, 6 veya 8 yapabilirsin.

# İstenen Sütunlar
CSV_HEADERS = ['id', 'title', 'published_date', 'authors', 'primary_category', 'summary']

# ----------------

def reconstruct_abstract(inverted_index):
    """Abstract'ı düzgün metne çevirir."""
    if not inverted_index:
        return ""
    try:
        word_index = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_index.append((pos, word))
        word_index.sort()
        return " ".join([word for _, word in word_index])
    except:
        return ""

def is_title_english(text):
    """
    Başlığın gerçekten İngilizce olup olmadığını kontrol eder.
    """
    if not text or len(text) < 3: # Çok kısa metinlerde hata verebilir, atla
        return False
    try:
        # Metni analiz et
        lang = detect(text)
        return lang == 'en'
    except LangDetectException:
        return False

def process_single_file(file_key):
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    bucket_name = "openalex"
    
    chunk_data = []
    
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        
        with gzip.open(obj['Body'], mode='rt', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    
                    # --- 1. SEVİYE FİLTRE: METADATA ---
                    # OpenAlex'in kendi etiketine bak
                    if item.get('language') != 'en':
                        continue
                    
                    # Başlığı al
                    title = item.get('title', '')
                    
                    # --- 2. SEVİYE FİLTRE: İÇERİK ANALİZİ ---
                    # Başlık gerçekten İngilizce mi? (Burası yavaşlatır ama temizler)
                    if not is_title_english(title):
                        continue

                    # Verileri çek
                    authors_list = item.get('authorships', [])
                    authors_str = ", ".join([a.get('author', {}).get('display_name', '') for a in authors_list])
                    
                    primary_topic = item.get('primary_topic', {})
                    if primary_topic:
                        category = primary_topic.get('display_name')
                    else:
                        concepts = item.get('concepts', [])
                        category = concepts[0]['display_name'] if concepts else ""

                    summary_text = reconstruct_abstract(item.get('abstract_inverted_index'))

                    # Satırı oluştur
                    row = {
                        'id': item.get('id'),
                        'title': title,
                        'published_date': item.get('publication_date'),
                        'authors': authors_str,
                        'primary_category': category,
                        'summary': summary_text
                    }
                    chunk_data.append(row)
                    
                except (json.JSONDecodeError, TypeError):
                    continue
        
        if chunk_data:
            df = pd.DataFrame(chunk_data)
            safe_name = file_key.replace('/', '_').replace('.gz', '.csv')
            output_path = os.path.join(TEMP_DIR, safe_name)
            # Escape karakterlerini ve quoting'i düzgün ayarla
            df.to_csv(output_path, index=False, header=False, quoting=1) # quoting=1 (QUOTE_ALL) güvenlidir
            return len(chunk_data)
            
    except Exception as e:
        return f"Hata: {e}"
    
    return 0

def get_all_s3_files(bucket_name, prefix="data/works/", max_files=None):
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    files = []
    print("S3 dosya listesi çekiliyor...")
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    
    for page in pages:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.gz'):
                files.append(key)
                if max_files and len(files) >= max_files:
                    return files
    return files

def merge_csv_files():
    print(f"\nParçalar birleştiriliyor -> {FINAL_FILENAME}...")
    all_temp_files = glob.glob(os.path.join(TEMP_DIR, "*.csv"))
    
    with open(FINAL_FILENAME, 'w', encoding='utf-8', newline='') as outfile:
        # Başlığı manuel yaz (CSV formatına uygun tırnaklama ile)
        outfile.write('"id","title","published_date","authors","primary_category","summary"\n')
        
        for filename in tqdm(all_temp_files, desc="Birleştirme"):
            with open(filename, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write("\n")
    
    print("Temizlik yapılıyor...")
    for f in all_temp_files:
        os.remove(f)
    os.rmdir(TEMP_DIR)

def main():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    all_files = get_all_s3_files("openalex", max_files=MAX_FILES)
    print(f"İşlenecek dosya sayısı: {len(all_files)}")
    
    start_time = time.time()
    total_records = 0
    
    with ProcessPoolExecutor(max_workers=WORKER_COUNT) as executor:
        futures = {executor.submit(process_single_file, f): f for f in all_files}
        
        with tqdm(total=len(all_files), unit="dosya", desc="İşleniyor") as pbar:
            for future in as_completed(futures):
                result = future.result()
                if isinstance(result, int):
                    total_records += result
                pbar.update(1)

    print(f"\nİndirme bitti. Toplam {total_records} TEMİZ makale bulundu.")
    
    if total_records > 0:
        merge_csv_files()
        print(f"\n--- İŞLEM BAŞARILI ---")
        print(f"Dosya: {os.path.abspath(FINAL_FILENAME)}")
    else:
        print("Hiç veri bulunamadı.")
        
    print(f"Toplam Süre: {int(time.time() - start_time)} saniye")

if __name__ == "__main__":
    main()