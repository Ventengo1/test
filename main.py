import re
import streamlit as st
import requests
from datetime import datetime, timedelta

# --- Configurations ---
API_KEY = "AIzaSyDvdx1ZVxkDsUCYUAIm7XkZBqgOzdf-6dY"
CSE_ID = "d4b7bac4f507f4b84"

# --- Keyword sets ---
very_positive_keywords = {
    "skyrocket", "blockbuster", "blowout", "explode", "unprecedented", "all-time high", "record-breaking", "soars", "soar"
}

positive_keywords = {
    "gain", "rise", "rises", "beat", "beats expectations", "surge", "surges", "record", "profit", "strong", "up", "increase",
    "growth", "positive", "upgrade", "buy", "bullish", "rally", "boost", "opportunity", "leads", "upside", "boosts", "rallied", "outperforms"
}

negative_keywords = {
    "loss", "fall", "drop", "decline", "miss", "cut", "downgrade", "bearish", "warn", "plunge", "weak", "down",
    "decrease", "layoff", "negative", "recall", "lawsuit", "crash", "hurt", "tariffs", "prices", "price", "missed", "bad"
}

very_negative_keywords = {
    "collapse", "bankruptcy", "scandal", "meltdown", "fraud", "devastating", "catastrophic", "all-time low"
}

# --- Sentiment scoring ---
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

    if score >= 3:
        sentiment = "Very Positive"
    elif score > 0:
        sentiment = "Positive"
    elif score == 0:
        sentiment = "Neutral"
    elif score <= -3:
        sentiment = "Very Negative"
    else:
        sentiment = "Negative"

    return sentiment, score, pos_count, neg_count

# --- Google CSE Search Function ---
def search_stock_news_google(stock_symbol, max_results=25):
    query = f"{stock_symbol} stock"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": 10,
        "dateRestrict": "d14"  # Last 14 days
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

            all_results.append({
                "title": title,
                "link": link,
                "snippet": snippet
            })

            if len(all_results) >= max_results:
                break

        start_index += 10

    return all_results

# --- Streamlit UI ---
st.title("📈 Stock News Sentiment Analyzer")
st.subheader("Analyze recent news headlines for stock sentiment")

ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA)", "").upper()

if ticker:
    with st.spinner("Fetching news..."):
        articles = search_stock_news_google(ticker, max_results=25)

    if articles:
        sentiment_counts = {
            "Very Positive": 0,
            "Positive": 0,
            "Neutral": 0,
            "Negative": 0,
            "Very Negative": 0
        }
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

        st.markdown("---")
        st.subheader("🧾 Sentiment Summary")
        for sentiment_type, count in sentiment_counts.items():
            st.write(f"{sentiment_type}: {count}")

        average_score = total_score / len(scored_articles) if scored_articles else 0
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

        st.markdown(f"### 📊 Overall Sentiment for **{ticker}**: {overall}")

        st.markdown("---")
        st.subheader("📰 Headlines")
        for item in scored_articles:
            with st.expander(f"[{item['sentiment']}] {item['title']}"):
                st.write(f"**Snippet:** {item['snippet']}")
                st.write(f"**Score:** {item['score']}")
                st.write(f"**Positive hits:** {item['pos']} | **Negative hits:** {item['neg']}")
                st.write(f"[Read Article]({item['link']})")

    else:
        st.warning("No news articles found in the last 14 days.")
