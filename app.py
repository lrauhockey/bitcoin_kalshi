
import json
import time
import threading
from collections import deque
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler

from signal_engine import run_full_analysis

app = Flask(__name__)

# --- In-memory cache ---
_cache = {
    'dashboard_data': None,
    'last_updated': 0,
}
_cache_lock = threading.Lock()

# --- Signal history (last 50 signals) ---
MAX_SIGNAL_HISTORY = 50
_signal_history = deque(maxlen=MAX_SIGNAL_HISTORY)
_history_lock = threading.Lock()

REFRESH_INTERVAL_SECONDS = 45


def refresh_data():
    """Background job: fetch all data and update cache."""
    try:
        print(f"[{time.strftime('%H:%M:%S')}] Refreshing dashboard data...")
        analysis = run_full_analysis()

        # Make the analysis JSON-serializable
        dashboard = serialize_analysis(analysis)

        with _cache_lock:
            _cache['dashboard_data'] = dashboard
            _cache['last_updated'] = time.time()

        # Record signal history
        with _history_lock:
            _signal_history.append({
                'timestamp': dashboard['timestamp'],
                'btc_price': dashboard.get('btc_price'),
                'direction': dashboard.get('final_signal', {}).get('direction'),
                'confidence': dashboard.get('final_signal', {}).get('confidence'),
                'weighted_score': dashboard.get('final_signal', {}).get('weighted_score'),
                'signals': {
                    k: v['signal']
                    for k, v in dashboard.get('signals', {}).items()
                },
            })

        print(f"[{time.strftime('%H:%M:%S')}] Dashboard data refreshed.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error refreshing data: {e}")


def serialize_analysis(analysis):
    """Convert analysis result to a JSON-friendly dict."""
    data = {
        'timestamp': analysis['timestamp'],
        'btc_price': analysis['btc_price'],
        'wall_strength': analysis['wall_strength'],
        'signals': {},
        'final_signal': analysis['final_signal'],
        'odds_value': analysis['odds_value'],
    }

    # Signals
    for name, signal in analysis['signals'].items():
        data['signals'][name] = signal

    # Derivatives summary
    deriv = analysis.get('derivatives', {})
    if deriv:
        data['derivatives'] = {
            'funding': deriv.get('funding'),
            'open_interest': deriv.get('open_interest'),
            'long_short_ratio': deriv.get('long_short_ratio'),
            'liquidations': _serialize_liquidations(deriv.get('liquidations')),
        }

    # Polymarket
    pm = analysis.get('polymarket')
    if pm:
        data['polymarket'] = pm

    # News (just headlines, not full body)
    news = analysis.get('news_summary')
    if news:
        data['news'] = {
            'overall_sentiment': news['overall_sentiment'],
            'avg_score': news['avg_score'],
            'bullish_count': news['bullish_count'],
            'bearish_count': news['bearish_count'],
            'neutral_count': news['neutral_count'],
            'headlines': [
                {
                    'title': h['title'],
                    'source': h['source'],
                    'published_at': h['published_at'],
                    'url': h['url'],
                    'sentiment': h['sentiment'],
                }
                for h in news.get('headlines', [])[:10]
            ],
        }

    return data


def _serialize_liquidations(liqs):
    """Trim liquidation events for API response."""
    if not liqs:
        return None
    return {
        'long_liquidation_usd': liqs['long_liquidation_usd'],
        'short_liquidation_usd': liqs['short_liquidation_usd'],
        'long_count': liqs['long_count'],
        'short_count': liqs['short_count'],
        'total_usd': liqs['total_usd'],
        'recent_events': liqs.get('recent_events', [])[:10],
    }


# --- API Routes ---

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """Returns the full dashboard state including all signals and data."""
    with _cache_lock:
        data = _cache['dashboard_data']
        last_updated = _cache['last_updated']

    if data is None:
        return jsonify({'error': 'Data not yet available. Please wait for first refresh.'}), 503

    return jsonify({
        'data': data,
        'cache_age_seconds': round(time.time() - last_updated, 1),
    })


@app.route('/api/signal')
def api_signal():
    """Returns just the current signal recommendation."""
    with _cache_lock:
        data = _cache['dashboard_data']

    if data is None:
        return jsonify({'error': 'Data not yet available.'}), 503

    return jsonify({
        'btc_price': data.get('btc_price'),
        'final_signal': data.get('final_signal'),
        'odds_value': data.get('odds_value'),
        'signals': data.get('signals'),
    })


@app.route('/api/news')
def api_news():
    """Returns the latest news headlines and sentiment."""
    with _cache_lock:
        data = _cache['dashboard_data']

    if data is None:
        return jsonify({'error': 'Data not yet available.'}), 503

    return jsonify(data.get('news', {}))


@app.route('/api/derivatives')
def api_derivatives():
    """Returns derivatives data (funding, OI, L/S ratio, liquidations)."""
    with _cache_lock:
        data = _cache['dashboard_data']

    if data is None:
        return jsonify({'error': 'Data not yet available.'}), 503

    return jsonify(data.get('derivatives', {}))


@app.route('/api/polymarket')
def api_polymarket():
    """Returns current Polymarket market context."""
    with _cache_lock:
        data = _cache['dashboard_data']

    if data is None:
        return jsonify({'error': 'Data not yet available.'}), 503

    return jsonify(data.get('polymarket', {}))


@app.route('/api/signal-history')
def api_signal_history():
    """Returns the history of recent signals."""
    with _history_lock:
        history = list(_signal_history)
    return jsonify({'history': history, 'count': len(history)})


@app.route('/api/bet-suggestion')
def api_bet_suggestion():
    """
    Returns the final output for a bet suggestion,
    including up/down attribute counts and current Polymarket line.
    """
    with _cache_lock:
        data = _cache['dashboard_data']

    if data is None:
        return jsonify({'error': 'Data not yet available. Please wait for first refresh.'}), 503

    up_attributes = 0
    down_attributes = 0
    signals = data.get('signals', {})
    for signal_name, signal_data in signals.items():
        if signal_data.get('signal') == 'UP':
            up_attributes += 1
        elif signal_data.get('signal') == 'DOWN':
            down_attributes += 1

    return jsonify({
        'final_signal': data.get('final_signal'),
        'up_attributes_count': up_attributes,
        'down_attributes_count': down_attributes,
        'polymarket_line': data.get('polymarket'),
        'timestamp': data.get('timestamp')
    })


@app.route('/')
def index():
    """Serve the dashboard frontend."""
    return render_template('index.html')


@app.route('/api/health')
def health():
    """Health check endpoint."""
    with _cache_lock:
        last = _cache['last_updated']
    return jsonify({
        'status': 'ok',
        'last_updated': last,
        'cache_age_seconds': round(time.time() - last, 1) if last > 0 else None,
    })


# --- Scheduler Setup ---

def start_scheduler():
    """Start the background scheduler for periodic data refresh."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        refresh_data,
        'interval',
        seconds=REFRESH_INTERVAL_SECONDS,
        id='refresh_dashboard',
        max_instances=1,
    )
    scheduler.start()
    # Do an immediate first refresh
    refresh_data()


if __name__ == '__main__':
    start_scheduler()
    app.run(debug=False, host='0.0.0.0', port=5124)
