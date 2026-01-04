# TermFlow: Academic Trend Intelligence Platform 📈

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Status](https://img.shields.io/badge/Status-Prototype-green)

**TermFlow** is a data science analytics tool designed to decode the evolution of scientific concepts. By analyzing millions of academic papers from **ArXiv** and **OpenAlex**, it filters out noise to visualize which technologies are rising, which are stable, and which are fading away.

## 🚀 Features

* **Global Dashboard:** A macro view of the scientific zeitgeist with Word Clouds and Seasonality analysis.
* **Trend Explorer:**
    * **Rising Stars (Growth-Share Matrix):** Identify high-growth terms vs. high-volume terms.
    * **Stability Analysis (Volatility):** Distinguish between "Evergreen" concepts and fleeting "Hype" using statistical distribution (Bell Curve).
    * **Cross-Disciplinary Flow:** visualize how terms move between fields (e.g., Physics to CS).
* **Deep Dive:**
    * **Future Prediction:** Linear Regression models to forecast term popularity for the next 3 years.
    * **Semantic Context:** N-Gram (Bigram) analysis to capture true meaning (e.g., "Deep Learning" instead of "Deep").

## 📂 Project Structure

```bash
TermFlow/
├── app.py                # Main Streamlit application
├── data_loader.py        # Data ingestion and caching logic
├── plot_manager.py       # Visualization engine (Plotly/Matplotlib)
├── requirements.txt      # Project dependencies
├── README.md             # Project documentation
├── data/                 # Data folder (CSV files)
│   ├── all_data_merged.csv
│   ├── domain_yearly_stats.csv
│   └── monthly_article_counts.csv
└── assets/               # Static images (Logo, Charts)


## 🛠️ Installation
Clone the repository:

Bash

git clone [https://github.com/yourusername/termflow.git](https://github.com/yourusername/termflow.git)
cd termflow
Create a Virtual Environment (Recommended):

Bash

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
Install Dependencies:

Bash

pip install -r requirements.txt
## ▶️ How to Run
To start the web application, run the following command in your terminal:

Bash

streamlit run app.py
The application will automatically open in your default web browser at http://localhost:8501.
