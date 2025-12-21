import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import deque

# File mapping
file_map = {
    "Artificial Intelligence": "data/ai/artificial_intelligence_quarterly_counts.csv",
    "Large Language Models": "data/ai/large_language_quarterly_counts.csv",
    "Machine Learning": "data/ai/machine_learning_quarterly_counts.csv",
    "Climate Change": "data/climate_change/climate_change_quarterly_counts.csv",
    "Electric Vehicle": "data/climate_change/electric_vehicle_quarterly_counts.csv",
    "Renewable Energy": "data/climate_change/renewable_energy_quarterly_counts.csv",
    "COVID Pandemic": "data/pandemic/covid_pandemic_quarterly_counts.csv",
    "Public Health": "data/pandemic/public_health_quarterly_counts.csv",
    "Social Distancing": "data/pandemic/social_distancing_quarterly_counts.csv"
}

# Load and combine data
all_data = []
for term, file_name in file_map.items():
    try:
        df = pd.read_csv(file_name)
        df['term'] = term
        all_data.append(df)
    except FileNotFoundError:
        pass

combined_df = pd.concat(all_data, ignore_index=True)

# Extract Year
combined_df['year'] = combined_df['period'].str[:4].astype(int)

# Group by Year and Term to get total yearly counts
yearly_counts = combined_df.groupby(['year', 'term'])['count'].sum().reset_index()

# Get list of years
years = sorted(yearly_counts['year'].unique())

# Setup the plot grid (2 rows, 3 columns for 6 years)
fig, axes = plt.subplots(3, 2, figsize=(16, 18)) # Adjusted figsize for 3x2 layout
axes = axes.flatten()

def gaussian_sort(df):
    """Sorts the dataframe rows to create a bell-curve shape based on 'count'."""
    # Sort by count descending first
    sorted_df = df.sort_values('count', ascending=False).reset_index(drop=True)
    
    # Use a deque to arrange: Largest in middle, then alternate right/left
    dq = deque()
    
    # Toggle for alternating sides. Start adding to the center (effectively right of empty)
    # But to get true center, we can just iterate.
    # Logic: [Max] -> [Max, 2nd] -> [3rd, Max, 2nd] -> [3rd, Max, 2nd, 4th] ...
    
    # Actually, simpler logic to ensure strict visual peak:
    # Start with empty deque.
    # 1. Append largest.
    # 2. Append next largest to right.
    # 3. Append next largest to left.
    # Repeat.
    
    for i, row in sorted_df.iterrows():
        if i == 0:
            dq.append(row)
        elif i % 2 == 1: # Odd indices (1, 3, 5...) -> Right
            dq.append(row)
        else: # Even indices (2, 4, 6...) -> Left
            dq.appendleft(row)
            
    return pd.DataFrame(dq)

# Create a plot for each year
for i, year in enumerate(years):
    if i >= 6: break 
    
    ax = axes[i]
    
    # Filter data for the specific year
    data_year = yearly_counts[yearly_counts['year'] == year]
    
    # Statistics for the year
    mu_year = data_year['count'].mean()
    mae_year = np.mean(np.abs(data_year['count'] - mu_year))
    
    # Rearrange data for "Gaussian Look"
    data_year_gaussian = gaussian_sort(data_year)
    
    # Define colors: Blue if count > Mean, else Gray
    # Note: Interpreting "MAE değerini aşan" as exceeding the Mean (mu_year), 
    # as MAE is an error metric and usually much smaller than the counts themselves.
    colors = ['blue' if x > mu_year else 'gray' for x in data_year_gaussian['count']]

    # Bar Plot
    sns.barplot(data=data_year_gaussian, x='term', y='count', ax=ax, palette=colors)
    
    # Mean Line
    ax.axhline(mu_year, color='red', linestyle='--', linewidth=2, label=f'Mean: {mu_year:.1f}')
    
    # MAE Text
    ax.text(0.95, 0.95, f'MAE: {mae_year:.2f}', transform=ax.transAxes, 
            fontsize=12, fontweight='bold', color='darkred',
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Formatting
    ax.set_title(f'Year {year}', fontsize=14, fontweight='bold')
    ax.set_ylabel('Total Count')
    ax.set_xlabel('')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=9)
    
    # Only add legend to the first plot or needed ones
    if i == 0:
        ax.legend(loc='upper left')
        
    ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.suptitle('Yearly Usage Counts Arranged as Bell Curve (Gaussian-like) with MAE Analysis', fontsize=18, y=1.02)
plt.savefig('yearly_counts_gaussian_sorted.png', bbox_inches='tight')
plt.close()