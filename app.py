from flask import Flask
import threading
import asyncio
import os
import requests
from worker import main as run_worker, analyze_nasdaq

app = Flask(__name__)

@app.route('/')
def home():
    return "RedKeys Pump Radar 24/7 Aktif!"

@app.route('/test')
def test_telegram():
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return "Token veya Chat ID eksik!", 400
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🚨 Test Başarılı! RedKeys Nasdaq Radar Telegram bağlantısı sağlam ve çalışıyor."
    }
    res = requests.post(url, json=payload)
    return f"Telegram test mesajı gönderildi! Sunucu yanıtı: {res.status_code}"

@app.route('/scan')
def manual_scan():
    try:
        analyze_nasdaq()
        return "Manuel tarama tetiklendi! Kriterlere uyan hisseler varsa Telegram'a bildirim gönderildi."
    except Exception as e:
        return f"Tarama hatası: {e}", 500

def start_bot():
    asyncio.run(run_worker())

if __name__ == '__main__':
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    app.run(host='0.0.0.0', port=10000)
