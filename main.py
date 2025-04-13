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
    elif score < 4:
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
    "Very Positive": "#27ae60",
    "Positive": "#2ecc71",
    "Neutral": "#95a5a6",
    "Negative": "#e74c3c",
    "Very Negative": "#c0392b"
}

# --- Fetch Index Data ---
def get_index_data(symbol):
    index = yf.Ticker(symbol)
    hist = index.history(period="1d")
    current_price = hist['Close'].iloc[0]
    change = hist['Close'].iloc[0] - hist['Open'].iloc[0]
    percentage_change = (change / hist['Open'].iloc[0]) * 100
    return current_price, change, percentage_change

# --- App UI ---
st.set_page_config(layout="wide")

# Header Section
st.markdown("""
    <div style='background: linear-gradient(to right, #003973, #e5e5be); padding: 1.5rem; border-radius: 10px; text-align: center; color: white;'>
        <h2>📈 Stock Sentiment Analyzer</h2>
        <p>Color-coded headlines + sentiment summary + chart — all in one place!</p>
    </div>
""", unsafe_allow_html=True)

# --- Stock Index Widgets on Homepage ---
st.markdown("### Major Stock Indexes")

col1, col2, col3 = st.columns(3)

with col1:
    # Dow Jones Industrial Average (DJIA)
    djia_price, djia_change, djia_pct = get_index_data("^DJI")
    st.markdown(f"""
        <div style='background-color:#2c3e50; color:white; padding: 10px; border-radius: 10px;'>
            <h3>Dow Jones</h3>
            <p><strong>Price:</strong> ${djia_price:,.2f}</p>
            <p><strong>Change:</strong> ${djia_change:,.2f} ({djia_pct:+.2f}%)</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    # NASDAQ Composite
    nasdaq_price, nasdaq_change, nasdaq_pct = get_index_data("^IXIC")
    st.markdown(f"""
        <div style='background-color:#2c3e50; color:white; padding: 10px; border-radius: 10px;'>
            <h3>NASDAQ</h3>
            <p><strong>Price:</strong> ${nasdaq_price:,.2f}</p>
            <p><strong>Change:</strong> ${nasdaq_change:,.2f} ({nasdaq_pct:+.2f}%)</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    # S&P 500
    sp500_price, sp500_change, sp500_pct = get_index_data("^GSPC")
    st.markdown(f"""
        <div style='background-color:#2c3e50; color:white; padding: 10px; border-radius: 10px;'>
            <h3>S&P 500</h3>
            <p><strong>Price:</strong> ${sp500_price:,.2f}</p>
            <p><strong>Change:</strong> ${sp500_change:,.2f} ({sp500_pct:+.2f}%)</p>
        </div>
    """, unsafe_allow_html=True)

# Enter Stock Ticker Section
ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA):", "").upper()

if ticker:
    col1, col2 = st.columns([2.3, 1.7])

    # News and Sentiment Analysis Section
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
                st.markdown(f"<span style='color:{color}; font-weight:600'>{sentiment}:</span> {count}", unsafe_allow_html=True)

            st.markdown(f"### 📊 Overall Sentiment for <span style='color:{sentiment_colors[overall]}'><strong>{ticker}</strong>: {overall}</span>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("### 📰 News Articles")

            for article in scored_articles:
                sentiment = article["sentiment"]
                st.markdown(f"#### [{article['title']}]({article['link']}) - {sentiment}")
                st.write(article["snippet"])

    # If no ticker, show placeholder message
else:
    st.write("Please enter a stock ticker symbol to analyze news.")
