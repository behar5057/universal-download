import os
import logging
import yt_dlp
import asyncio
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

# Supported domains
SUPPORTED_DOMAINS = [
    'youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 
    'fb.watch', 'tiktok.com', 'twitter.com', 'x.com',
    'vimeo.com', 'soundcloud.com', 'pinterest.com'
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    welcome_text = """
🎬 *Universal Media Downloader Bot* 🎵

Welcome! I can download media from various platforms including:
• YouTube
• Instagram  
• Facebook
• TikTok
• Twitter/X
• Pinterest
• SoundCloud
• Vimeo

📝 *How to use:*
Just send me any media URL and I'll give you options to download as MP3 (audio) or MP4 (video)!

⚡ Fast • 🔒 Secure • 🆓 Free
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    logger.info(f"Start command from user {update.message.from_user.id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text.strip()
    logger.info(f"Received message: {message_text}")
    
    # Check if it's a URL
    if any(domain in message_text.lower() for domain in SUPPORTED_DOMAINS):
        # Create format selection buttons
        keyboard = [
            [
                InlineKeyboardButton("🎵 MP3 (Audio)", callback_data=f"mp3|{message_text}"),
                InlineKeyboardButton("🎬 MP4 (Video)", callback_data=f"mp4|{message_text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📥 *Download Options*\n\nChoose your preferred format:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Please send a valid URL from supported platforms:\n"
            "YouTube, Instagram, Facebook, TikTok, Twitter, etc.",
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        format_type, url = data.split('|', 1)
        
        await query.edit_message_text(
            f"⏳ *Processing your {format_type.upper()} download...*\n\nPlease wait...",
            parse_mode='Markdown'
        )
        
        # Download the media
        file_path = await download_media(url, format_type)
        
        if file_path:
            if format_type == 'mp3':
                await query.message.reply_audio(
                    audio=open(file_path, 'rb'),
                    caption="🎵 Your audio is ready!"
                )
            else:  # mp4
                await query.message.reply_video(
                    video=open(file_path, 'rb'),
                    caption="🎬 Your video is ready!",
                    supports_streaming=True
                )
            
            # Clean up
            os.remove(file_path)
        else:
            await query.message.reply_text("❌ Download failed. Please try another URL.")
            
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.message.reply_text("❌ An error occurred. Please try again.")

async def download_media(url, format_type):
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
            return ydl.prepare_filename(info)
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None

def main():
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 Bot is starting...")
    application.run_polling()
    print("🤖 Bot is running!")

if __name__ == '__main__':
    main()
