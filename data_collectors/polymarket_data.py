
from py_clob_client.client import ClobClient
import requests
import json
from datetime import datetime, timezone

# Polymarket CLOB API URL
CLOB_API_URL = "https://clob.polymarket.com"
GAMMA_API_URL = "https://gamma-api.polymarket.com"

def get_polymarket_client():
    """
    Returns a ClobClient instance. 
    Note: For read-only public data, we might not need keys, 
    but the client might enforce them. If so, we'll use raw requests.
    """
    try:
        # constant_derivation=False is often needed for read-only or valid checks
        return ClobClient(host=CLOB_API_URL, chain_id=137) 
    except Exception as e:
        print(f"Error initializing ClobClient: {e}")
        return None

def get_active_btc_markets():
    """
    Fetches active Bitcoin markets, filtering for 15-min or high-frequency binary options.
    Uses the Gamma API (easier for discovery than CLOB API).
    """
    # First, let's try to find the tag ID for "Bitcoin" if possible, or just search broadly.
    # The Gamma API endpoint /events is often better for grouped markets.
    # But let's stick to /markets with a broader query.
    
    url = f"{GAMMA_API_URL}/markets"
    
    params = {
        "limit": 100,
        "active": "true",
        "closed": "false",
        "tag_slug": "bitcoin", # Try filtering by tag slug directly if supported
        "order": "volume24hr", # Order by volume to find popular ones
        "ascending": "false"
    }
    
    try:
        response = requests.get(url, params=params)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Gamma API Error: {e}")
            print(f"Response: {response.text[:200]}")
            return []
            
        markets = response.json()
        
        # If markets is a dict with 'data', extract it. Some APIs wrap the list.
        if isinstance(markets, dict) and 'data' in markets:
            markets = markets['data']
            
        # Filter for future markets
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        btc_markets = []
        for market in markets:
            question = market.get('question', '').lower()
            end_date_str = market.get('endDate')
            if end_date_str:
                # Handle ISO format Z (e.g. 2026-02-12T17:00:00Z)
                try:
                    end_date = datetime.strptime(end_date_str.replace('Z', ''), "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    continue # Skip if date format is weird
                
                if end_date < current_time:
                    continue # Skip past markets

            # Loose filter for Bitcoin related markets
            if 'btc' in question or 'bitcoin' in question:
                btc_markets.append(market)
                
        # Sort to prioritize "Up or Down"
        btc_markets.sort(key=lambda m: "up or down" not in m.get('question', '').lower())
        
        return btc_markets
    except Exception as e:
        print(f"General Error fetching markets: {e}")
        return []

def extract_token_ids(market):
    """
    Extracts clobTokenIds and outcomes from a market object.
    The Gamma API returns these as JSON strings, not lists.
    Returns list of dicts: [{'outcome': 'Up', 'token_id': '...'}, ...]
    """
    clob_ids_raw = market.get('clobTokenIds', '[]')
    if isinstance(clob_ids_raw, str):
        clob_ids = json.loads(clob_ids_raw)
    else:
        clob_ids = clob_ids_raw

    outcomes_raw = market.get('outcomes', '[]')
    if isinstance(outcomes_raw, str):
        outcomes = json.loads(outcomes_raw)
    else:
        outcomes = outcomes_raw

    result = []
    for i, tid in enumerate(clob_ids):
        outcome_label = outcomes[i] if i < len(outcomes) else f"Outcome {i}"
        result.append({'outcome': outcome_label, 'token_id': tid})
    return result


def get_market_prices(condition_id):
    """
    Fetches the current order book or price for a specific condition_id (market).
    """
    print(f"DEBUG: Fetching price for condition/token ID: {condition_id}")
    # We can use the ClobClient to get the orderbook or ticker
    client = get_polymarket_client()
    if client:
        try:
            print("DEBUG: Using ClobClient...")
            book = client.get_order_book(condition_id)
            print("DEBUG: ClobClient returned book.")
            return book
        except Exception as e:
            print(f"Error fetching orderbook via Client: {e}")
    
    # Fallback to REST if client fails
    try:
        print("DEBUG: Falling back to REST API...")
        url = f"{CLOB_API_URL}/book"
        params = {"token_id": condition_id} 
        response = requests.get(url, params=params)
        print(f"DEBUG: REST API Status: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error fetching book via REST: {e}")
        return None

if __name__ == "__main__":
    print("Fetching Active BTC Markets...")
    markets = get_active_btc_markets()
    print(f"Found {len(markets)} active BTC markets.")
    
    # Print the first 5 to see what they look like
    for m in markets[:5]:
        print(f"\nTitle: {m.get('question')}")
        print(f"Market Slug: {m.get('slug')}")
        print(f"End Date: {m.get('endDate')}")
        
    if markets:
        first_market = markets[0]
        print(f"\n--- Detailed Debug for First Market ---")
        print(f"Question: {first_market.get('question')}")
        print(f"Condition ID: {first_market.get('conditionId')}")
        print(f"Outcomes: {first_market.get('outcomes')}")
        print(f"Outcome Prices: {first_market.get('outcomePrices')}")
        print(f"Best Bid: {first_market.get('bestBid')}")
        print(f"Best Ask: {first_market.get('bestAsk')}")

        # Extract token IDs - clobTokenIds is a JSON string, not a list
        clob_ids_raw = first_market.get('clobTokenIds', '[]')
        if isinstance(clob_ids_raw, str):
            clob_ids = json.loads(clob_ids_raw)
        else:
            clob_ids = clob_ids_raw

        outcomes_raw = first_market.get('outcomes', '[]')
        if isinstance(outcomes_raw, str):
            outcomes = json.loads(outcomes_raw)
        else:
            outcomes = outcomes_raw

        print(f"\nParsed Token IDs ({len(clob_ids)}):")
        for i, tid in enumerate(clob_ids):
            outcome_label = outcomes[i] if i < len(outcomes) else f"Outcome {i}"
            print(f"  {outcome_label}: {tid[:20]}...{tid[-10:]}")

        # Fetch order book for the first token (typically "Up" / "Yes")
        if clob_ids:
            print(f"\nFetching order book for '{outcomes[0] if outcomes else 'first token'}'...")
            book = get_market_prices(clob_ids[0])
            print("Order Book:", str(book)[:300])
