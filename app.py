from flask import Flask
import threading
import asyncio
from worker import main as run_worker

app = Flask(__name__)

@app.route('/')
def home():
    return "RedKeys Pump Radar 24/7 Aktif!"

def start_bot():
    asyncio.run(run_worker())

if __name__ == '__main__':
    # Botu arka planda thread olarak başlatıyoruz
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Render'ın 10000 portunda web sunucusunu ayağa kaldırıyoruz
    app.run(host='0.0.0.0', port=10000)
