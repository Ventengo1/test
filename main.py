import re
import streamlit as st
import requests
import yfinance as yf
from datetime import datetime, timedelta

# --- Configurations ---
API_KEY = "AIzaSyDvdx1ZVxkDsUCYUAIm7XkZBqgOzdf-6dY"
CSE_ID = "d4b7bac4f507f4b84"

# --- Sentiment Keywords ---
very_positive_keywords = {"skyrocket", "blockbuster", "blowout", "explode", "unprecedented", "all-time high", "record-breaking", "soars", "soar"}
positive_keywords = {"gain", "rise", "rises", "beat", "beats expectations", "surge", "surges", "record", "profit", "strong", "up", "increase", "growth", "positive", "upgrade", "buy", "bullish", "rally", "boost", "opportunity", "leads", "upside", "boosts", "rallied", "outperforms"}
negative_keywords = {"loss", "fall", "drop", "decline", "miss", "cut", "downgrade", "bearish", "warn", "plunge", "weak", "down", "decrease", "negative", "recall", "lawsuit", "crash", "hurt", "tariffs", "prices", "price", "missed", "bad"}
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

# --- Styling and Layout ---
st.set_page_config(page_title="Stock Sentiment Analyzer", layout="wide")

# --- Header Section ---
st.markdown("""
    <div style='background: linear-gradient(to right, #00aaff, #1e3c72); padding: 2rem; border-radius: 10px; text-align: center; color: white;'>
        <h1>📈 Stock Sentiment Analyzer</h1>
        <p style='font-size: 18px;'>Analyze the sentiment of recent stock news and view the latest trends and insights.</p>
    </div>
""", unsafe_allow_html=True)

# --- Stock Ticker Input with Styling ---
st.markdown("""
    <div style='background-color: #2C3E50; padding: 1rem; border-radius: 8px; margin-bottom: 2rem;'>
        <h3 style='color: white; text-align: center;'>Enter Stock Ticker Symbol</h3>
    </div>
""", unsafe_allow_html=True)

ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA):", "", key="ticker_input", placeholder="Stock Symbol")

# --- Check if Ticker is Provided ---
if ticker:
    col1, col2 = st.columns([2.5, 1.5])

    with col1:
        with st.spinner("🔍 Fetching news..."):
            articles = search_stock_news_google(ticker, max_results=25)

        if articles:
            sentiment_counts = {s: 0 for s in ["Very Positive", "Positive", "Neutral", "Negative", "Very Negative"]}
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

            # --- Display Sentiment Summary ---
            st.markdown("### 🧾 Sentiment Summary")
            for sentiment, count in sentiment_counts.items():
                st.write(f"{sentiment}: {count}")

            # --- Display Articles ---
            st.markdown("### 📰 Headlines")
            for item in scored_articles:
                with st.expander(f"[{item['sentiment']}] {item['title']}"):
                    st.write(f"**Snippet:** {item['snippet']}")
                    st.write(f"**Score:** {item['score']}")
                    st.write(f"**Positive hits:** {item['pos']} | **Negative hits:** {item['neg']}")
                    st.write(f"[Read Article]({item['link']})")

        else:
            st.warning("No news articles found in the last 14 days.")

    with col2:
        # --- 30-Day Stock Chart ---
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
    
else:
    st.markdown("""
        <div style='background-color: #ecf0f1; padding: 1rem; border-radius: 8px; text-align: center;'>
            <p style='color: #34495e;'>Please enter a stock ticker symbol to get started.</p>
        </div>
    """, unsafe_allow_html=True)
