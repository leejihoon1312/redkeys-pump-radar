import json
import logging
from collections import defaultdict, deque
import aiohttp
import websockets

logger = logging.getLogger(__name__)
REST_URL = "https://api.binance.com"
WS_URL = "wss://stream.binance.com:9443/stream"

class BinanceMarket:
    def __init__(self):
        self.symbols = []
        self.candles = defaultdict(lambda: deque(maxlen=100))

    async def load_symbols(self):
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{REST_URL}/api/v3/exchangeInfo") as response:
                if response.status != 200:
                    raise RuntimeError(f"Binance exchangeInfo hatası: {response.status}")
                data = await response.json()

        symbols = []
        for item in data["symbols"]:
            if item["status"] != "TRADING":
                continue
            if item["quoteAsset"] != "USDT":
                continue
            if not item["isSpotTradingAllowed"]:
                continue
            symbols.append(item["symbol"].lower())

        if not symbols:
            raise RuntimeError("Binance geçerli coin döndürmedi.")

        self.symbols = symbols
        logger.info("%d USDT spot paritesi bulundu.", len(symbols))

    async def connect(self):
        selected = self.symbols[:100]
        streams = [f"{symbol}@kline_5m" for symbol in selected]
        url = f"{WS_URL}?streams=" + "/".join(streams)

        while True:
            try:
                logger.info("Binance WebSocket bağlanıyor...")
                async with websockets.connect(url, ping_interval=20, ping_timeout=60) as websocket:
                    logger.info("BINANCE CANLI BAĞLANTI OK.")
                    async for raw in websocket:
                        message = json.loads(raw)
                        data = message.get("data", {})
                        if data.get("e") != "kline":
                            continue
                        symbol = data["s"].lower()
                        kline = data["k"]
                        candle = {
                            "open_time": kline["t"],
                            "open": float(kline["o"]),
                            "high": float(kline["h"]),
                            "low": float(kline["l"]),
                            "close": float(kline["c"]),
                            "volume": float(kline["v"]),
                            "closed": bool(kline["x"]),
                        }
                        self.candles[symbol].append(candle)
                        logger.info("%s | $%s | volume=%s", symbol.upper(), candle["close"], candle["volume"])
            except Exception as error:
                logger.error("WebSocket koptu: %s", error)
                logger.info("5 saniye sonra yeniden bağlanıyorum...")
                import asyncio
                await asyncio.sleep(5)
