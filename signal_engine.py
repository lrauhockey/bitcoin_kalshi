
import time
from data_collectors.market_data import get_btc_price, get_order_book, calculate_wall_strength
from data_collectors.polymarket_data import get_active_btc_markets, extract_token_ids, get_market_prices
from data_collectors.derivatives_data import get_all_derivatives_data
from data_collectors.news_data import get_news_summary

# --- Thresholds (tunable) ---
# Funding rate: annualized thresholds for "extreme"
# OKX returns per-8h rate. E.g. 0.01% per 8h = 0.0001
FUNDING_HIGH_THRESHOLD = 0.0001    # 0.01% per 8h — longs crowded
FUNDING_LOW_THRESHOLD = -0.0001    # -0.01% per 8h — shorts crowded

# Liquidation ratio: if one side is X times the other, it's "dominant"
LIQ_DOMINANCE_RATIO = 1.5

# Order book wall ratio thresholds
WALL_BID_STRONG = 1.3    # bid volume > 1.3x ask volume = bid wall dominant
WALL_ASK_STRONG = 0.77   # bid volume < 0.77x ask volume = ask wall dominant (inverse of 1.3)

# Polymarket max share price for "decent odds"
MAX_SHARE_PRICE = 0.55

# Minimum signals needed to generate a non-SKIP signal
MIN_ALIGNED_SIGNALS = 2


def analyze_funding(derivatives_data):
    """
    Analyze funding rate signal.
    High positive → longs crowded → bearish
    High negative → shorts crowded → bullish
    """
    funding = derivatives_data.get('funding', {})
    rate = funding.get('current_rate')
    if rate is None:
        return {'signal': 'neutral', 'score': 0, 'detail': 'No funding data'}

    if rate >= FUNDING_HIGH_THRESHOLD:
        strength = min(1.0, rate / (FUNDING_HIGH_THRESHOLD * 3))
        return {
            'signal': 'bearish',
            'score': -strength,
            'detail': f'Funding {rate*100:.4f}% — longs crowded, risk of pullback',
        }
    elif rate <= FUNDING_LOW_THRESHOLD:
        strength = min(1.0, abs(rate) / (abs(FUNDING_LOW_THRESHOLD) * 3))
        return {
            'signal': 'bullish',
            'score': strength,
            'detail': f'Funding {rate*100:.4f}% — shorts crowded, risk of squeeze up',
        }
    else:
        return {
            'signal': 'neutral',
            'score': 0,
            'detail': f'Funding {rate*100:.4f}% — within normal range',
        }


def analyze_liquidations(derivatives_data):
    """
    Analyze liquidation data.
    Short liqs >> long liqs → shorts already squeezed → fuel exhausted → bearish
    Long liqs >> short liqs → longs already flushed → selling done → bullish
    """
    liqs = derivatives_data.get('liquidations')
    if not liqs:
        return {'signal': 'neutral', 'score': 0, 'detail': 'No liquidation data'}

    long_usd = liqs['long_liquidation_usd']
    short_usd = liqs['short_liquidation_usd']
    total = liqs['total_usd']

    if total == 0:
        return {'signal': 'neutral', 'score': 0, 'detail': 'No recent liquidations'}

    # Ratio of dominant side
    if short_usd > 0 and long_usd / short_usd >= LIQ_DOMINANCE_RATIO:
        # Longs flushed → selling pressure exhausted → likely bounce
        ratio = long_usd / short_usd
        strength = min(1.0, (ratio - 1) / 3)
        return {
            'signal': 'bullish',
            'score': strength,
            'detail': f'Long liqs ${long_usd:,.0f} vs short ${short_usd:,.0f} '
                       f'(ratio {ratio:.1f}x) — longs flushed, bounce likely',
        }
    elif long_usd > 0 and short_usd / long_usd >= LIQ_DOMINANCE_RATIO:
        # Shorts squeezed → upside fuel exhausted → likely pullback
        ratio = short_usd / long_usd
        strength = min(1.0, (ratio - 1) / 3)
        return {
            'signal': 'bearish',
            'score': -strength,
            'detail': f'Short liqs ${short_usd:,.0f} vs long ${long_usd:,.0f} '
                       f'(ratio {ratio:.1f}x) — shorts squeezed, pullback likely',
        }
    else:
        return {
            'signal': 'neutral',
            'score': 0,
            'detail': f'Liquidations balanced — long ${long_usd:,.0f} vs short ${short_usd:,.0f}',
        }


def analyze_order_book(wall_data):
    """
    Analyze order book walls.
    Strong bid wall (high ratio) → support below → bullish
    Strong ask wall (low ratio) → resistance above → bearish
    """
    if not wall_data:
        return {'signal': 'neutral', 'score': 0, 'detail': 'No order book data'}

    ratio = wall_data['wall_ratio']
    bid_vol = wall_data['bid_wall_volume']
    ask_vol = wall_data['ask_wall_volume']

    if ratio >= WALL_BID_STRONG:
        strength = min(1.0, (ratio - 1) / 2)
        return {
            'signal': 'bullish',
            'score': strength,
            'detail': f'Bid wall dominant — bids {bid_vol:.2f} vs asks {ask_vol:.2f} '
                       f'(ratio {ratio:.2f}) — support below',
        }
    elif ratio <= WALL_ASK_STRONG:
        strength = min(1.0, (1 - ratio) / 0.5)
        return {
            'signal': 'bearish',
            'score': -strength,
            'detail': f'Ask wall dominant — bids {bid_vol:.2f} vs asks {ask_vol:.2f} '
                       f'(ratio {ratio:.2f}) — resistance above',
        }
    else:
        return {
            'signal': 'neutral',
            'score': 0,
            'detail': f'Walls balanced — ratio {ratio:.2f}',
        }


def analyze_news(news_summary):
    """
    Analyze news sentiment as a confirming/conflicting signal.
    """
    if not news_summary:
        return {'signal': 'neutral', 'score': 0, 'detail': 'No news data'}

    sentiment = news_summary['overall_sentiment']
    score = news_summary['avg_score']

    if sentiment == 'bullish':
        return {
            'signal': 'bullish',
            'score': score,
            'detail': f'News sentiment bullish (score: {score:.3f}) — '
                       f'{news_summary["bullish_count"]} bullish, '
                       f'{news_summary["bearish_count"]} bearish headlines',
        }
    elif sentiment == 'bearish':
        return {
            'signal': 'bearish',
            'score': score,
            'detail': f'News sentiment bearish (score: {score:.3f}) — '
                       f'{news_summary["bullish_count"]} bullish, '
                       f'{news_summary["bearish_count"]} bearish headlines',
        }
    else:
        return {
            'signal': 'neutral',
            'score': 0,
            'detail': f'News sentiment neutral (score: {score:.3f})',
        }


def analyze_long_short_ratio(derivatives_data):
    """
    Analyze long/short account ratio as a contrarian signal.
    Very high ratio → too many longs → bearish
    Very low ratio → too many shorts → bullish
    """
    ls = derivatives_data.get('long_short_ratio')
    if not ls or ls.get('current_ratio') is None:
        return {'signal': 'neutral', 'score': 0, 'detail': 'No long/short data'}

    ratio = ls['current_ratio']

    # Typical range is 0.5-3.0. Extremes beyond 2.5 or below 0.7 are notable.
    if ratio >= 2.5:
        strength = min(1.0, (ratio - 2.0) / 2.0)
        return {
            'signal': 'bearish',
            'score': -strength * 0.5,  # lower weight — confirming signal
            'detail': f'L/S ratio {ratio:.2f} — longs very crowded (contrarian bearish)',
        }
    elif ratio <= 0.7:
        strength = min(1.0, (1.0 - ratio) / 0.5)
        return {
            'signal': 'bullish',
            'score': strength * 0.5,
            'detail': f'L/S ratio {ratio:.2f} — shorts very crowded (contrarian bullish)',
        }
    else:
        return {
            'signal': 'neutral',
            'score': 0,
            'detail': f'L/S ratio {ratio:.2f} — within normal range',
        }


def generate_signal(signals_dict):
    """
    Combine all individual signals into a final recommendation.

    Core logic from the article:
      bid wall + negative funding + long liqs dominant → UP
      ask wall + positive funding + short liqs dominant → DOWN
      Signals contradicting or < MIN_ALIGNED_SIGNALS → SKIP
    """
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    total_score = 0.0

    # Weight each signal: funding & liquidations are primary, order book secondary, news confirming
    weights = {
        'funding': 1.5,
        'liquidations': 1.5,
        'order_book': 1.0,
        'long_short_ratio': 0.5,
        'news': 0.5,
    }

    for key, signal in signals_dict.items():
        w = weights.get(key, 1.0)
        direction = signal['signal']
        weighted_score = signal['score'] * w

        if direction == 'bullish':
            bullish_count += 1
        elif direction == 'bearish':
            bearish_count += 1
        else:
            neutral_count += 1

        total_score += weighted_score

    # Determine final signal
    if bullish_count >= MIN_ALIGNED_SIGNALS and bullish_count > bearish_count:
        direction = 'UP'
        confidence = min(1.0, total_score / 2.0)
    elif bearish_count >= MIN_ALIGNED_SIGNALS and bearish_count > bullish_count:
        direction = 'DOWN'
        confidence = min(1.0, abs(total_score) / 2.0)
    else:
        direction = 'SKIP'
        confidence = 0.0

    return {
        'direction': direction,
        'confidence': round(confidence, 3),
        'weighted_score': round(total_score, 3),
        'bullish_signals': bullish_count,
        'bearish_signals': bearish_count,
        'neutral_signals': neutral_count,
    }


def get_polymarket_context(markets):
    """Extract the best current market and its odds."""
    if not markets:
        return None

    market = markets[0]
    tokens = extract_token_ids(market)

    # Parse outcome prices
    import json
    prices_raw = market.get('outcomePrices', '[]')
    if isinstance(prices_raw, str):
        prices = json.loads(prices_raw)
    else:
        prices = prices_raw

    outcomes = {}
    for i, token_info in enumerate(tokens):
        price = float(prices[i]) if i < len(prices) else None
        outcomes[token_info['outcome']] = {
            'token_id': token_info['token_id'],
            'price': price,
        }

    return {
        'question': market.get('question'),
        'end_date': market.get('endDate'),
        'slug': market.get('slug'),
        'outcomes': outcomes,
    }


def check_odds_value(polymarket_context, direction):
    """
    Check if the Polymarket odds offer value based on our signal direction.
    Only bet when share price <= MAX_SHARE_PRICE.
    """
    if not polymarket_context:
        return {'has_value': False, 'detail': 'No Polymarket data'}

    outcomes = polymarket_context.get('outcomes', {})

    if direction == 'UP':
        target = outcomes.get('Up', {})
    elif direction == 'DOWN':
        target = outcomes.get('Down', {})
    else:
        return {'has_value': False, 'detail': 'Signal is SKIP — no bet'}

    price = target.get('price')
    if price is None:
        return {'has_value': False, 'detail': 'No price for target outcome'}

    if price <= MAX_SHARE_PRICE:
        payout = 1.0 / price
        return {
            'has_value': True,
            'share_price': price,
            'potential_payout': round(payout, 2),
            'detail': f'{direction} shares at ${price:.2f} → {payout:.2f}x payout if correct',
        }
    else:
        return {
            'has_value': False,
            'share_price': price,
            'detail': f'{direction} shares at ${price:.2f} — too expensive (max ${MAX_SHARE_PRICE})',
        }


def run_full_analysis():
    """
    Run the complete signal analysis pipeline.
    Fetches all data, analyzes each dimension, produces final signal.
    """
    result = {
        'timestamp': int(time.time()),
        'btc_price': None,
        'wall_strength': None,
        'derivatives': None,
        'polymarket': None,
        'news_summary': None,
        'signals': {},
        'final_signal': None,
        'odds_value': None,
    }

    # --- Fetch all data ---
    print("Fetching market data...")
    btc_price = get_btc_price()
    result['btc_price'] = btc_price

    order_book = get_order_book(limit=100)
    wall_strength = calculate_wall_strength(order_book) if order_book else None
    result['wall_strength'] = wall_strength

    print("Fetching derivatives data...")
    derivatives = get_all_derivatives_data()
    result['derivatives'] = derivatives

    print("Fetching Polymarket data...")
    markets = get_active_btc_markets()
    polymarket_ctx = get_polymarket_context(markets)
    result['polymarket'] = polymarket_ctx

    print("Fetching news...")
    news_summary = get_news_summary()
    result['news_summary'] = news_summary

    # --- Analyze each signal ---
    signals = {
        'funding': analyze_funding(derivatives),
        'liquidations': analyze_liquidations(derivatives),
        'order_book': analyze_order_book(wall_strength),
        'long_short_ratio': analyze_long_short_ratio(derivatives),
        'news': analyze_news(news_summary),
    }
    result['signals'] = signals

    # --- Generate final signal ---
    final = generate_signal(signals)
    result['final_signal'] = final

    # --- Check odds value ---
    odds = check_odds_value(polymarket_ctx, final['direction'])
    result['odds_value'] = odds

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("  ASCETIC0X SIGNAL ENGINE — Full Analysis")
    print("=" * 70)

    analysis = run_full_analysis()

    print(f"\n{'='*70}")
    print(f"  BTC Price: ${analysis['btc_price']:,.2f}" if analysis['btc_price'] else "  BTC Price: N/A")
    print(f"{'='*70}")

    print("\n--- Individual Signals ---")
    for name, signal in analysis['signals'].items():
        icon = {'bullish': '+', 'bearish': '-', 'neutral': '~'}[signal['signal']]
        print(f"  [{icon}] {name:20s}: {signal['detail']}")

    print(f"\n--- Final Signal ---")
    final = analysis['final_signal']
    print(f"  Direction:  {final['direction']}")
    print(f"  Confidence: {final['confidence']}")
    print(f"  Score:      {final['weighted_score']}")
    print(f"  Bullish/Bearish/Neutral signals: "
          f"{final['bullish_signals']}/{final['bearish_signals']}/{final['neutral_signals']}")

    if analysis['polymarket']:
        pm = analysis['polymarket']
        print(f"\n--- Polymarket ---")
        print(f"  Market: {pm['question']}")
        print(f"  Ends:   {pm['end_date']}")
        for outcome, data in pm['outcomes'].items():
            print(f"  {outcome}: ${data['price']:.2f}")

    odds = analysis['odds_value']
    print(f"\n--- Odds Value ---")
    print(f"  {odds['detail']}")
    if odds.get('has_value'):
        print(f"  Potential Payout: {odds['potential_payout']}x")

    print(f"\n{'='*70}")
    if final['direction'] != 'SKIP' and odds.get('has_value'):
        print(f"  >>> RECOMMENDATION: BET {final['direction']} "
              f"(confidence: {final['confidence']:.0%}) <<<")
    elif final['direction'] != 'SKIP':
        print(f"  >>> Signal is {final['direction']} but odds don't offer value — SKIP <<<")
    else:
        print(f"  >>> RECOMMENDATION: SKIP this window <<<")
    print(f"{'='*70}")
