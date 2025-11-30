import os
import logging
import yt_dlp
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Bot configuration
BOT_TOKEN = "8268332814:AAFgKG_g9yWTkYq6mnVNP7NbzjtTRDD7tYo"
ADMIN_ID = 6120264201

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store URLs temporarily
user_urls = {}

def get_url_hash(url):
    """Create a short hash for the URL to avoid long callback data."""
    return hashlib.md5(url.encode()).hexdigest()[:10]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    welcome_text = """
🎬 *Universal Media Downloader Bot* 🎵

Welcome! I can download media from various platforms!

📝 *How to use:*
Just send me any media URL and I'll give you options to download as MP3 (audio) or MP4 (video)!

⚡ Fast • 🔒 Secure • 🆓 Free
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    logger.info("Start command received")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text.strip()
    logger.info(f"Received: {message_text}")
    
    # Simple URL check
    if any(domain in message_text for domain in ['http://', 'https://']):
        # Store URL with hash
        url_hash = get_url_hash(message_text)
        user_urls[url_hash] = message_text
        
        keyboard = [
            [
                InlineKeyboardButton("🎵 MP3 (Audio)", callback_data=f"mp3|{url_hash}"),
                InlineKeyboardButton("🎬 MP4 (Video)", callback_data=f"mp4|{url_hash}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📥 *Download Options*\n\nURL: `{message_text}`\n\nChoose your preferred format:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        format_type, url_hash = data.split('|', 1)
        
        # Get original URL from storage
        original_url = user_urls.get(url_hash)
        
        if not original_url:
            await query.edit_message_text("❌ URL expired. Please send the URL again.")
            return
        
        await query.edit_message_text(f"⏳ Processing your {format_type.upper()}...\n\nURL: {original_url}")
        
        # Download the media
        file_path = download_media(original_url, format_type)
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            
            # Check file size limit (50MB for Telegram)
            if file_size > 50:
                await query.message.reply_text(
                    f"❌ File too large ({file_size:.1f}MB). Telegram limit is 50MB.\nTry downloading as MP3 or a shorter video."
                )
                os.remove(file_path)
                return
            
            if format_type == 'mp3':
                await query.message.reply_audio(
                    audio=open(file_path, 'rb'),
                    caption=f"🎵 Your audio is ready!\n\nOriginal URL: {original_url}"
                )
            else:
                await query.message.reply_video(
                    video=open(file_path, 'rb'),
                    caption=f"🎬 Your video is ready!\n\nOriginal URL: {original_url}",
                    supports_streaming=True
                )
            
            # Clean up
            os.remove(file_path)
            logger.info(f"Successfully sent {format_type} for {original_url}")
            
        else:
            await query.message.reply_text(
                "❌ Download failed. This might be due to:\n"
                "• Private/restricted content\n"
                "• Unsupported platform\n"
                "• Network issues\n"
                "• File too large\n\n"
                "Try another URL."
            )
            
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.message.reply_text("❌ Error processing your request. Please try again.")

def download_media(url, format_type):
    """Download media using yt-dlp."""
    try:
        os.makedirs('downloads', exist_ok=True)
        
        if format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title).50s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }
        else:
            ydl_opts = {
                'format': 'best[height<=480]',  # Lower quality for smaller files
                'outtmpl': 'downloads/%(title).50s.%(ext)s',
                'quiet': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            if format_type == 'mp3':
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            
            return file_path
            
    except Exception as e:
        logger.error(f"Download error for {url}: {e}")
        return None

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_error_handler(error_handler)
        
        # Start bot
        print("🤖 Bot starting...")
        application.run_polling()
        print("🤖 Bot is running!")
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")

if __name__ == '__main__':
    main()
