import yfinance as yf
import re
import streamlit as st

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

# --- Weighted Overall Sentiment ---
def get_weighted_overall_sentiment(headlines):
    total_weighted_score = 0
    total_weight = 0

    for item in headlines:
        score = item['score']
        weight = max(1, abs(score))  # More extreme = more weight
        total_weighted_score += score * weight
        total_weight += weight

    if total_weight == 0:
        return "Neutral"

    average_weighted_score = total_weighted_score / total_weight

    if average_weighted_score >= 3:
        return "Very Positive"
    elif average_weighted_score > 0:
        return "Positive"
    elif average_weighted_score == 0:
        return "Neutral"
    elif average_weighted_score <= -3:
        return "Very Negative"
    else:
        return "Negative"

# --- Streamlit UI ---
st.title("📈 Stock News Sentiment Analyzer")
st.subheader("Analyze recent news headlines for stock sentiment")

ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA)", "").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if news:
            st.success(f"Fetched {len(news)} news headlines for {ticker}")
            sentiment_counts = {
                "Very Positive": 0,
                "Positive": 0,
                "Neutral": 0,
                "Negative": 0,
                "Very Negative": 0
            }
            total_score = 0
            headline_count = 0
            scored_headlines = []

            for item in news:
                content = item.get("content", item)
                title = content.get("title", "No Title Found")
                link_data = content.get("canonicalUrl") or content.get("clickThroughUrl")
                link = link_data["url"] if isinstance(link_data, dict) and "url" in link_data else "No Link Found"

                sentiment, score, pos, neg = get_sentiment_weighted(title)
                sentiment_counts[sentiment] += 1
                total_score += score
                headline_count += 1

                scored_headlines.append({
                    "sentiment": sentiment,
                    "title": title,
                    "score": score,
                    "pos": pos,
                    "neg": neg,
                    "link": link
                })

            # --- Summary section FIRST ---
            st.markdown("---")
            st.subheader("🧾 Sentiment Summary")
            for sentiment_type, count in sentiment_counts.items():
                st.write(f"{sentiment_type}: {count}")

            average_score = total_score / headline_count if headline_count else 0
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

            # --- Weighted Overall Sentiment ---
            weighted_overall = get_weighted_overall_sentiment(scored_headlines)
            st.markdown(f"**🧠 Weighted Sentiment (Strength-Based):** {weighted_overall}")

            # --- Then show the headlines ---
            st.markdown("---")
            st.subheader("📰 Headlines")

            for item in scored_headlines:
                with st.expander(f"[{item['sentiment']}] {item['title']}"):
                    st.write(f"**Score:** {item['score']}")
                    st.write(f"**Positive hits:** {item['pos']} | **Negative hits:** {item['neg']}")
                    st.write(f"[Read Article]({item['link']})")

        else:
            st.warning("No news found for this ticker.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
