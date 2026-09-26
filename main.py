import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐉 NAGA BOT MR BRYAN AKTIF BOSKU! 🔥")

async def gacor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 JAM GACOR: 20:00 - 02:00 WIB BOS!")

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gacor", gacor))
    app.run_polling()

if __name__ == "__main__":
    main()
