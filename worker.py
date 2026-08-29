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

NASDAQ_SYMBOLS = ["SOUN", "IONQ", "BBAI", "CLSK", "HUT", "BITF", "HIMS", "MARA", "RIOT", "PLTR", "SOFI", "DKNG", "RIVN"]

# Yahoo'nun bot korumasını (Invalid Crumb / 401) aşmak için tarayıcı kimliği tanımlıyoruz
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

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
    print("Küçük/Orta ölçekli Nasdaq taraması yapılıyor...", flush=True)
    for symbol in NASDAQ_SYMBOLS:
        try:
            # Oturumu yfinance'e vererek bot engellerini bypass ediyoruz
            ticker = yf.Ticker(symbol, session=session)
            df = ticker.history(period="5d", interval="15m")
            
            if df.empty or len(df) < 10:
                continue

            last_close = df['Close'].iloc[-1]
            recent_high = df['High'].iloc[-20:-1].max()
            avg_volume = df['Volume'].iloc[-20:-1].mean()
            last_volume = df['Volume'].iloc[-1]

            if last_close >= recent_high * 0.98 and (avg_volume * 0.2 <= last_volume <= avg_volume * 0.8):
                prompt = f"""
                Küçük/Orta ölçekli Nasdaq varlığı {symbol} henüz patlamadı, dipte sıkışıyor!
                Son Fiyat: {last_close:.2f}
                Son Zirve Direnci: {recent_high:.2f}
                Hacim Durumu: Normal ortalamanın %{(last_volume/avg_volume)*100:.0f} kadarı (Sessiz birikim).
                
                Profesyonel bir trader gözüyle kısa ve vurucu yorumla:
                1. Bu hissede patlama potansiyeli var mı?
                2. Kritik tetik seviyesi neresidir?
                """
                
                if client:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    analysis = response.choices[0].message.content
                    send_telegram(f"🚨 *SESSİZ / POTANSİYEL HİSSE: {symbol}*\n\n{analysis}")
        except Exception as e:
            print(f"{symbol} analiz hatası: {e}")

async def main():
    print("RedKeys Küçük Ölçekli Radar Başlatıldı...", flush=True)
    send_telegram("🔔 *Küçük Ölçekli Nasdaq Radarı* tarama motoru güncellendi!")
    
    while True:
        try:
            analyze_nasdaq()
        except Exception as e:
            print(f"Tarama döngü hatası: {e}")
        await asyncio.sleep(900)

if __name__ == "__main__":
    asyncio.run(main())
