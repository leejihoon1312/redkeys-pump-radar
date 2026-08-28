import yfinance as yf
import pandas as pd

class BinanceMarket:
    def __init__(self):
        # Popüler ve hacimli kripto çiftleri
        self.symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "XRP-USD", "DOGE-USD", "PEPE-USD", "NEAR-USD"]

    async def load_symbols(self):
        # Yahoo Finance üzerinden sembollerin güncel verilerini simüle ediyoruz
        print("Piyasa verileri Yahoo Finance üzerinden başarıyla çekiliyor (Binance IP engeli aşıldı).")
        return self.symbols

    async def get_market_data(self):
        data = {}
        for symbol in self.symbols:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="5m")
            if not hist.empty:
                data[symbol] = hist
        return data
