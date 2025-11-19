import requests
from typing import Dict, Optional
import logging

COINGECKO_API = "https://api.coingecko.com/api/v3"

def get_coin_id(coin_name: str) -> Optional[str]:
    try:
        url = f"{COINGECKO_API}/coins/list"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        coins = response.json()
        
        # Simple search by symbol or id (case-insensitive)
        for coin in coins:
            if coin['symbol'].upper() == coin_name.upper() or coin['id'].upper() == coin_name.upper():
                logging.info(f"Found exact match for {coin_name}: {coin['id']}")
                return coin['id']
        
        # Fallback to name search
        for coin in coins:
            if coin_name.upper() in coin['name'].upper():
                logging.info(f"Found name match for {coin_name}: {coin['id']}")
                return coin['id']
        
        logging.warning(f"No coin found for {coin_name}")
        return None
    except Exception as e:
        logging.error(f"Error searching coin {coin_name}: {e}")
        return None

def get_prices(coin_names: list) -> Dict[str, float]:
    """Get current USD prices for list of coin names (symbols)."""
    prices = {}
    if not coin_names:
        return prices
    
    name_to_id = {}
    coin_ids = []
    
    # Hardcoded for defaults
    id_map = {
        'SOL': 'solana',
        'ETH': 'ethereum',
        'BTC': 'bitcoin',
        'BNB': 'binancecoin'
    }
    
    for name in coin_names:
        coin_id = id_map.get(name.upper())
        if not coin_id:
            # Custom: search for ID
            coin_id = get_coin_id(name)
            if not coin_id:
                logging.warning(f"Could not find ID for {name}")
                continue
        
        name_to_id[name] = coin_id
        coin_ids.append(coin_id)
    
    if not coin_ids:
        return prices
    
    try:
        url = f"{COINGECKO_API}/simple/price"
        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': 'usd'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Map back using id_to_name
        id_to_name = {v: k for k, v in name_to_id.items()}
        for coin_id, price_data in data.items():
            name = id_to_name.get(coin_id)
            if name:
                prices[name] = price_data['usd']
                logging.info(f"Price for {name}: {price_data['usd']}")
        
        return prices
    except Exception as e:
        logging.error(f"Error fetching prices: {e}")
        return prices
