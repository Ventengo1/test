import re
import streamlit as st
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- Configurations ---
API_KEY = "AIzaSyDvdx1ZVxkDsUCYUAIm7XkZBqgOzdf-6dY"
CSE_ID = "d4b7bac4f507f4b84"

# --- Sentiment Keywords ---
very_positive_keywords = {"skyrocket", "blockbuster", "blowout", "explode", "unprecedented", "all-time high", "record-breaking", "soars", "soar"}
positive_keywords = {"gain", "rise", "rises", "beat", "beats expectations", "surge", "surges", "record", "profit", "strong", "up", "increase", "growth", "positive", "upgrade", "buy", "bullish", "rally", "boost", "opportunity", "leads", "upside", "boosts", "rallied", "outperforms"}
negative_keywords = {"loss", "fall", "drop", "decline", "miss", "cut", "downgrade", "bearish", "warn", "plunge", "weak", "down", "decrease", "layoff", "negative", "recall", "lawsuit", "crash", "hurt", "tariffs", "prices", "price", "missed", "bad"}
very_negative_keywords = {"collapse", "bankruptcy", "scandal", "meltdown", "fraud", "devastating", "catastrophic", "all-time low"}

# --- Sentiment Scoring ---
def get_sentiment_weighted(text):
    words = re.findall(r'\b\w+\b', text.lower())
    score = 0
    pos_count = neg_count = 0
    for word in words:
        if word in very_positive_keywords:
            score += 2
            pos_count += 1
        elif word in positive_keywords:
            score += 1
            pos_count += 1
        elif word in very_negative_keywords:
            score -= 2
            neg_count += 1
        elif word in negative_keywords:
            score -= 1
            neg_count += 1

    if score >= 10:
        sentiment = "Very Positive"
    elif score > 4:
        sentiment = "Positive"
    elif score < 4 and score > -4:
        sentiment = "Negative"
    elif score <= -10:
        sentiment = "Very Negative"
    else:
        sentiment = "Neutral"

    return sentiment, score, pos_count, neg_count

# --- Google CSE Search ---
def search_stock_news_google(stock_symbol, max_results=25):
    query = f"{stock_symbol} stock"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": 10,
        "dateRestrict": "d14"
    }

    all_results = []
    start_index = 1

    while len(all_results) < max_results:
        params["start"] = start_index
        response = requests.get(url, params=params)
        data = response.json()

        if "items" not in data:
            break

        for item in data["items"]:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")

            if "stock quote" in snippet.lower() or "historical data" in snippet.lower():
                continue

            all_results.append({
                "title": title,
                "link": link,
                "snippet": snippet
            })

            if len(all_results) >= max_results:
                break

        start_index += 10

    return all_results

# --- Custom Badge Colors ---
sentiment_colors = {
    "Very Positive": "#1abc9c",
    "Positive": "#2ecc71",
    "Neutral": "#95a5a6",
    "Negative": "#e67e22",
    "Very Negative": "#e74c3c"
}

# --- App UI Styling ---
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #f5f7fa;
        color: #222;
    }
    .card {
        background-color: #eaf0f7;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    .sentiment-box {
        padding: 12px;
        border-radius: 10px;
        margin: 10px 0;
    }
    h2, h3, h4 {
        color: #111;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("""
    <div class="card" style='text-align: center; background: linear-gradient(to right, #dff2fd, #d1f4e0);'>
        <h2 style="color: black;">Stock Sentiment Analyzer</h2>
        <p style='color: #333;'>Visualize market sentiment, headlines, and performance trends all in one place.</p>
    </div>
""", unsafe_allow_html=True)

# --- Main Index Widgets ---
st.markdown("### 🌍 Market Overview")
st.components.v1.html("""
    <div style="display: flex; justify-content: space-around;">
        <div style="width: 30%;">
            <iframe src="https://www.tradingview.com/widgetembed/?frameElementId=tradingview_e09e3&symbol=NASDAQ%3ANDX&interval=D&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=light&style=1&timezone=Etc%2FUTC&withdateranges=1&hideideas=1&studies_overrides={}&overrides={}&enabled_features=[]&disabled_features=[]&locale=en" width="100%" height="300" frameborder="0"></iframe>
        </div>
        <div style="width: 30%;">
            <iframe src="https://www.tradingview.com/widgetembed/?frameElementId=tradingview_67890&symbol=SPXM&interval=D&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=light&style=1&timezone=Etc%2FUTC&withdateranges=1&hideideas=1&studies_overrides={}&overrides={}&enabled_features=[]&disabled_features=[]&locale=en" width="100%" height="300" frameborder="0"></iframe>
        </div>
        <div style="width: 30%;">
            <iframe src="https://www.tradingview.com/widgetembed/?frameElementId=tradingview_67890&symbol=DJI&interval=D&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=light&style=1&timezone=Etc%2FUTC&withdateranges=1&hideideas=1&studies_overrides={}&overrides={}&enabled_features=[]&disabled_features=[]&locale=en" width="100%" height="300" frameborder="0"></iframe>
        </div>
    </div>
""", height=320)

# --- Input ---
ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA):", "").upper()

if ticker:
    col1, col2 = st.columns([2.3, 1.7])

    with col1:
        with st.spinner("🔍 Fetching news..."):
            articles = search_stock_news_google(ticker, max_results=25)

        if articles:
            sentiment_counts = {s: 0 for s in sentiment_colors}
            total_score = 0
            scored_articles = []

            for article in articles:
                title = article["title"]
                link = article["link"]
                snippet = article["snippet"]
                sentiment, score, pos, neg = get_sentiment_weighted(title)
                sentiment_counts[sentiment] += 1
                total_score += score

                scored_articles.append({
                    "sentiment": sentiment,
                    "title": title,
                    "score": score,
                    "pos": pos,
                    "neg": neg,
                    "link": link,
                    "snippet": snippet
                })

            average_score = total_score / len(scored_articles)
            if average_score >= 3:
                overall = "Very Positive"
            elif average_score > 0:
                overall = "Positive"
            elif average_score == 0:
                overall = "Neutral"
            elif average_score <= -3:
                overall = "Very Negative"
            else:
                overall = "Negative"

            st.markdown("### 🧾 Sentiment Summary")
            for sentiment, count in sentiment_counts.items():
                color = sentiment_colors[sentiment]
                st.markdown(f"<div class='sentiment-box' style='background-color:{color}33;'><b style='color:{color}'>{sentiment}:</b> {count}</div>", unsafe_allow_html=True)

            st.markdown(f"<h4>📊 Overall Sentiment for <span style='color:{sentiment_colors[overall]}'>{ticker}</span>: <b>{overall}</b></h4>", unsafe_allow_html=True)
            st.markdown("### 📰 Headlines")

            for item in scored_articles:
                color = sentiment_colors[item['sentiment']]
                st.markdown(f"""
                    <div class="card">
                        <h4 style='color:{color};'>{item['sentiment']}</h4>
                        <b>{item['title']}</b><br>
                        <i>{item['snippet']}</i><br><br>
                        <small>👍 {item['pos']} | 👎 {item['neg']} | Score: {item['score']}</small><br>
                        <a href="{item['link']}" target="_blank">🔗 Read More</a>
                    </div>
                """, unsafe_allow_html=True)

        else:
            st.warning("No news articles found in the last 14 days.")

    with col2:
        st.markdown("### 📈 30-Day Stock Chart")
        try:
            end_date = datetime.today()
            start_date = end_date - timedelta(days=30)
            data = yf.download(ticker, start=start_date, end=end_date)
            if not data.empty:
                st.line_chart(data["Close"])
            else:
                st.info("No chart data available.")
        except Exception as e:
            st.error(f"Chart error: {e}")

        st.markdown("### 🏢 Company Overview")
        try:
            info = yf.Ticker(ticker).info
            sector = info.get("sector", "N/A")
            market_cap = f"${round(info.get('marketCap', 0)/1e9, 2)}B"
            pe_ratio = info.get("trailingPE", "N/A")
            div_yield = info.get("dividendYield", None)
            div_yield_str = f"{round((div_yield or 0), 2)}%" if div_yield else "N/A"
            week_52_range = f"${info.get('fiftyTwoWeekLow', 'N/A')} - ${info.get('fiftyTwoWeekHigh', 'N/A')}"

            st.markdown(f"""
                <div class="card" style='background-color:#f0f4fa;'>
                    <p style='font-size:16px; color:#111;'>
                        <b>Sector:</b> {sector}<br>
                        <b>Market Cap:</b> {market_cap}<br>
                        <b>P/E Ratio:</b> {pe_ratio}<br>
                        <b>Dividend Yield:</b> {div_yield_str}<br>
                        <b>52-Week Range:</b> {week_52_range}
                    </p>
                </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error("Could not load company info.")
