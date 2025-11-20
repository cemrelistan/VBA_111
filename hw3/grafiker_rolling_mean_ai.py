import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# List of the three provided files
file_names = {
    "Artificial Intelligence": "data/ai/artificial_intelligence_quarterly_counts.csv",
    "Large Language": "data/ai/large_language_quarterly_counts.csv",
    "Machine Learning": "data/ai/machine_learning_quarterly_counts.csv"
}

# Load and combine data
all_data = []
for term, file_name in file_names.items():
    df = pd.read_csv(file_name)
    df['term'] = term
    all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)

# Inspect the combined DataFrame
print(combined_df.head())
print(combined_df.info())


# Convert 'period' to a sortable format for correct plotting order, e.g., 'YYYY.Q'
combined_df['sort_period'] = combined_df['period'].str.replace('Q', '.')
combined_df['sort_period'] = combined_df['sort_period'].astype(float)

# Sort the data
combined_df = combined_df.sort_values(by='sort_period')

# 1. Sophisticated Line Plot with Rolling Mean
# Calculate 4-quarter rolling mean for each term
combined_df['rolling_mean'] = combined_df.groupby('term')['count'].transform(lambda x: x.rolling(window=4, min_periods=1).mean())

# Calculate the total mean
total_mean = combined_df['count'].mean()

plt.figure(figsize=(12, 6))

# Plot the raw data
sns.lineplot(
    data=combined_df,
    x='period',
    y='count',
    hue='term',
    linestyle='--', # Dotted line for raw data
    alpha=0.4,
    legend=False,
)

# Plot the smoothed trend (rolling mean)
sns.lineplot(
    data=combined_df,
    x='period',
    y='rolling_mean',
    hue='term',
    linewidth=2.5, # Thicker line for trend
    alpha=1,
)

# Add a horizontal line for the total mean
plt.axhline(total_mean, color='red', linestyle='--', label=f'Total Mean ({total_mean:.2f})')
plt.legend()

plt.title('Quarterly Counts for AI Related Terms: Raw Data and 4-Quarter Rolling Mean', fontsize=14)
plt.xlabel('Period (Quarter)', fontsize=12)
plt.ylabel('Count', fontsize=12)

# Rotate x-axis labels for readability and only show every 4th label (yearly)
n = 4 # show every 4th label
xticks = combined_df['period'].unique()
plt.xticks(xticks[::n], rotation=45, ha='right')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.savefig('grafikler/ai_time_series_line_plot.png')
plt.close()

# 2. Calculate and display required statistics (Mean and Std. Dev.)
stats_df = combined_df.groupby('term')['count'].agg(['mean', 'std']).reset_index()
stats_df['std'] = stats_df['std'].fillna(0) # Fill NaN for terms with only one count if any
stats_df = stats_df.rename(columns={'mean': 'Mean Count', 'std': 'Standard Deviation'})

print(stats_df)
