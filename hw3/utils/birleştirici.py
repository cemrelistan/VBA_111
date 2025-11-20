import pandas as pd

vehicle = pd.read_csv('data/climate_change/electric_vehicle_quarterly_counts.csv')
vehicles = pd.read_csv('data/climate_change/electric_vehicles_quarterly_counts.csv')

total_vehicles = vehicle['count'] + vehicles['count']
combined_df = pd.DataFrame({
    'period': vehicle['period'],
    'count': total_vehicles
})
combined_df.to_csv('data/climate_change/electric_vehicle_combined.csv', index=False)