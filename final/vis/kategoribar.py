import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns  # For better looking charts

# 1. READ DATA
try:
    df = pd.read_csv('data/all_data_merged.csv')
except FileNotFoundError:
    print("Error: 'all_data_merged.csv' file not found!")
    exit()

# Clean column names (lowercase, no spaces)
df.columns = [str(c).lower().strip() for c in df.columns]

# 2. PREPARE DATA
# Sum the 'total' column values for each category
# If 'total' column doesn't exist, calculate it
if 'total' in df.columns:
    category_counts = df.groupby('category')['total'].sum().sort_values(ascending=False)
else:
    # If total doesn't exist, sum all numeric columns (Backup plan)
    numeric_cols = df.select_dtypes(include=['number']).columns
    df['total_calc'] = df[numeric_cols].sum(axis=1)
    category_counts = df.groupby('category')['total_calc'].sum().sort_values(ascending=False)

# 3. DRAW CHART (MATPLOTLIB)
plt.figure(figsize=(12, 7))

# Create color palette
colors = sns.color_palette('viridis', len(category_counts))

# Create bar chart
bars = plt.bar(category_counts.index, category_counts.values, color=colors)

# Title and Labels
plt.title('Total Term/Article Counts Categories', fontsize=16, fontweight='bold')
plt.xlabel('Categories', fontsize=12)
plt.ylabel('Total Frequency', fontsize=12)
plt.xticks(rotation=45, ha='right')  # Rotate labels to fit
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Write numbers on top of bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height):,}',
             ha='center', va='bottom', fontsize=10)

plt.tight_layout()

# Show chart
plt.show()