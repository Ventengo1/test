import streamlit as st
import requests
import re
from datetime import datetime, timedelta

# Google Custom Search config
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
    "decrease", "layoff", "negative", "recall", "lawsuit", "crash", "hurt", "tariffs", "prices", "price", "missed"
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

# --- Google CSE search ---
def search_stock_news_google(stock_symbol, max_results=25, days_back=14):
    query = f"{stock_symbol} stock"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": 10,
    }

    all_results = []
    start_index = 1
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)

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
            pub_date = item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", "")

            # Date filtering
            try:
                if pub_date:
                    date_obj = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    if not (start_date <= date_obj <= end_date):
                        continue
            except Exception:
                pass  # Keep if no valid date

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
st.title("🔍 Google Stock News Sentiment Analyzer")
st.subheader("Using Google Custom Search + AI Sentiment")

ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA)", "").upper()

if ticker:
    with st.spinner("Fetching news..."):
        headlines = search_stock_news_google(ticker)

    if headlines:
        sentiment_counts = {
            "Very Positive": 0,
            "Positive": 0,
            "Neutral": 0,
            "Negative": 0,
            "Very Negative": 0
        }
        total_score = 0
        scored_headlines = []

        for article in headlines:
            sentiment, score, pos, neg = get_sentiment_weighted(article['title'])
            sentiment_counts[sentiment] += 1
            total_score += score
            scored_headlines.append({
                "title": article['title'],
                "link": article['link'],
                "sentiment": sentiment,
                "score": score,
                "pos": pos,
                "neg": neg
            })

        st.markdown("---")
        st.subheader("🧾 Sentiment Summary")
        for sentiment_type, count in sentiment_counts.items():
            st.write(f"{sentiment_type}: {count}")

        average_score = total_score / len(scored_headlines)
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

        # Headlines
        st.markdown("---")
        st.subheader("📰 Headlines")

        for item in scored_headlines:
            with st.expander(f"[{item['sentiment']}] {item['title']}"):
                st.write(f"**Score:** {item['score']}")
                st.write(f"**Positive hits:** {item['pos']} | **Negative hits:** {item['neg']}")
                st.write(f"[Read Article]({item['link']})")

    else:
        st.warning("No news found in the last 14 days.")
