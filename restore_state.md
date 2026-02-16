# Project Restoration Point & Chat History

**Date**: 2026-02-12
**Project**: Bitcoin Trading Dashboard (Ascetic0x Strategy)
**Target Location**: `/Volumes/Crucial X9/myfolder/lrau/dev_bit/`

---

## Current State: PHASE 3 COMPLETE — All Core Features Built

**Phases 1-3 are complete.** The dashboard is fully functional with live data, signal engine, Chart.js visualizations, signal history tracking, and a polished responsive UI.

---

### Phase 1 — Data Connectors
1.  `data_collectors/market_data.py` — Kraken: BTC price, order book, wall strength
2.  `data_collectors/polymarket_data.py` — Polymarket Gamma API + CLOB: market discovery, odds, order book
3.  `data_collectors/derivatives_data.py` — OKX Public API: funding rate, OI, L/S ratio, liquidations
4.  `data_collectors/news_data.py` — CryptoCompare + TextBlob: headlines + sentiment

### Phase 2 — Signal Engine + Flask Backend
5.  `signal_engine.py` — 5-signal weighted analysis (funding, liquidations, order book, L/S ratio, news). Produces UP/DOWN/SKIP with confidence score.
6.  `app.py` — Flask app on port 5124. Background scheduler (45s refresh). Thread-safe cache. Signal history deque (last 50).
    *   Endpoints: `/`, `/api/dashboard-data`, `/api/signal`, `/api/signal-history`, `/api/news`, `/api/derivatives`, `/api/polymarket`, `/api/health`

### Phase 3 — Frontend + Visualizations
7.  `templates/index.html` — Full dashboard overhaul:
    *   **Sticky header**: ASCETIC0x logo + live BTC price + connection status indicator
    *   **Signal hero**: Large UP/DOWN/SKIP badge + confidence + Polymarket odds + odds value callout
    *   **Signal breakdown**: Color-coded rows with dot indicators + detail text + labels
    *   **Derivatives card**: Funding rate (color-coded by extremes), OI, L/S ratio + **Chart.js bar chart** of funding rate history (last 10 settlements)
    *   **Order book card**: Bid/ask wall volumes + ratio + **Chart.js horizontal bar chart** (green bids vs red asks)
    *   **Liquidations card**: Gradient progress bar (long vs short %) + data rows + **Chart.js doughnut chart** with legend
    *   **Signal history card**: Mini timeline of colored bars (green=UP, red=DOWN, gray=SKIP, height=confidence) + **Chart.js line chart** of BTC price over time with signal-colored dots
    *   **News feed**: 2-column grid with colored left borders (green/red/gray by sentiment), clickable headlines, source + time
    *   **Responsive**: 3-column > 2-column > 1-column breakpoints
    *   **Loading state**: Spinner with "first refresh" message
    *   **Auto-refresh**: Polls API every 8 seconds

### Codebase Structure
```
dev_bit/
  app.py                        # Flask app + scheduler (port 5124)
  signal_engine.py              # Signal analysis engine
  .env                          # API keys
  requirements.txt              # Python dependencies
  venv/                         # Virtual environment
  data_collectors/
    __init__.py
    market_data.py              # Kraken: BTC price + order book + wall strength
    polymarket_data.py          # Polymarket: market discovery + odds + order book
    derivatives_data.py         # OKX: funding rate + OI + long/short + liquidations
    news_data.py                # CryptoCompare: news headlines + sentiment
  templates/
    index.html                  # Dashboard frontend (Chart.js + responsive)
  implementation_plan.md        # Original architecture plan
  tasks.md                      # Task checklist
  article.txt                   # Source article on ascetic0x strategy
  restore_state.md              # This file
```

### API Sources Summary
| Data Point | Source | Auth | Status |
|:---|:---|:---|:---|
| BTC Price + Order Book | Kraken (ccxt) | No | Working |
| Polymarket Odds | Gamma API + CLOB | No | Working |
| Funding Rate | OKX Public | No | Working |
| Open Interest | OKX Public | No | Working |
| Long/Short Ratio | OKX Public | No | Working |
| Liquidations | OKX Public | No | Working |
| News Headlines | CryptoCompare | No | Working |
| Sentiment | TextBlob + Keywords | N/A | Working |

---

## How to Run
```bash
cd /Volumes/Crucial\ X9/myfolder/lrau/dev_bit
source venv/bin/activate
python app.py
# Open http://localhost:5124
```

---

### Possible Future Enhancements
1.  **15-min market auto-detection**: Better filtering for exact active window on Polymarket
2.  **Configurable thresholds**: Tune signal thresholds from the UI
3.  **WebSocket/SSE**: Replace polling with push updates
4.  **Persistent signal history**: Save to SQLite/JSON file
5.  **Backtesting**: Compare past signals against actual outcomes
6.  **Sound/browser alerts**: Notify when strong signal appears
7.  **Mobile optimization**: Further responsive tweaks

---

## Resume Prompt
> **I am restarting our session on the Bitcoin Trading Dashboard. Phases 1-3 are COMPLETE — data connectors, signal engine, Flask backend, and polished Chart.js frontend all working. The app runs on port 5124. Please read `restore_state.md` for full context.**

---

## Technical Notes
*   **Port**: 5124 (5000 taken by macOS AirPlay)
*   **Geo-restrictions**: Binance (451) and Bybit (403) blocked. Using Kraken + OKX.
*   **CryptoPanic**: API down (404). Using CryptoCompare instead.
*   **Polymarket**: `clobTokenIds`/`outcomes` are JSON strings — must `json.loads()`.
*   **OKX**: `ccy='BTC'` for L/S ratio, `instId='BTC-USDT-SWAP'` for funding/OI.
*   **Signal weights**: Funding & liquidations 1.5x, order book 1.0x, L/S ratio & news 0.5x.
*   **Signal history**: In-memory deque (max 50). Resets on server restart.
*   **Chart.js**: Loaded from CDN v4.4.7. Charts destroyed and recreated each render cycle.
