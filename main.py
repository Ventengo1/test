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

# --- Custom CSS for Font + Styling ---
st.set_page_config(layout="wide", page_title="Stock Sentiment Analyzer")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f5f7fa;
    }

    .stTextInput>div>div>input {
        font-size: 1.1rem;
        padding: 0.5rem;
    }

    .input-box {
        background-color: #eaf0f7;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-top: 1rem;
    }

    .hero-banner {
        background: linear-gradient(to right, #4facfe, #00f2fe);
        color: white;
        border-radius: 12px;
        padding: 2.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(0,0,0,0.1);
        text-align: center;
    }

    .hero-banner h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    .hero-banner p {
        font-size: 1.2rem;
        opacity: 0.95;
    }
    </style>
""", unsafe_allow_html=True)

# --- Hero Banner ---
st.markdown("""
<div class="hero-banner">
    <h1>📊 Stock Sentiment Analyzer</h1>
    <p>Analyze the latest stock news, trends, and market mood — all in one sleek dashboard.</p>
</div>
""", unsafe_allow_html=True)

# --- Input Box ---
with st.container():
    st.markdown('<div class="input-box">', unsafe_allow_html=True)
    ticker = st.text_input("🔎 Enter Stock Ticker Symbol (e.g., AAPL, TSLA):", "").upper()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Stock Data and Sentiment Display ---
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
                st.markdown(f"<span style='color:{color}; font-weight:600'>{sentiment}:</span> {count}", unsafe_allow_html=True)

            st.markdown(f"### 📊 Overall Sentiment for <span style='color:{sentiment_colors[overall]}'><strong>{ticker}</strong>: {overall}</span>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("### 📰 Headlines")

            for item in scored_articles:
                color = sentiment_colors[item['sentiment']]
                with st.container():
                    st.markdown(f"""
                        <div style='border-left: 5px solid {color}; padding-left: 15px; margin-bottom: 10px;'>
                            <h5 style='color: {color};'>{item['sentiment']}</h5>
                            <b>{item['title']}</b><br>
                            <i>{item['snippet']}</i><br>
                            <small>👍 {item['pos']} | 👎 {item['neg']} | Score: {item['score']}</small><br>
                            <a href="{item['link']}" target="_blank">🔗 Read More</a>
                        </div>
                    """, unsafe_allow_html=True)

        else:
            st.warning("No news articles found in the last 14 days.")

    with col2:
        st.markdown("### 📉 30-Day Stock Chart")
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

        # Company Overview Section
        st.markdown("### 🏢 Company Overview")
        try:
            stock_info = yf.Ticker(ticker).info
            st.markdown(f"""
                <div style="background-color: #f0f4f7; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1)">
                    <b>Sector:</b> {stock_info.get("sector", "N/A")}<br>
                    <b>Market Cap:</b> ${round(stock_info.get("marketCap", 0) / 1e9, 2)}B<br>
                    <b>P/E Ratio:</b> {stock_info.get("trailingPE", "N/A")}<br>
                    <b>Dividend Yield:</b> {round(stock_info.get("dividendYield", 0) * 100, 2) if stock_info.get("dividendYield") else "N/A"}%<br>
                    <b>52-Week Range:</b> ${stock_info.get("fiftyTwoWeekLow", "N/A")} - ${stock_info.get("fiftyTwoWeekHigh", "N/A")}
                </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Company data error: {e}")
