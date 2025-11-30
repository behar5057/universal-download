import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from flask import Flask

# Bot configuration
BOT_TOKEN = "8268332814:AAFgKG_g9yWTkYq6mnVNP7NbzjtTRDD7tYo"
ADMIN_ID = 6120264201

app = Flask(__name__)

# Initialize bot application
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🎬 Universal Media Downloader Bot 🎵

Welcome! I can download media from various platforms!

📝 How to use:
Just send me any media URL and I'll give you options to download as MP3 (audio) or MP4 (video)!
    """
    await update.message.reply_text(welcome_text)

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(CallbackQueryHandler(button_handler))

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.update_queue.put(update)
    return 'ok'

if __name__ == '__main__':
    # Set webhook for Render
    application.bot.set_webhook(url="https://your-bot-name.onrender.com/webhook")
    app.run(host='0.0.0.0', port=8080)
