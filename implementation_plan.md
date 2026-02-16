# Bitcoin Trading Dashboard Plan - "The Ascetic0x Strategy"

## 1. Objective
Build a real-time dashboard that aggregates specific data points used by the trader "ascetic0x" to trade 15-minute Bitcoin Up/Down markets on Polymarket. The app will visualize:
- Polymarket Odds
- Bitcoin Order Book (Bid/Ask Walls)
- Funding Rates
- Liquidation Data
- Breaking News

## 2. Architecture
- **Backend**: Python (Flask)
- **Data Fetching**: Custom Python modules using `ccxt` and specific APIs.
- **Frontend**: HTML/JS (Vanilla or simple framework) with real-time charts.
- **Update Frequency**: Real-time or 1-minute intervals (matching the high-frequency nature of 15-minute bets).

## 3. Data Sources & Tech Stack

| Data Point | Source | Tool/Library | Notes |
| :--- | :--- | :--- | :--- |
| **Bitcoin Price** | Binance / Coinbase | `ccxt` (Python) | 1-min candles (OHLCV) |
| **Order Book** | Binance / Coinbase | `ccxt` | Depth L2, visualize walls |
| **Funding Rates** | Binance Futures | `ccxt` | Proxy for market overcrowding |
| **Liquidations** | Binance Futures (Stream) | `websocket-client` | Real-time liquidation events |
| **News** | CryptoPanic | `requests` (API) | Filter for "hot" or breaking news |
| **Polymarket Odds** | Polymarket API | `py-clob-client` | Fetch "Yes" price for current BTC market |
| **Sentiment** | (Derived from News) | NLP (NLTK/TextBlob) | Simple sentiment score on headlines |

## 4. Implementation Steps

### Phase 1: Data Connectors (Python)
- [ ] **Setup**: Initialize Flask project and virtual environment.
- [ ] **Polymarket Module**: Connect to Polymarket to find the *current* active 15-min BTC market and get Share Prices (odds).
- [ ] **Market Data Module**: Use `ccxt` to fetch:
    - Current BTC/USDT price.
    - Order Book (Bids/Asks) -> Calculate "Wall" strength (e.g., sum volume at +/- 1% range).
    - Funding Rate (current predicted rate).
- [ ] **Liquidation Module**: Connect to Binance WebSocket to listen for liquidation events and aggregate them (e.g., "Last 24h Short Liqs").
- [ ] **News Module**: Poll CryptoPanic API for the latest 5 news items.

### Phase 2: Logic & "Signal" Engine
- [ ] **Aggregation**: Combine all data into a single state object.
- [ ] **Signal Calculation**: Implement the checklist from the article:
    - `IF Funding > High_Threshold AND Ask_Wall > Bid_Wall -> Bearish`
    - `IF Liquidation_Shorts > Liquidation_Longs (Significant) -> Bearish (Squeeze over)`
    - *Note: Logic will need fine-tuning based on the specific "rules" in the text.*

### Phase 3: Flask Layer
- [ ] Create API endpoints:
    - `/api/status`: Returns current price, odds, walls, funding, signal.
    - `/api/news`: Returns latest news.
- [ ] Implement a background scheduler (or async loop) to keep data fresh without blocking HTTP requests.

### Phase 4: Frontend Dashboard
- [ ] **Layout**:
    - **Top**: BTC Price (Live), Polymarket Odds (Yes/No).
    - **Middle Left**: Order Book Visualization (Bid/Ask Walls).
    - **Middle Right**: Funding Rate Gauge & Liquidation Bar Chart.
    - **Bottom**: News Feed ticker.
- [ ] **Tech**: HTML5, CSS (Grid/Flexbox), Chart.js (for visualization).

## 5. Prerequisities
- Python 3.9+
- API Keys:
    - CryptoPanic (Free tier available)
    - Polymarket (Public, but wallet needed for trading - we only need *reading* for now).
    - Binance/Coinbase (Public data usually doesn't need keys for basic rate limits).
