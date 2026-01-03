import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.metrics import r2_score
import os

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
CONFIG = {
    "words_file": "data/all_data_merged.csv",
    "domains_file": "data/domain_yearly_stats.csv",
    "output_dir": "output",
    "target_year": 2030,
    "top_n": 5,  # Top N terms to plot per category
}

# ---------------------------------------------------------
# 1. DATA LOADING AND NORMALIZATION
# ---------------------------------------------------------
def load_and_normalize_data():
    if not os.path.exists(CONFIG['words_file']) or not os.path.exists(CONFIG['domains_file']):
        print(f"Error: Data files not found!")
        return None, None, None

    try:
        # A. Word Data
        df_words = pd.read_csv(CONFIG['words_file'])
        df_words.columns = [str(c).lower().strip() for c in df_words.columns]
        
        term_col = next((c for c in ['bigram', 'term', 'keyword', 'unnamed: 0'] if c in df_words.columns), None)
        if term_col == 'unnamed: 0': 
            df_words.rename(columns={'unnamed: 0': 'bigram'}, inplace=True)
            term_col = 'bigram'
        
        # B. Domain Data (Total Paper Counts)
        df_domains = pd.read_csv(CONFIG['domains_file'])
        df_domains.columns = [str(c).lower().strip() for c in df_domains.columns]
        if 'domain' in df_domains.columns:
            df_domains.rename(columns={'domain': 'category'}, inplace=True)

        # C. Find Years and Melt (Long Format)
        year_cols = [c for c in df_words.columns if c.isdigit() and 1990 <= int(c) <= 2030]
        
        # Melt Words
        df_words_long = df_words.melt(
            id_vars=['category', term_col], 
            value_vars=year_cols, 
            var_name='year', 
            value_name='count'
        )
        
        # Melt Domains
        d_cols = ['category'] + [y for y in year_cols if y in df_domains.columns]
        df_domains_long = df_domains[d_cols].melt(
            id_vars=['category'], 
            var_name='year', 
            value_name='total_papers'
        )

        # Fix Data Types
        df_words_long['year'] = pd.to_numeric(df_words_long['year'])
        df_words_long['count'] = pd.to_numeric(df_words_long['count'], errors='coerce').fillna(0)
        
        df_domains_long['year'] = pd.to_numeric(df_domains_long['year'])
        df_domains_long['total_papers'] = pd.to_numeric(df_domains_long['total_papers'], errors='coerce').fillna(1)

        # D. Merge
        merged_df = pd.merge(df_words_long, df_domains_long, on=['category', 'year'], how='inner')
        
        # E. Normalization (Per 10,000 papers)
        merged_df['norm_freq'] = (merged_df['count'] / merged_df['total_papers']) * 10000
        
        # Cleanup: Remove outliers
        merged_df = merged_df[merged_df['norm_freq'] < 50000]

        return merged_df, term_col, sorted(merged_df['year'].unique())

    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

# ---------------------------------------------------------
# 2. REGRESSION ENGINE
# ---------------------------------------------------------
def calculate_normalized_trends(df, category, start_year, end_year, term_col):
    # Category Filter
    df = df[df['category'] == category].copy()
    
    # Year Filter (Training Range)
    df_train = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    
    results = []
    grouped = df_train.groupby(term_col)
    
    for term, group in grouped:
        if len(group) < 2: 
            continue
        
        last_val = group[group['year'] == end_year]['norm_freq'].values
        if len(last_val) == 0 or last_val[0] < 1: 
            continue
        
        X = group['year'].values
        y = group['norm_freq'].values
        
        try:
            slope, intercept = np.polyfit(X, y, 1)
            y_pred = slope * X + intercept
            r2 = r2_score(y, y_pred)
            
            full_history = df[df[term_col] == term].sort_values('year')
            
            results.append({
                'term': term,
                'slope': slope,
                'intercept': intercept,
                'r2': r2,
                'current_norm': last_val[0],
                'history_x': full_history['year'].values,
                'history_y': full_history['norm_freq'].values
            })
        except:
            continue
            
    return pd.DataFrame(results)

# ---------------------------------------------------------
# 3. CHART GENERATION
# ---------------------------------------------------------
def create_forecast_chart(row, train_start, train_end, target_year, category):
    slope = row['slope']
    intercept = row['intercept']
    term = row['term']
    
    hist_x = row['history_x']
    future_x = np.arange(train_end + 1, target_year + 1)
    
    train_trend_y = slope * hist_x + intercept
    future_y = slope * future_x + intercept
    future_y = [max(0, y) for y in future_y]

    fig = go.Figure()
    
    # Actual Data (Points)
    fig.add_trace(go.Scatter(
        x=hist_x, y=row['history_y'], mode='markers+lines', name='Actual Data',
        line=dict(color='lightgray', width=1), marker=dict(color='blue', size=8)
    ))
    
    # Trend Line (Training Range)
    mask_train = (hist_x >= train_start) & (hist_x <= train_end)
    fig.add_trace(go.Scatter(
        x=hist_x[mask_train], y=train_trend_y[mask_train], mode='lines', name='Trend (Learned)',
        line=dict(color='orange', width=3)
    ))
    
    # Future Prediction
    fig.add_trace(go.Scatter(
        x=future_x, y=future_y, mode='lines', name=f'Prediction ({target_year})',
        line=dict(color='green', width=3, dash='dot')
    ))
    
    fig.update_layout(
        title=f"'{term}' Density Forecast (Per 10k Papers) - {category}",
        xaxis_title="Year",
        yaxis_title="Normalized Frequency (per 10k)",
        template="plotly_white",
        height=500,
        width=900
    )
    
    return fig

# ---------------------------------------------------------
# 4. MAIN EXECUTION
# ---------------------------------------------------------
def main():
    print("Loading data...")
    data_tuple = load_and_normalize_data()
    
    if data_tuple[0] is None:
        print("Error: Could not load data files.")
        return
    
    df, term_col, all_years = data_tuple
    min_yr, max_yr = int(min(all_years)), int(max(all_years))
    
    # Training range: last 5 years
    train_start = max_yr - 5 if (max_yr - 5) >= min_yr else min_yr
    train_end = max_yr
    target_year = CONFIG['target_year']
    
    # Create output directory
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    
    categories = sorted(df['category'].unique())
    print(f"Found {len(categories)} categories: {categories}")
    
    for category in categories:
        print(f"\nProcessing: {category}")
        
        res_df = calculate_normalized_trends(df, category, train_start, train_end, term_col)
        
        if res_df.empty:
            print(f"  No significant trends found for {category}")
            continue
        
        # Filter R2 > 0.5, sort by slope
        top_df = res_df[res_df['r2'] > 0.5].sort_values(by='slope', ascending=False).head(CONFIG['top_n'])
        
        if top_df.empty:
            print(f"  No high-quality trends (R2 > 0.5) for {category}")
            continue
        
        # Create category folder
        cat_dir = os.path.join(CONFIG['output_dir'], category.replace(" ", "_").lower())
        os.makedirs(cat_dir, exist_ok=True)
        
        # Generate charts for top terms
        for idx, row in top_df.iterrows():
            term = row['term']
            print(f"  Creating chart: {term}")
            
            fig = create_forecast_chart(row, train_start, train_end, target_year, category)
            
            # Save as HTML and PNG
            safe_term = term.replace(" ", "_").replace("/", "_").replace("\\", "_")[:50]
            html_path = os.path.join(cat_dir, f"{safe_term}_forecast.html")
            png_path = os.path.join(cat_dir, f"{safe_term}_forecast.png")
            
            fig.write_html(html_path)
            fig.write_image(png_path, scale=2)
            
            print(f"    Saved: {png_path}")
        
        # Save summary CSV
        summary_path = os.path.join(cat_dir, "top_trends_summary.csv")
        top_df[['term', 'slope', 'current_norm', 'r2']].to_csv(summary_path, index=False)
        print(f"  Summary saved: {summary_path}")
    
    print(f"\n✅ All charts saved to '{CONFIG['output_dir']}/' folder.")

if __name__ == "__main__":
    main()