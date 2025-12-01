import os
import logging
import yt_dlp
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from flask import Flask, request

# Bot configuration
BOT_TOKEN = "8268332814:AAFgKG_g9yWTkYq6mnVNP7NbzjtTRDD7tYo"
ADMIN_ID = 6120264201

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for webhook
app = Flask(__name__)

# Store URLs temporarily
user_urls = {}

def get_url_hash(url):
    """Create a short hash for the URL to avoid long callback data."""
    return hashlib.md5(url.encode()).hexdigest()[:10]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    welcome_text = """
🎬 *Universal Media Downloader Bot* 🎵

Welcome! Send me any media URL and I'll download it as MP3 or MP4 for you!
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text.strip()
    
    if any(domain in message_text for domain in ['http://', 'https://']):
        url_hash = get_url_hash(message_text)
        user_urls[url_hash] = message_text
        
        keyboard = [
            [
                InlineKeyboardButton("🎵 MP3", callback_data=f"mp3|{url_hash}"),
                InlineKeyboardButton("🎬 MP4", callback_data=f"mp4|{url_hash}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📥 Download options for:\n`{message_text}`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        format_type, url_hash = data.split('|', 1)
        original_url = user_urls.get(url_hash)
        
        if not original_url:
            await query.edit_message_text("❌ URL expired. Send it again.")
            return
        
        await query.edit_message_text(f"⏳ Downloading {format_type.upper()}...")
        
        file_path = download_media(original_url, format_type)
        
        if file_path and os.path.exists(file_path):
            if format_type == 'mp3':
                await query.message.reply_audio(
                    audio=open(file_path, 'rb'),
                    caption="🎵 Your audio is ready!"
                )
            else:
                await query.message.reply_video(
                    video=open(file_path, 'rb'),
                    caption="🎬 Your video is ready!",
                    supports_streaming=True
                )
            os.remove(file_path)
        else:
            await query.message.reply_text("❌ Download failed. Try another URL.")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text("❌ Error. Please try again.")

def download_media(url, format_type):
    try:
        os.makedirs('downloads', exist_ok=True)
        
        if format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
            }
        else:
            ydl_opts = {
                'format': 'best[height<=480]',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format_type == 'mp3':
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            return file_path
    except:
        return None

# Flask routes
@app.route('/')
def home():
    return "🤖 Bot is running! Use /start on Telegram."

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates."""
    update = Update.de_json(request.get_json(), bot)
    application.update_queue.put(update)
    return 'ok'

def main():
    """Start the bot with webhook."""
    global application, bot
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    bot = application.bot
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Set webhook for Render
    webhook_url = "https://universal-download.onrender.com/webhook"
    bot.set_webhook(webhook_url)
    print(f"✅ Webhook set to: {webhook_url}")
    
    # Start Flask
    print("🤖 Bot is running with webhook...")
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
