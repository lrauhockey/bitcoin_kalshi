
import ccxt
import time

def get_exchange_instance():
    """Returns a ccxt exchange instance (Kraken)."""
    return ccxt.kraken({
        'enableRateLimit': True,
    })

def get_btc_price():
    """Fetches the current BTC/USDT price."""
    exchange = get_exchange_instance()
    try:
        ticker = exchange.fetch_ticker('BTC/USD')
        return ticker['last']
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
        return None

def get_order_book(limit=20):
    """Fetches the order book for BTC/USDT."""
    exchange = get_exchange_instance()
    try:
        order_book = exchange.fetch_order_book('BTC/USD', limit=limit)
        return order_book
    except Exception as e:
        print(f"Error fetching order book: {e}")
        return None

def calculate_wall_strength(order_book, price_range_percent=0.01):
    """
    Calculates the strength of bid and ask walls within a certain percentage of the current price.
    
    Args:
        order_book (dict): The order book data from ccxt.
        price_range_percent (float): The percentage range to consider (default 1%).
    
    Returns:
        dict: A dictionary containing 'bid_wall_volume', 'ask_wall_volume', and 'wall_ratio'.
    """
    if not order_book:
        return None

    bids = order_book['bids']
    asks = order_book['asks']
    
    # Get the best bid and ask prices to use as a baseline, or use the ticker price if available.
    # Here we use the best bid/ask from the order book.
    best_bid = bids[0][0] if bids else 0
    best_ask = asks[0][0] if asks else 0
    mid_price = (best_bid + best_ask) / 2

    # Calculate the price boundaries
    lower_bound = mid_price * (1 - price_range_percent)
    upper_bound = mid_price * (1 + price_range_percent)

    bid_wall_volume = sum(entry[1] for entry in bids if entry[0] >= lower_bound)
    ask_wall_volume = sum(entry[1] for entry in asks if entry[0] <= upper_bound)

    wall_ratio = bid_wall_volume / ask_wall_volume if ask_wall_volume > 0 else float('inf')

    return {
        'bid_wall_volume': bid_wall_volume,
        'ask_wall_volume': ask_wall_volume,
        'wall_ratio': wall_ratio,
        'mid_price': mid_price
    }

if __name__ == "__main__":
    # Test the module
    print("Fetching BTC Price...")
    price = get_btc_price()
    print(f"Current BTC Price: {price}")

    print("\nFetching Order Book...")
    ob = get_order_book(limit=100)
    
    if ob:
        print(f"Top Bid: {ob['bids'][0]}")
        print(f"Top Ask: {ob['asks'][0]}")
        
        print("\nCalculating Wall Strength (1% range)...")
        walls = calculate_wall_strength(ob)
        print(f"Bid Wall Volume: {walls['bid_wall_volume']:.2f}")
        print(f"Ask Wall Volume: {walls['ask_wall_volume']:.2f}")
        print(f"Wall Ratio (Bid/Ask): {walls['wall_ratio']:.2f}")
