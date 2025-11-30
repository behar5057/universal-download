import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

# Bot configuration
BOT_TOKEN = "8268332814:AAFgKG_g9yWTkYq6mnVNP7NbzjtTRDD7tYo"
ADMIN_ID = 6120264201

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    """Send welcome message when the command /start is issued."""
    welcome_text = """
🎬 *Universal Media Downloader Bot* 🎵

Welcome! I can download media from various platforms!

📝 *How to use:*
Just send me any media URL and I'll give you options to download as MP3 (audio) or MP4 (video)!

⚡ Fast • 🔒 Secure • 🆓 Free
    """
    update.message.reply_text(welcome_text, parse_mode='Markdown')
    logger.info("Start command received")

def handle_message(update: Update, context: CallbackContext):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text.strip()
    logger.info(f"Received: {message_text}")
    
    # Simple URL check
    if any(domain in message_text for domain in ['http://', 'https://']):
        keyboard = [
            [
                InlineKeyboardButton("🎵 MP3 (Audio)", callback_data=f"mp3|{message_text}"),
                InlineKeyboardButton("🎬 MP4 (Video)", callback_data=f"mp4|{message_text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "📥 *Download Options*\n\nChoose your preferred format:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")

def button_handler(update: Update, context: CallbackContext):
    """Handle button callbacks."""
    query = update.callback_query
    query.answer()
    
    try:
        data = query.data
        format_type, url = data.split('|', 1)
        
        query.edit_message_text(f"⏳ Processing your {format_type.upper()}...")
        
        # Download the media
        file_path = download_media(url, format_type)
        
        if file_path and os.path.exists(file_path):
            if format_type == 'mp3':
                query.message.reply_audio(
                    audio=open(file_path, 'rb'),
                    caption="🎵 Your audio is ready!"
                )
            else:
                query.message.reply_video(
                    video=open(file_path, 'rb'),
                    caption="🎬 Your video is ready!",
                    supports_streaming=True
                )
            os.remove(file_path)
        else:
            query.message.reply_text("❌ Download failed. Try another URL.")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        query.message.reply_text("❌ Error processing your request.")

def download_media(url, format_type):
    """Download media using yt-dlp."""
    try:
        os.makedirs('downloads', exist_ok=True)
        
        if format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            }
        else:
            ydl_opts = {
                'format': 'best[height<=720]',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format_type == 'mp3':
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            return file_path
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None

def error_handler(update: Update, context: CallbackContext):
    """Log errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    try:
        # Create updater and dispatcher
        updater = Updater(BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Add handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        dispatcher.add_handler(CallbackQueryHandler(button_handler))
        dispatcher.add_error_handler(error_handler)
        
        # Start bot
        print("🤖 Bot starting...")
        updater.start_polling()
        print("🤖 Bot is running!")
        
        # Run the bot until you press Ctrl-C
        updater.idle()
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")

if __name__ == '__main__':
    main()
