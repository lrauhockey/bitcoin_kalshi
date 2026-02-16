
import requests
from datetime import datetime, timezone
from textblob import TextBlob

CRYPTOCOMPARE_NEWS_URL = "https://min-api.cryptocompare.com/data/v2/news/"

# Keywords that signal high-impact news for short-term BTC trading
BULLISH_KEYWORDS = [
    'etf approved', 'etf approval', 'institutional', 'adoption',
    'bullish', 'rally', 'surge', 'breakout', 'all-time high', 'ath',
    'accumulation', 'buying', 'inflow',
]
BEARISH_KEYWORDS = [
    'hack', 'hacked', 'exploit', 'ban', 'banned', 'crackdown',
    'bearish', 'crash', 'plunge', 'dump', 'sell-off', 'selloff',
    'liquidation', 'outflow', 'sec', 'lawsuit', 'fraud',
]


def get_btc_news(limit=10):
    """
    Fetches latest BTC-related news from CryptoCompare (free, no key required).
    Returns list of news items with title, source, time, url, and sentiment.
    """
    try:
        r = requests.get(
            CRYPTOCOMPARE_NEWS_URL,
            params={
                'categories': 'BTC',
                'lang': 'EN',
                'sortOrder': 'latest',
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        if not data.get('Data'):
            return []

        news_items = []
        for item in data['Data'][:limit]:
            title = item.get('title', '')
            body = item.get('body', '')
            sentiment = analyze_sentiment(title, body)

            news_items.append({
                'title': title,
                'source': item.get('source_info', {}).get('name', item.get('source', 'Unknown')),
                'published_at': int(item.get('published_on', 0)),
                'url': item.get('url', ''),
                'categories': item.get('categories', ''),
                'sentiment': sentiment,
            })

        return news_items
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


def analyze_sentiment(title, body=""):
    """
    Analyzes sentiment of a news headline using TextBlob + keyword matching.
    Returns dict with polarity score and label (bullish/bearish/neutral).
    """
    text = f"{title} {body[:200]}".lower()

    # TextBlob polarity: -1 (negative) to +1 (positive)
    blob = TextBlob(title)
    polarity = blob.sentiment.polarity

    # Keyword boost
    bullish_hits = sum(1 for kw in BULLISH_KEYWORDS if kw in text)
    bearish_hits = sum(1 for kw in BEARISH_KEYWORDS if kw in text)

    keyword_score = (bullish_hits - bearish_hits) * 0.2
    combined_score = polarity + keyword_score

    # Clamp to [-1, 1]
    combined_score = max(-1.0, min(1.0, combined_score))

    if combined_score > 0.1:
        label = 'bullish'
    elif combined_score < -0.1:
        label = 'bearish'
    else:
        label = 'neutral'

    return {
        'score': round(combined_score, 3),
        'label': label,
        'polarity': round(polarity, 3),
        'bullish_keywords': bullish_hits,
        'bearish_keywords': bearish_hits,
    }


def get_news_summary():
    """
    Returns a summary of current news sentiment.
    Useful for the signal engine.
    """
    news = get_btc_news(limit=10)
    if not news:
        return None

    scores = [n['sentiment']['score'] for n in news]
    avg_score = sum(scores) / len(scores)
    bullish_count = sum(1 for n in news if n['sentiment']['label'] == 'bullish')
    bearish_count = sum(1 for n in news if n['sentiment']['label'] == 'bearish')
    neutral_count = sum(1 for n in news if n['sentiment']['label'] == 'neutral')

    if avg_score > 0.1:
        overall = 'bullish'
    elif avg_score < -0.1:
        overall = 'bearish'
    else:
        overall = 'neutral'

    return {
        'overall_sentiment': overall,
        'avg_score': round(avg_score, 3),
        'bullish_count': bullish_count,
        'bearish_count': bearish_count,
        'neutral_count': neutral_count,
        'headlines': news,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("BTC NEWS & SENTIMENT (CryptoCompare)")
    print("=" * 60)

    news = get_btc_news(limit=10)
    print(f"\nFetched {len(news)} headlines:\n")

    for i, item in enumerate(news, 1):
        t = datetime.fromtimestamp(item['published_at'], tz=timezone.utc)
        s = item['sentiment']
        indicator = {'bullish': '+', 'bearish': '-', 'neutral': '~'}[s['label']]
        print(f"  {i:2d}. [{indicator}] {item['title'][:80]}")
        print(f"      Source: {item['source']} | {t.strftime('%H:%M UTC')} | Score: {s['score']}")
        print()

    print("-" * 60)
    summary = get_news_summary()
    if summary:
        print(f"Overall Sentiment: {summary['overall_sentiment'].upper()} (avg: {summary['avg_score']})")
        print(f"Bullish: {summary['bullish_count']} | Neutral: {summary['neutral_count']} | Bearish: {summary['bearish_count']}")
