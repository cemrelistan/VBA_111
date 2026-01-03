import pandas as pd
import matplotlib.pyplot as plt

# 1. READ DATA
try:
    df = pd.read_csv('data/all_data_merged.csv')
except FileNotFoundError:
    print("Error: 'all_data_merged.csv' file not found!")
    exit()

# Clean column names
df.columns = [str(c).lower().strip() for c in df.columns]

# 2. FIND YEAR COLUMNS
# Automatically detect years between 1990 and 2030 from column names
years = [c for c in df.columns if c.isdigit() and 1990 <= int(c) <= 2030]
years.sort() # Sort years (1990, 1991...)

if not years:
    print("Error: Year columns (1990-2030) not found in dataset.")
    exit()

# 3. GROUP AND ORGANIZE DATA
# Group by categories and sum each year's values
yearly_data = df.groupby('category')[years].sum()

# Transpose (Rows=Years, Columns=Categories) -> Required for plotting
yearly_data_t = yearly_data.T

# Convert year index to integer (For proper axis display)
yearly_data_t.index = yearly_data_t.index.astype(int)

# 4. DRAW CHART (MATPLOTLIB)
plt.figure(figsize=(14, 8))

# Draw a line for each category
for category in yearly_data_t.columns:
    plt.plot(yearly_data_t.index, yearly_data_t[category], 
             marker='o', markersize=4, linewidth=2, label=category.title())

# Title and Labels
plt.title('Categories Development Over Years (1990-2025)', fontsize=16, fontweight='bold')
plt.xlabel('Year', fontsize=12)
plt.ylabel('Annual Term/Article Frequency', fontsize=12)
plt.legend(title='Categories', bbox_to_anchor=(1.02, 1), loc='upper left') # Move legend outside
plt.grid(True, linestyle='--', alpha=0.6)
plt.xticks(yearly_data_t.index, rotation=45) # Show all years

# Adjust margins for cleaner view
plt.tight_layout()

# Show chart
plt.show()