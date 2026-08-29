import time
import os
import asyncio
import requests
import yfinance as yf
from openai import OpenAI

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Hem büyük devler hem de 0.3 / küçük-orta ölçekli hareketli Nasdaq varlıkları
NASDAQ_SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META", "PLTR", "SOFI", "RIVN", "DKNG", "MARA", "RIOT", "QQQ"]

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram hata: {e}")

def analyze_nasdaq():
    print("Nasdaq hacim ve direnç taraması yapılıyor...", flush=True)
    for symbol in NASDAQ_SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d", interval="15m")
            
            if df.empty or len(df) < 10:
                continue

            last_close = df['Close'].iloc[-1]
            recent_high = df['High'].iloc[-20:-1].max()
            avg_volume = df['Volume'].iloc[-20:-1].mean()
            last_volume = df['Volume'].iloc[-1]

            # Eşiği 0.3'e düşürdük, daha küçük hacim dalgalanmalarını da yakalayacak
            if last_close >= recent_high * 0.98 and last_volume > avg_volume * 0.3:
                prompt = f"""
                Nasdaq varlığı {symbol} direnç bölgesine yaklaşıyor!
                Son Fiyat: {last_close:.2f}
                Son Zirve Direnci: {recent_high:.2f}
                Hacim Durumu: Normal ortalamanın %{(last_volume/avg_volume)*100:.0f} kadarı.
                
                Bunu profesyonel bir borsa traderı gözüyle kısaca yorumla:
                1. Direnci kırma ihtimali nedir?
                2. Kritik tetik seviyesi neresidir?
                Formatı net ve vurucu tut.
                """
                
                if client:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    analysis = response.choices[0].message.content
                    send_telegram(f"🚨 *NASDAQ HACİM ALARMI: {symbol}*\n\n{analysis}")
                else:
                    send_telegram(f"🚨 *{symbol}* direnç bölgesinde hareketli! Fiyat: {last_close}")
        except Exception as e:
            print(f"{symbol} analiz hatası: {e}")

async def main():
    print("RedKeys Nasdaq Radar Worker Başlatıldı...", flush=True)
    send_telegram("🔔 *Nasdaq Hacim ve Direnç Radar* güncellendi! 7/24 aktif tarama devrede...")
    
    while True:
        try:
            analyze_nasdaq()
        except Exception as e:
            print(f"Tarama döngü hatası: {e}")
        # Her 15 dakikada bir piyasayı tekrar tara
        await asyncio.sleep(900)

if __name__ == "__main__":
    asyncio.run(main())
