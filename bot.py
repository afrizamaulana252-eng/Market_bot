import os
import json
import logging
import requests
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
TG_URL = f"https://api.telegram.org/bot{TOKEN}/"
PORTO_FILE = "portofolio.json"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_porto():
    if not os.path.exists(PORTO_FILE):
        return {}
    with open(PORTO_FILE, "r") as f:
        return json.load(f)

def save_porto(data):
    with open(PORTO_FILE, "w") as f:
        json.dump(data, f, indent=4)

def send_message(chat_id, text):
    requests.post(TG_URL + "sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def get_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,idr"
    return requests.get(url).json()

def cmd_harga(chat_id, args):
    try:
        coin = args[0].lower()
        data = get_price(coin)
        usd = data[coin]["usd"]
        idr = data[coin]["idr"]
        send_message(chat_id, f"📊 {coin.upper()}\nUSD: ${usd:,}\nIDR: Rp {idr:,}")
    except:
        send_message(chat_id, "Format: /harga btc")

alerts = {}

def cmd_alert(chat_id, user_id, args):
    try:
        coin = args[0].lower()
        target = float(args[1])
        alerts.setdefault(user_id, []).append({"coin": coin, "target": target})
        send_message(chat_id, f"🔔 Alert diset {coin.upper()} → ${target}")
    except:
        send_message(chat_id, "Format: /alert btc 90000")

def check_alerts():
    for user, arr in alerts.items():
        for a in list(arr):
            price = get_price(a["coin"])[a["coin"]]["usd"]
            if price <= a["target"]:
                requests.post(TG_URL + "sendMessage", json={
                    "chat_id": user,
                    "text": f"⚠ ALERT! {a['coin'].upper()} sekarang ${price:,}"
                })
                arr.remove(a)

def cmd_add(chat_id, user_id, args):
    try:
        coin = args[0].lower()
        amount = float(args[1])
        porto = load_porto()
        porto.setdefault(user_id, {})
        porto[user_id][coin] = porto[user_id].get(coin, 0) + amount
        save_porto(porto)
        send_message(chat_id, f"✔ Ditambahkan {amount} {coin.upper()}")
    except:
        send_message(chat_id, "Format: /add btc 0.01")

def cmd_porto(chat_id, user_id):
    porto = load_porto()
    if user_id not in porto:
        send_message(chat_id, "Portofolio kosong.")
        return
    text = "📊 PORTOFOLIO\n\n"
    total_usd = 0
    total_idr = 0
    for coin, amount in porto[user_id].items():
        data = get_price(coin)[coin]
        usd = data["usd"]
        idr = data["idr"]
        v_usd = usd * amount
        v_idr = idr * amount
        total_usd += v_usd
        total_idr += v_idr
        text += f"{coin.upper()} — {amount}\nUSD: ${v_usd:,.2f}\nIDR: Rp {v_idr:,.0f}\n\n"
    text += f"TOTAL:\nUSD: ${total_usd:,.2f}\nIDR: Rp {total_idr:,.0f}"
    send_message(chat_id, text)

def cmd_berita(chat_id):
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=free&filter=important"
        data = requests.get(url).json()
        text = "📰 BERITA CRYPTO\n\n"
        for b in data["results"][:5]:
            text += f"• {b['title']}\n\n"
        send_message(chat_id, text)
    except:
        send_message(chat_id, "Gagal ambil berita.")

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return "OK"
    chat_id = data["message"]["chat"]["id"]
    user_id = str(data["message"]["from"]["id"])
    text = data["message"].get("text", "")
    parts = text.split()
    cmd = parts[0].lower()
    args = parts[1:]
    if cmd == "/start":
        send_message(chat_id, "Halo! Bot Webhook Railway aktif 🚀")
    elif cmd == "/harga":
        cmd_harga(chat_id, args)
    elif cmd == "/alert":
        cmd_alert(chat_id, user_id, args)
    elif cmd == "/add":
        cmd_add(chat_id, user_id, args)
    elif cmd == "/porto":
        cmd_porto(chat_id, user_id)
    elif cmd == "/berita":
        cmd_berita(chat_id)
    return "OK"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
