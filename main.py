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

    if score >= 9:
        sentiment = "Very Positive"
    elif score > 4:
        sentiment = "Positive"
    elif score <=4 and =>-4 :
        sentiment = "Neutral"
    elif score <= -9:
        sentiment = "Very Negative"
    else:
        sentiment = "Negative"

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

# --- Streamlit UI ---
st.set_page_config(layout="wide")

# --- Title with Logo ---  
st.markdown("""
    <div class="card" style='text-align: center; background: linear-gradient(to right, #dff2fd, #d1f4e0); padding: 1rem; border-radius: 10px;'>
        <h2 style="color: black; font-family: 'Roboto', sans-serif; font-weight: 700;">
            <img src="https://i.ibb.co/wNLf7hDj/Screenshot-2025-04-12-210441-removebg-preview.png"
                 width="50" alt="Logo" style="vertical-align: middle; margin-right: 10px;">
            Stock Sentiment Analyzer
        </h2>
        <p style='color: #333; font-size: 0.9rem; margin-top: 0.2rem;'>Visualize market sentiment, headlines, and performance trends all in one place.</p>
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



# --- Widgets ---
ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA):", "").upper()

if ticker:
    col1, col2 = st.columns([2.3, 1.7])

    # --- Left column: News & sentiment ---
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

    # --- Right column: Chart + Company Stats ---
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

        # --- Company Stats ---
        st.markdown("### 🏢 Company Statistics")
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            stats = {
                "Market Cap": info.get("marketCap", "N/A"),
                "P/E Ratio": info.get("trailingPE", "N/A"),
                "Dividend Yield": f"{round(info.get('dividendYield', 0), 2)}%" if info.get('dividendYield') else "N/A",
                "52-Week High": info.get("fiftyTwoWeekHigh", "N/A"),
                "52-Week Low": info.get("fiftyTwoWeekLow", "N/A"),
                "Sector": info.get("sector", "N/A"),
                "Industry": info.get("industry", "N/A")
            }

            for k, v in stats.items():
                st.write(f"**{k}:** {v}")

        except Exception as e:
            st.error(f"Could not load company stats: {e}")
