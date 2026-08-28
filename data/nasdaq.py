import logging
import aiohttp

logger = logging.getLogger(__name__)

ALLOWED_STOCKS = [
    "PLTR", "SOUN", "MARA", "RIOT", "MSTR", 
    "COIN", "IONQ", "HOOD", "RIVN", "SMCI", 
    "NVAX", "BYND", "RDDT", "ASTS"
]

FORBIDDEN_STOCKS = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META"]

async def fetch_nasdaq_data():
    symbols_str = ",".join(ALLOWED_STOCKS)
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols_str}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise RuntimeError(f"Yahoo Finance NASDAQ veri hatası: {response.status}")
            
            data = await response.json()
            
    quotes = data.get("quoteResponse", {}).get("result", [])
    
    if not quotes:
        raise RuntimeError("Yahoo Finance canlı NASDAQ verisi döndürmedi. Sıfır tolerans: İşlem iptal.")

    parsed_results = []
    for q in quotes:
        symbol = q.get("symbol")
        
        if symbol in FORBIDDEN_STOCKS:
            continue
            
        regular_price = q.get("regularMarketPrice")
        pre_market_price = q.get("preMarketPrice")
        pre_market_change = q.get("preMarketChangePercent")
        
        pre_market_volume = q.get("preMarketVolume", 0) or 0
        avg_volume = q.get("averageDailyVolume10Day", 1) or 1
        
        current_price = pre_market_price if pre_market_price is not None else regular_price
        change_pct = pre_market_change if pre_market_change is not None else q.get("regularMarketChangePercent", 0.0)

        if current_price is None:
            raise RuntimeError(f"{symbol} için canlı fiyat okunamadı. Fallback yasak.")

        volume_ratio = float(pre_market_volume) / float(avg_volume) if avg_volume > 0 else 0.0

        parsed_results.append({
            "symbol": symbol,
            "price": float(current_price),
            "change_pct": float(change_pct),
            "pre_market_volume": int(pre_market_volume),
            "volume_ratio": float(volume_ratio)
        })

    parsed_results.sort(key=lambda x: x["change_pct"], reverse=True)
    return parsed_results
