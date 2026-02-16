# Project Tasks: Bitcoin Trading Dashboard

## Phase 1: Research & Setup
- [x] Analyze `article.txt` for strategy details (Completed).
- [x] Identify data sources (Completed: Polymarket, Binance, CryptoPanic).
- [ ] Create Python virtual environment.
- [ ] Install necessary libraries: `flask`, `ccxt`, `requests`, `py-clob-client`.
- [ ] Verify API access for:
    - [ ] Polymarket (Public market data).
    - [ ] Binance (Public market data).
    - [ ] CryptoPanic (Get free API Key).

## Phase 2: Data Ingestion Layers
### 2.1 Market Data (Price & Order Book)
- [ ] Create `market_data.py` module.
- [ ] Implement function to fetch current Bitcoin price.
- [ ] Implement function to fetch Order Book depth (top 20 bids/asks).
- [ ] Calculate "Wall Strength" (volume at key levels).

### 2.2 Funding & Liquidations
- [ ] Create `derivatives_data.py` module.
- [ ] Fetch current Funding Rate for BTC-USDT Perpetual.
- [ ] Fetch recent Liquidation data (24h aggregated volume).
- [ ] *Optional*: Visualize liquidation trends via simple moving average.

### 2.3 News & Sentiment
- [ ] Create `news_data.py` module.
- [ ] Integrate CryptoPanic API to fetch latest 5-10 headlines.
- [ ] Implement basic sentiment analysis (e.g., using `TextBlob` or keyword matching: "hack", "ban", "ETF approval").

### 2.4 Polymarket Integration
- [ ] Create `polymarket_data.py` module.
- [ ] Fetch active 15-min Bitcoin markets.
- [ ] Parse current odds for "Yes" and "No" outcomes.

## Phase 3: Backend Logic (Flask)
- [ ] Create `app.py`.
- [ ] Define data models/structures for the dashboard.
- [ ] Create `/api/dashboard-data` endpoint that aggregates all sources.
- [ ] Implement caching mechanism (simple in-memory or Redis) to avoid rate limits (e.g., update every 30s).

## Phase 4: Frontend Dashboard
- [ ] Create `templates/index.html`.
- [ ] Design layout with CSS Grid/Flexbox.
- [ ] Implement charts for:
    - Price trend (Sparkline or Candle).
    - Order Book Depth (Bar chart).
    - Liquidation/Funding Gauge.
- [ ] displaying the derived "Signal" based on strategy rules.

## Phase 5: Testing & Validation
- [ ] Verify data accuracy against live exchange data.
- [ ] Test strategy logic with historical scenarios (if possible) or live dry-run.
- [ ] User Acceptance Testing (UAT).
