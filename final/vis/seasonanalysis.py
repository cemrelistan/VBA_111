import pandas as pd
import matplotlib.pyplot as plt
import calendar

# ---------------------------------------------------------
# 1. LOAD AND PROCESS DATA
# ---------------------------------------------------------
try:
    df = pd.read_csv('analysis_results/monthly_article_counts.csv')
except FileNotFoundError:
    print("Error: 'monthly_article_counts.csv' not found.")
    exit()

# Convert date column to datetime objects
df['date'] = pd.to_datetime(df['date'])

# Extract month (1 = January, 12 = December)
df['month'] = df['date'].dt.month

# Calculate the Average number of articles per month (across all years)
# This reveals the seasonal pattern (e.g., "Do researchers submit more in Summer?")
monthly_stats = df.groupby('month')['count'].mean()

# ---------------------------------------------------------
# 2. PLOTTING (MATPLOTLIB)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))

# Plot line chart
plt.plot(monthly_stats.index, monthly_stats.values, 
         marker='o', linestyle='-', color='#1f77b4', linewidth=2.5, label='Avg. Articles')

# Highlight the Maximum (Peak) Month
max_month = monthly_stats.idxmax()
max_val = monthly_stats.max()
plt.scatter(max_month, max_val, color='green', s=150, zorder=5, label='Peak Month')
plt.text(max_month, max_val + (max_val*0.02), f'Peak: {calendar.month_abbr[max_month]}', 
         ha='center', fontsize=10, fontweight='bold', color='green')

# Highlight the Minimum (Lowest) Month
min_month = monthly_stats.idxmin()
min_val = monthly_stats.min()
plt.scatter(min_month, min_val, color='red', s=150, zorder=5, label='Lowest Month')
plt.text(min_month, min_val - (min_val*0.05), f'Low: {calendar.month_abbr[min_month]}', 
         ha='center', fontsize=10, fontweight='bold', color='red')

# ---------------------------------------------------------
# 3. FORMATTING (ENGLISH)
# ---------------------------------------------------------
plt.title('Publish Trend (Seasonality Analysis)', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Month of the Year', fontsize=12)
plt.ylabel('Average Number of Articles Submitted', fontsize=12)

# Set X-axis to show month names (Jan, Feb...) instead of numbers
plt.xticks(monthly_stats.index, [calendar.month_abbr[i] for i in monthly_stats.index], fontsize=11)

plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc='upper left')

plt.tight_layout()

# Show the plot
print(f"Analysis Complete: The busiest month is {calendar.month_name[max_month]}!")
plt.show()