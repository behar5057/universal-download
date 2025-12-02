import os
import logging
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Set token as environment variable FIRST
os.environ['BOT_TOKEN'] = "8268332814:AAGhskQ16kgCieoz8BBHX6iQWxDEGt5XPxg"
BOT_TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = 6120264201

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    welcome_text = """
🎬 *DOWNLOAD ANYTHING BOT* 🎵

Send me any media URL and I'll download it!

Examples:
• YouTube: https://www.youtube.com/watch?v=dQw4w9WgXcQ
• Instagram: https://www.instagram.com/reel/Cx9JtVpMhQy/
• TikTok, Twitter, Facebook, etc.

⚡ Fast • 🔒 Secure • 🆓 Free
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text.strip()
    
    if message_text.startswith(('http://', 'https://', 'www.')):
        if message_text.startswith('www.'):
            message_text = 'https://' + message_text
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video", callback_data=f"video|{message_text}"),
                InlineKeyboardButton("🎵 MP3", callback_data=f"audio|{message_text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📥 Download: `{message_text}`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Send a valid URL starting with http:// or https://")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        format_type, url = data.split('|', 1)
        
        await query.edit_message_text(f"⏳ Downloading {format_type}...")
        
        # Download the media
        file_path = download_media(url, format_type)
        
        if file_path and os.path.exists(file_path):
            if format_type == 'audio':
                with open(file_path, 'rb') as f:
                    await query.message.reply_audio(
                        audio=f,
                        caption="🎵 Your audio is ready!"
                    )
            else:
                with open(file_path, 'rb') as f:
                    await query.message.reply_video(
                        video=f,
                        caption="🎬 Your video is ready!",
                        supports_streaming=True
                    )
            os.remove(file_path)
            print(f"✅ Successfully sent {format_type}")
        else:
            await query.message.reply_text("❌ Download failed. Try a YouTube URL.")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text("❌ Error. Try YouTube: https://www.youtube.com/watch?v=dQw4w9WgXcQ")

def download_media(url, format_type):
    """Download media using yt-dlp."""
    try:
        os.makedirs('downloads', exist_ok=True)
        
        if format_type == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'quiet': True,
            }
        else:
            ydl_opts = {
                'format': 'best[height<=720]',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'quiet': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format_type == 'audio':
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            return file_path
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None

def main():
    """Start the bot with error handling."""
    try:
        print("🤖 Starting bot...")
        print(f"✅ Token: {BOT_TOKEN[:10]}...")
        
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        print("🤖 Bot is running! Waiting for messages...")
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Bot failed: {e}")
        print("🔄 Restarting in 5 seconds...")
        time.sleep(5)
        main()

if __name__ == '__main__':
    import time
    main()
