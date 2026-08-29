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

NASDAQ_SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META", "PLTR", "QQQ"]

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

            if last_close >= recent_high * 0.99 and last_volume > avg_volume * 1.5:
                prompt = f"""
                Nasdaq hissesi {symbol} kritik direnç bölgesini test ediyor!
                Son Fiyat: {last_close:.2f}
                Son Zirve Direnci: {recent_high:.2f}
                Hacim Durumu: Normal ortalamanın %{(last_volume/avg_volume)*100:.0f} katı.
                
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
                    send_telegram(f"🚨 *{symbol}* direnç bölgesinde hacim patlatıyor! Fiyat: {last_close}")
        except Exception as e:
            print(f"{symbol} analiz hatası: {e}")

async def main():
    print("RedKeys Nasdaq Radar Worker Başlatıldı...", flush=True)
    send_telegram("🔔 *Nasdaq Hacim ve Direnç Radar* devrede! Piyasalar taranıyor...")
    
    while True:
        try:
            analyze_nasdaq()
        except Exception as e:
            print(f"Tarama döngü hatası: {e}")
        # Her 15 dakikada bir piyasayı tekrar tara
        await asyncio.sleep(900)

if __name__ == "__main__":
    asyncio.run(main())
