import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

class PlotManager:
    
    # --- 1. GROWTH MATRIX ---
    def plot_growth_matrix(self, df, category, start_year, end_year):
        cat_df = df[df['category'] == category].copy()
        s_col, e_col = str(start_year), str(end_year)
        
        if s_col not in cat_df.columns or e_col not in cat_df.columns:
            return None

        cat_df = cat_df[(cat_df[s_col] > 0) & (cat_df[e_col] >= 5)]
        
        years_diff = end_year - start_year
        if years_diff < 1: years_diff = 1
        
        cat_df['CAGR'] = ((cat_df[e_col] / cat_df[s_col]) ** (1/years_diff)) - 1
        cat_df['Growth_Percent'] = cat_df['CAGR'] * 100
        cat_df['Volume'] = cat_df[e_col]
        
        cat_df = cat_df[cat_df['Growth_Percent'] < 5000]

        fig = px.scatter(
            cat_df,
            x="Volume",
            y="Growth_Percent",
            hover_name="bigram",
            color="Growth_Percent",
            title=f"Rising Stars: {category} ({start_year}-{end_year})",
            labels={"Volume": f"Volume ({end_year})", "Growth_Percent": "Growth Rate (%)"},
            color_continuous_scale="RdYlGn",
            height=600,
            log_x=True
        )
        return fig

    # --- 2. RELATION SCATTER ---
    def plot_relation_scatter(self, df, cat1, cat2):
        pivot_df = df.pivot_table(index='bigram', columns='category', values='total', aggfunc='sum').fillna(0)
        pivot_df = pivot_df.reset_index()
        
        if cat1 not in pivot_df.columns or cat2 not in pivot_df.columns:
            return None
        
        mask = (pivot_df[cat1] > 0) | (pivot_df[cat2] > 0)
        filtered_df = pivot_df[mask].copy()
        filtered_df['Total'] = filtered_df[cat1] + filtered_df[cat2]

        fig = px.scatter(
            filtered_df,
            x=cat1,
            y=cat2,
            hover_name="bigram",
            color="Total",
            size="Total",
            size_max=30,
            height=600,
            opacity=0.7,
            color_continuous_scale="Viridis",
            title=f"Relation Network: {cat1} vs {cat2}",
            labels={cat1: f"{cat1} (Usage)", cat2: f"{cat2} (Usage)"},
            log_x=True,
            log_y=True
        )
        fig.update_layout(template="plotly_dark")
        return fig

    # --- 3. NORMALIZED TRENDS ---
    def plot_normalized_trend(self, df_words, df_domains, category):
        cat_words = df_words[df_words['category'] == category]
        top_words = cat_words.groupby('bigram')['total'].sum().sort_values(ascending=False).head(5).index.tolist()
        plot_data = cat_words[cat_words['bigram'].isin(top_words)].copy()
        
        year_cols = [c for c in plot_data.columns if c.isdigit()]
        df_long = plot_data.melt(id_vars=['bigram', 'category'], value_vars=year_cols, var_name='year', value_name='count')
        df_long['year'] = pd.to_numeric(df_long['year'])
        
        dom_cols = [c for c in df_domains.columns if c.isdigit()]
        df_dom_long = df_domains.melt(id_vars=['category'], value_vars=dom_cols, var_name='year', value_name='total_papers')
        df_dom_long['year'] = pd.to_numeric(df_dom_long['year'])
        
        merged = pd.merge(df_long, df_dom_long, on=['category', 'year'], how='inner')
        merged['normalized_freq'] = (merged['count'] / merged['total_papers']) * 10000
        
        fig = px.line(
            merged, x='year', y='normalized_freq', color='bigram', markers=True,
            title=f"Normalized Trends in {category} (Per 10k Papers)",
            template="plotly_dark"
        )
        return fig
    
    # --- 4. VOLATILITY ANALYSIS (NEW ADDITION) ---
# --- 4. VOLATILITY DISTRIBUTION (ŞAPKA / BELL CURVE) ---# --- 4. VOLATILITY / POPULARITY DISTRIBUTION (BELL SHAPE) ---
    def plot_volatility_analysis(self, df, category):
        """
        Kelimeleri popülaritesine göre ortada en yüksek olacak şekilde dizer (Bell Shape).
        X: Kelimeler, Y: Kullanım Sayısı (Volume).
        """
        cat_df = df[df['category'] == category].copy()
        year_cols = [c for c in df.columns if c.isdigit()]
        
        # Toplam hacmi hesapla
        cat_df['Total_Volume'] = cat_df[year_cols].sum(axis=1)
        
        # En popüler 21 kelimeyi al (Sayısı değiştirilebilir)
        top_n = 21
        top_terms = cat_df.nlargest(top_n, 'Total_Volume').sort_values('Total_Volume', ascending=False).reset_index(drop=True)
        
        if top_terms.empty: return None

        # --- ŞAPKA (BELL) DİZİLİMİ ALGORİTMASI ---
        # En büyüğü ortaya, diğerlerini sağa-sola dağıtarak şapka şekli verelim.
        # Örn: [3, 1, 0, 2, 4] gibi indeksler oluşacak.
        
        left_side = []
        right_side = []
        center = []
        
        for i, row in top_terms.iterrows():
            if i == 0:
                center.append(row) # En büyük (Zirve)
            elif i % 2 == 1:
                left_side.append(row) # Tekler Sola
            else:
                right_side.append(row) # Çiftler Sağa
        
        # Sol tarafı küçükten büyüğe sırala (Zirveye tırmanış)
        left_side.sort(key=lambda x: x['Total_Volume'])
        # Sağ tarafı büyükten küçüğe sırala (Zirveden iniş)
        right_side.sort(key=lambda x: x['Total_Volume'], reverse=True)
        
        # Hepsini Birleştir: [Küçükler -> ZİRVE -> Küçükler]
        bell_shaped_data = pd.DataFrame(left_side + center + right_side)
        
        # --- ÇİZİM ---
        fig = go.Figure()
        
        # 1. Alan Grafiği (Filled Area)
        fig.add_trace(go.Scatter(
            x=bell_shaped_data['bigram'],
            y=bell_shaped_data['Total_Volume'],
            mode='lines+markers',
            fill='tozeroy', # Altını doldur
            name='Usage Volume',
            line=dict(color='#00f2c3', width=3, shape='spline'), # Spline: Çizgileri yumuşatır (kavisli yapar)
            marker=dict(size=8, color='white', line=dict(width=1, color='#00f2c3'))
        ))
        
        # En tepeye (Zirveye) özel bir etiket (Annotation)
        peak_term = center[0]
        fig.add_annotation(
            x=peak_term['bigram'],
            y=peak_term['Total_Volume'],
            text=f"👑 {peak_term['bigram']}",
            showarrow=True,
            arrowhead=1,
            yshift=10,
            font=dict(color="yellow", size=14, weight="bold")
        )

        fig.update_layout(
            title=f"Market Dominance Curve: {category} (Top {top_n} Terms)",
            xaxis_title="Terms (Arranged by Popularity)",
            yaxis_title="Total Usage Volume",
            template="plotly_dark",
            hovermode="x unified",
            height=500
        )
        
        return fig

    # --- 5. DEEP DIVE: PREDICTION & SUNBURST ---
    def plot_prediction(self, df, term):
        term_data = df[df['bigram'] == term].copy()
        year_cols = [c for c in df.columns if c.isdigit()]
        years = [int(y) for y in year_cols]
        counts = term_data[year_cols].sum().values
        
        trend_df = pd.DataFrame({'year': years, 'count': counts})
        trend_df = trend_df[trend_df['count'] > 0]
        
        if len(trend_df) < 3: return None
        
        X = trend_df['year'].values.reshape(-1, 1)
        y = trend_df['count'].values
        model = LinearRegression().fit(X, y)
        
        future_years = np.array([years[-1]+1, years[-1]+2, years[-1]+3]).reshape(-1, 1)
        future_preds = model.predict(future_years)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend_df['year'], y=trend_df['count'], mode='lines+markers', name='Actual Data', line=dict(color='#00f2c3', width=3)))
        fig.add_trace(go.Scatter(x=future_years.flatten(), y=future_preds, mode='lines+markers', name='Prediction', line=dict(color='orange', dash='dot')))
        fig.update_layout(title=f"'{term}' Future Prediction", template="plotly_dark")
        return fig

    def plot_sunburst(self, df, term):
        term_data = df[df['bigram'] == term][['category', 'total']]
        fig = px.sunburst(term_data, path=['category'], values='total', title=f"'{term}' Category Distribution", template="plotly_dark")
        return fig