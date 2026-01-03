import pandas as pd
import streamlit as st
import os

class DataLoader:
    def __init__(self):
        # Klasör yapına göre yollar
        self.main_data_path = os.path.join("data", "all_data_merged.csv")
        self.domain_stats_path = os.path.join("data", "domain_yearly_stats.csv")

    @st.cache_data
    def load_main_data(_self):
        """all_data_merged.csv dosyasını yükler ve temizler."""
        if not os.path.exists(_self.main_data_path):
            return None
        
        try:
            df = pd.read_csv(_self.main_data_path)
            # Sütun isimlerini standartlaştır
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # Kelime sütununu 'bigram' olarak sabitle
            possible_names = ['bigram', 'term', 'keyword', 'unnamed: 0']
            for name in possible_names:
                if name in df.columns:
                    df.rename(columns={name: 'bigram'}, inplace=True)
                    break
            
            # Yıl sütunlarını sayıya çevir, boşlukları 0 yap
            year_cols = [c for c in df.columns if c.isdigit()]
            for yc in year_cols:
                df[yc] = pd.to_numeric(df[yc], errors='coerce').fillna(0)
            
            # Total yoksa hesapla
            if 'total' not in df.columns and year_cols:
                df['total'] = df[year_cols].sum(axis=1)
                
            return df
        except Exception as e:
            st.error(f"Ana veri yükleme hatası: {e}")
            return None

    @st.cache_data
    def load_domain_stats(_self):
        """domain_yearly_stats.csv dosyasını yükler (Normalize trendler için)."""
        if os.path.exists(_self.domain_stats_path):
            df = pd.read_csv(_self.domain_stats_path)
            df.columns = [str(c).lower().strip() for c in df.columns]
            if 'domain' in df.columns:
                df.rename(columns={'domain': 'category'}, inplace=True)
            return df
        return None