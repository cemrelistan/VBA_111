import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# ----------------------------------------------------------------
# PLOT: COMPARE ALL CATEGORIES
# ----------------------------------------------------------------
print("Generating plot: Comparing all categories...")

# 1. Veri dosyalarını bul
data_dir = 'data/pandemic'
csv_files = [f for f in os.listdir(data_dir) if f.endswith('_quarterly_counts.csv')]

# 2. Tüm verileri tek bir DataFrame'de birleştir
fig, ax = plt.subplots(figsize=(18, 10))

for filename in csv_files:
    # Dosya adından kategori adını çıkar (örn: "artificial_intelligence")
    category_name = filename.replace('_quarterly_counts.csv', '').replace('_', ' ').title()
    
    # Veriyi oku
    df_temp = pd.read_csv(os.path.join(data_dir, filename))
    
    # Tarih formatını ayarla
    df_temp['date'] = pd.PeriodIndex(df_temp['period'], freq='Q').to_timestamp()
    
    # Çizgiyi çizdir
    ax.plot(df_temp['date'], df_temp['count'], label=category_name,linewidth=3)


# --- Başlık, Eksenler ve Legend ---
ax.set_title('Quarterly Frequency Comparison of Different Categories', fontsize=18)
ax.set_xlabel('Date (by Quarter)', fontsize=14)
ax.set_ylabel('Frequency Count', fontsize=14)
ax.legend(title='Categories', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, which='both', linestyle='--', linewidth=0.5)

# X eksenini formatla
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")


plt.tight_layout(rect=[0, 0, 0.85, 1]) # Legend için sağda boşluk bırak

# Grafiği kaydet
output_filename = "plot_comparison.png"
fig.savefig(output_filename)
print(f"-> '{output_filename}' saved.")
plt.close(fig)

print("\n--- Comparison plot generated successfully! ---")