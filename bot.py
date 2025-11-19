import requests
from telegram.ext import Updater, CommandHandler
import json, os, logging

TOKEN = "8237404529:AAFoFSvHok6OF7zPiMCFkXf7AK1CLrCI-_w"

PORTO_FILE = "portofolio.json"

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

def get_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,idr"
    return requests.get(url).json()

def harga(update, context):
    try:
        coin = context.args[0].lower()
        data = get_price(coin)
        usd = data[coin]['usd']
        idr = data[coin]['idr']
        update.message.reply_text(f"📊 {coin.upper()}\nUSD: ${usd:,}\nIDR: Rp {idr:,}")
    except:
        update.message.reply_text("Format: /harga btc")

alerts = {}

def alert(update, context):
    try:
        coin = context.args[0].lower()
        target = float(context.args[1])
        user = update.message.from_user.id
        alerts.setdefault(user, []).append({"coin": coin, "target": target})
        update.message.reply_text(f"🔔 Alert dibuat {coin.upper()} → ${target}")
    except:
        update.message.reply_text("Contoh: /alert btc 90000")

def check_alerts(context):
    for user, arr in alerts.items():
        for a in list(arr):
            price = get_price(a["coin"])[a["coin"]]["usd"]
            if price <= a["target"]:
                context.bot.send_message(chat_id=user, text=f"⚠ ALERT: {a['coin'].upper()} sekarang ${price:,}")
                arr.remove(a)

def add_porto(update, context):
    try:
        coin = context.args[0].lower()
        amount = float(context.args[1])
        user = str(update.message.from_user.id)
        porto = load_porto()
        porto.setdefault(user, {})
        porto[user][coin] = porto[user].get(coin, 0) + amount
        save_porto(porto)
        update.message.reply_text(f"✔ Ditambahkan {amount} {coin.upper()}")
    except:
        update.message.reply_text("Format: /add btc 0.01")

def porto(update, context):
    user = str(update.message.from_user.id)
    porto = load_porto()
    if user not in porto:
        update.message.reply_text("Portofolio kosong.")
        return
    text = "📊 PORTOFOLIO\n\n"
    total_usd = 0
    total_idr = 0
    for coin, amount in porto[user].items():
        data = get_price(coin)[coin]
        usd = data["usd"]
        idr = data["idr"]
        val_usd = usd * amount
        val_idr = idr * amount
        total_usd += val_usd
        total_idr += val_idr
        text += f"{coin.upper()} — {amount}\nUSD: ${val_usd:,.2f}\nIDR: Rp {val_idr:,.0f}\n\n"
    text += f"TOTAL:\nUSD: ${total_usd:,.2f}\nIDR: Rp {total_idr:,.0f}"
    update.message.reply_text(text)

def berita(update, context):
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=free&filter=important"
        data = requests.get(url).json()
        text = "📰 BERITA CRYPTO\n\n"
        for b in data["results"][:5]:
            text += f"• {b['title']}\n\n"
        update.message.reply_text(text)
    except:
        update.message.reply_text("Gagal ambil berita.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("harga", harga))
    dp.add_handler(CommandHandler("alert", alert))
    dp.add_handler(CommandHandler("add", add_porto))
    dp.add_handler(CommandHandler("porto", porto))
    dp.add_handler(CommandHandler("berita", berita))

    job = updater.job_queue
    job.run_repeating(check_alerts, interval=30, first=5)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
