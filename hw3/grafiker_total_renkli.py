import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the combined data from the previous step (assuming it was saved or available in memory,
# but to be safe, I'll re-combine and prepare it briefly if needed, though for the thought process I know it exists.
# Since the interpreter state is reset, I must re-read and combine the files.)

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

all_data = []
for term, file_name in file_map.items():
    df = pd.read_csv(file_name)
    df['term'] = term
    all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)

# Prepare for plotting and sorting
combined_df['sort_period'] = combined_df['period'].str.replace('Q', '.').astype(float)
combined_df = combined_df.sort_values(by='sort_period')

# --- 1. Normalized Stacked Area Chart (Composition over Time) ---

# Calculate total count per period
total_counts = combined_df.groupby('period')['count'].sum().reset_index()
total_counts.rename(columns={'count': 'total_count'}, inplace=True)

# Merge total counts back to the main DataFrame
df_merged = pd.merge(combined_df, total_counts, on='period')

# Calculate the percentage of each term in that period
df_merged['percentage'] = (df_merged['count'] / df_merged['total_count']) * 100

# Pivot the data for stacked area chart
df_pivot = df_merged.pivot_table(index='period', columns='term', values='percentage', fill_value=0)

# Define the desired order for stacking
group_order = [
    "Public Health", "Social Distancing","COVID Pandemic",
    "Machine Learning", "Artificial Intelligence", "Large Language Models",
    "Climate Change", "Electric Vehicle", "Renewable Energy"
]
df_pivot = df_pivot[group_order]


# Create the plot
plt.figure(figsize=(14, 8))
df_pivot.plot(kind='area', stacked=True, colormap='Spectral', ax=plt.gca())

plt.title('Topic Density Distribution of 9 Terms Over Time (Composition Analysis)', fontsize=16)
plt.xlabel('Period (Quarter)', fontsize=12)
plt.ylabel('Percentage (%)', fontsize=12)

# Set x-axis ticks to show only the first quarter of each year
all_ticks = df_pivot.index.tolist()
tick_locations = [i for i, tick in enumerate(all_ticks) if tick.endswith('Q1')]
tick_labels = [all_ticks[i] for i in tick_locations]
ax = plt.gca()
ax.set_xticks(tick_locations)
ax.set_xticklabels(tick_labels, rotation=45, ha='right')

plt.legend(title='Term', bbox_to_anchor=(1.01, 1), loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('grafikler/normalized_stacked_area_chart.png')
plt.close()
