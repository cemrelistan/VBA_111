import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Map of term names to their file names
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
    df = pd.read_csv(file_name)
    df['term'] = term
    all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)

# Calculate mean count to determine the descending order
mean_order = combined_df.groupby('term')['count'].mean().sort_values(ascending=False).index

# Generate the Box Plot Sorted by Descending Mean
plt.figure(figsize=(12, 7))

sns.boxplot(
    data=combined_df,
    x='count', # Count on the X-axis (horizontal plot)
    y='term',  # Term on the Y-axis (categories)
    order=mean_order, # Sort by descending mean
    palette='viridis'
)

plt.title('Frequency Distribution by Term ', fontsize=16)
plt.xlabel('Quarterly Count', fontsize=14)
plt.ylabel('Term', fontsize=14)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('grafikler/sorted_box_plot.png')
plt.close()