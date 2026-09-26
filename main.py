import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐉 NAGA GACOR MR BRYAN AKTIF BOS! Ketik /gacor")

async def gacor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 JAM GACOR: 22:00 - 02:00 WIB")

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gacor", gacor))
    app.run_polling()

if __name__ == "__main__":
    main()
