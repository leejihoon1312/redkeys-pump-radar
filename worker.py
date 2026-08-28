import asyncio
import logging
from data.binance import BinanceMarket
from data.nasdaq import fetch_nasdaq_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

async def nasdaq_loop():
    while True:
        try:
            results = await fetch_nasdaq_data()
            logging.info("--- NASDAQ PRE-MARKET TARAMA RAPORU ---")
            for item in results[:5]:  # En hareketli ilk 5 hisse
                logging.info(
                    "HİSSE: %s | Fiyat: $%s | Değişim: %%%.2f | Hacim Oranı: %.2f",
                    item["symbol"],
                    item["price"],
                    item["change_pct"],
                    item["volume_ratio"]
                )
        except Exception as error:
            logging.error("NASDAQ tarama hatası: %s", error)
        
        # 5 dakikada bir pre-market verilerini tara
        await asyncio.sleep(300)

async def main():
    market = BinanceMarket()
    await market.load_symbols()
    
    # Binance WebSocket ile NASDAQ periyodik tarayıcısını aynı anda (async) çalıştır
    await asyncio.gather(
        market.connect(),
        nasdaq_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
