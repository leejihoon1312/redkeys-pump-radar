import time
import os
import requests
import yfinance as yf
from openai import OpenAI
from data.binance import BinanceMarket

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram token veya chat id eksik!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")

async def main():
    print("RedKeys Pump Radar Worker Başlatıldı...", flush=True)
    market = BinanceMarket()
    
    # Başlangıçta çalıştığını anlamak için Telegram'a haber uçuralım
    send_telegram("🚀 *RedKeys Pump Radar* aktif! Piyasalar taranıyor...")

    while True:
        try:
            symbols = await market.load_symbols()
            data = await market.get_market_data()
            
            for symbol, df in data.items():
                if df.empty or len(df) < 2:
                    continue
                
                # Basit bir değişim kontrolü (Son mumu kontrol et)
                last_row = df.iloc[-1]
                prev_row = df.iloc[-2]
                
                # Fiyat değişim yüzdesi
                change = ((last_row['Close'] - prev_row['Close']) / prev_row['Close']) * 100
                
                # Test amaçlı veya belirgin bir hareket (örn: %1.5 üzeri değişim) yakalarsa OpenAI'a soralım
                if abs(change) >= 1.0: 
                    prompt = f"""
                    Kripto varlık {symbol} için son fiyat değişimi %{change:.2f}. 
                    Bunu bir kripto analisti gibi değerlendir. Şu formatta Türkçe bir rapor hazırla:
                    🚨 REDKEYS KRİPTO SPOT RAPORU 🚨
                    Büyük Lig Trend Analizi
                    #{symbol.replace('-USD', '')} Analiz Özeti
                    Giriş / Kademeli Alım Bölgesi: [...]
                    Orta Vade Hedefler: [...]
                    Stop / Destek Seviyesi: [...]
                    Kısa Yorum: [...]
                    """
                    
                    if client:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        analysis = response.choices[0].message.content
                        send_telegram(analysis)
                    else:
                        send_telegram(f"🚨 *{symbol}* hareketli! Değişim: %{change:.2f}")
            
            # Her 10 dakikada bir tarama yap
            await asyncio.sleep(600)
        except Exception as e:
            print(f"Worker döngü hatası: {e}", flush=True)
            await asyncio.sleep(60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
