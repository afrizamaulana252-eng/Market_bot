import logging
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

import os
TOKEN = os.getenv("TOKEN", "TOKEN_PLACEHOLDER")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running! Send /market to get US market data.")

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tickers = {
        "Dow Jones": "^DJI",
        "Nasdaq": "^IXIC",
        "S&P 500": "^GSPC"
    }

    msg = "📊 **Market Update:**\n\n"

    for name, symbol in tickers.items():
        data = yf.Ticker(symbol).history(period="1d")
        price = round(data["Close"].iloc[-1], 2)
        msg += f"• {name}: {price}\n"

    await update.message.reply_text(msg)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("market", market))

if __name__ == "__main__":
    app.run_polling()
