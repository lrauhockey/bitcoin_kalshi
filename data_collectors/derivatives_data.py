
import requests
from datetime import datetime, timezone

OKX_BASE_URL = "https://www.okx.com"


def get_funding_rate():
    """
    Fetches the current BTC-USDT perpetual funding rate from OKX.
    Returns dict with current rate, next funding time, and recent history.
    """
    result = {
        'current_rate': None,
        'next_funding_time': None,
        'recent_rates': [],
    }

    # Current funding rate
    try:
        r = requests.get(
            f"{OKX_BASE_URL}/api/v5/public/funding-rate",
            params={'instId': 'BTC-USDT-SWAP'},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        if data.get('data'):
            item = data['data'][0]
            result['current_rate'] = float(item['fundingRate'])
            result['next_funding_time'] = int(item['fundingTime'])
    except Exception as e:
        print(f"Error fetching current funding rate: {e}")

    # Recent funding rate history (last 10 settlements)
    try:
        r = requests.get(
            f"{OKX_BASE_URL}/api/v5/public/funding-rate-history",
            params={'instId': 'BTC-USDT-SWAP', 'limit': '10'},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        if data.get('data'):
            for item in data['data']:
                result['recent_rates'].append({
                    'rate': float(item['fundingRate']),
                    'time': int(item['fundingTime']),
                })
    except Exception as e:
        print(f"Error fetching funding rate history: {e}")

    return result


def get_open_interest():
    """
    Fetches the current BTC-USDT-SWAP open interest from OKX.
    Returns dict with OI in contracts and in BTC.
    """
    try:
        r = requests.get(
            f"{OKX_BASE_URL}/api/v5/public/open-interest",
            params={'instType': 'SWAP', 'instId': 'BTC-USDT-SWAP'},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        if data.get('data'):
            item = data['data'][0]
            return {
                'oi_contracts': float(item['oi']),
                'oi_btc': float(item['oiCcy']),
                'timestamp': int(item['ts']),
            }
    except Exception as e:
        print(f"Error fetching open interest: {e}")
    return None


def get_long_short_ratio():
    """
    Fetches the BTC long/short account ratio from OKX (hourly).
    A ratio > 1 means more accounts are long. < 1 means more short.
    Returns the most recent ratio and a short history.
    """
    try:
        r = requests.get(
            f"{OKX_BASE_URL}/api/v5/rubik/stat/contracts/long-short-account-ratio",
            params={'ccy': 'BTC', 'period': '1H'},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        if data.get('data'):
            history = []
            for item in data['data'][:12]:  # Last 12 hours
                history.append({
                    'timestamp': int(item[0]),
                    'ratio': float(item[1]),
                })
            return {
                'current_ratio': history[0]['ratio'] if history else None,
                'history': history,
            }
    except Exception as e:
        print(f"Error fetching long/short ratio: {e}")
    return None


def get_recent_liquidations():
    """
    Fetches recent BTC-USDT liquidation orders from OKX.
    Returns aggregated long/short liquidation volumes and individual events.
    """
    try:
        r = requests.get(
            f"{OKX_BASE_URL}/api/v5/public/liquidation-orders",
            params={
                'instType': 'SWAP',
                'uly': 'BTC-USDT',
                'state': 'filled',
            },
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        long_liqs = 0.0
        short_liqs = 0.0
        long_count = 0
        short_count = 0
        events = []

        if data.get('data'):
            for batch in data['data']:
                for detail in batch.get('details', []):
                    price = float(detail['bkPx'])
                    size = float(detail['sz'])
                    value_usd = price * size
                    pos_side = detail.get('posSide', '')

                    if pos_side == 'long':
                        long_liqs += value_usd
                        long_count += 1
                    elif pos_side == 'short':
                        short_liqs += value_usd
                        short_count += 1

                    events.append({
                        'side': pos_side,
                        'price': price,
                        'size_btc': size,
                        'value_usd': value_usd,
                        'time': int(detail['ts']),
                    })

        return {
            'long_liquidation_usd': long_liqs,
            'short_liquidation_usd': short_liqs,
            'long_count': long_count,
            'short_count': short_count,
            'total_usd': long_liqs + short_liqs,
            'recent_events': sorted(events, key=lambda x: x['time'], reverse=True)[:20],
        }
    except Exception as e:
        print(f"Error fetching liquidations: {e}")
    return None


def get_all_derivatives_data():
    """Fetches all derivatives data in one call. Returns a combined dict."""
    return {
        'funding': get_funding_rate(),
        'open_interest': get_open_interest(),
        'long_short_ratio': get_long_short_ratio(),
        'liquidations': get_recent_liquidations(),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("DERIVATIVES DATA (OKX - BTC-USDT-SWAP)")
    print("=" * 60)

    print("\n--- Funding Rate ---")
    funding = get_funding_rate()
    if funding['current_rate'] is not None:
        rate_pct = funding['current_rate'] * 100
        print(f"Current Rate: {rate_pct:.4f}%")
        next_time = datetime.fromtimestamp(
            funding['next_funding_time'] / 1000, tz=timezone.utc
        )
        print(f"Next Settlement: {next_time.strftime('%Y-%m-%d %H:%M UTC')}")
        if funding['recent_rates']:
            avg = sum(r['rate'] for r in funding['recent_rates']) / len(funding['recent_rates'])
            print(f"Avg Rate (last {len(funding['recent_rates'])} settlements): {avg*100:.4f}%")
    else:
        print("Failed to fetch funding rate.")

    print("\n--- Open Interest ---")
    oi = get_open_interest()
    if oi:
        print(f"OI: {oi['oi_btc']:.2f} BTC ({oi['oi_contracts']:,.0f} contracts)")
    else:
        print("Failed to fetch open interest.")

    print("\n--- Long/Short Ratio ---")
    ls = get_long_short_ratio()
    if ls and ls['current_ratio']:
        ratio = ls['current_ratio']
        long_pct = ratio / (1 + ratio) * 100
        short_pct = 100 - long_pct
        print(f"Ratio: {ratio:.2f} (Longs: {long_pct:.1f}%, Shorts: {short_pct:.1f}%)")
    else:
        print("Failed to fetch long/short ratio.")

    print("\n--- Recent Liquidations ---")
    liqs = get_recent_liquidations()
    if liqs:
        print(f"Long Liqs:  ${liqs['long_liquidation_usd']:>12,.2f} ({liqs['long_count']} events)")
        print(f"Short Liqs: ${liqs['short_liquidation_usd']:>12,.2f} ({liqs['short_count']} events)")
        print(f"Total:      ${liqs['total_usd']:>12,.2f}")
        if liqs['recent_events']:
            print(f"\nLast 5 liquidations:")
            for ev in liqs['recent_events'][:5]:
                t = datetime.fromtimestamp(ev['time'] / 1000, tz=timezone.utc)
                print(f"  {ev['side']:5s} | {ev['size_btc']:.2f} BTC @ ${ev['price']:,.1f} (${ev['value_usd']:,.0f}) | {t.strftime('%H:%M:%S')}")
    else:
        print("Failed to fetch liquidations.")
