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
    try:
        df = pd.read_csv(file_name)
        df['term'] = term
        all_data.append(df)
    except FileNotFoundError:
        print(f"File not found: {file_name}")

combined_df = pd.concat(all_data, ignore_index=True)

# 1. Calculate Mean Count for each term
mean_counts = combined_df.groupby('term')['count'].mean().sort_values(ascending=False).reset_index()
mean_counts.rename(columns={'count': 'Mean Count'}, inplace=True)

# 2. Generate Sorted Bar Chart
plt.figure(figsize=(10, 6))

sns.barplot(
    data=mean_counts,
    x='Mean Count',
    y='term',
    palette='viridis'
)

plt.title('Comparison of Average Quarterly Counts for 9 Terms', fontsize=14)
plt.xlabel('Mean Count', fontsize=12)
plt.ylabel('Term', fontsize=12)
plt.xticks(rotation=0, ha='center')

# Add values to the bars
for index, row in mean_counts.iterrows():
    plt.text(row['Mean Count'] + 1, index, f"{row['Mean Count']:.2f}", color='black', ha="left", va="center")

# Set x-axis limit to create space for the text labels on the right
max_val = mean_counts['Mean Count'].max()
plt.xlim(right=max_val * 1.1) # Extend the x-axis by 15% of the max value

plt.grid(axis='x', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('grafikler/mean_comparison_bar_chart.png')
plt.close()

# Print the data for confirmation and easy inclusion in the response
print("Mean Counts Sorted:")
print(mean_counts.to_markdown(index=False))