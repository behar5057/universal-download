import os
import logging
import yt_dlp
import requests
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
    'pinterest.com', 'tiktok.com', 'twitter.com', 'x.com',
    'vimeo.com', 'soundcloud.com', 'twitch.tv', 'dailymotion.com',
    'reddit.com', 'linkedin.com', 'vimeo.com'
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    welcome_text = """
🎬 *Universal Media Downloader Bot* 🎵

Welcome! I can download media from various platforms including:
• YouTube
• Instagram  
• Facebook
• Pinterest
• TikTok
• Twitter/X
• Vimeo
• SoundCloud
• And many more!

📝 *How to use:*
Just send me any media URL and I'll give you options to download as MP3 (audio) or MP4 (video)!

⚡ Fast • 🔒 Secure • 🆓 Free
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message when the command /help is issued."""
    help_text = """
🤖 *Bot Help Guide*

*Supported Platforms:*
- YouTube
- Instagram
- Facebook  
- TikTok
- Twitter/X
- Pinterest
- SoundCloud
- Vimeo
- And 1000+ other sites!

*How to Use:*
1. Send any media URL
2. Choose download format (MP3/MP4)
3. Wait for processing
4. Download your media!

*Formats:*
🎵 MP3 - Audio only
🎬 MP4 - Video with audio

*Need Help?* Contact admin @behar5057
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def is_supported_url(url):
    """Check if the URL is from a supported domain."""
    return any(domain in url.lower() for domain in SUPPORTED_DOMAINS)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text
    
    if not is_supported_url(message_text):
        await update.message.reply_text(
            "❌ *Unsupported URL*\n\n"
            "I currently don't support this platform. "
            "Supported platforms include: YouTube, Instagram, Facebook, TikTok, Twitter, etc.",
            parse_mode='Markdown'
        )
        return
    
    # Create format selection buttons
    keyboard = [
        [
            InlineKeyboardButton("🎵 MP3 (Audio)", callback_data=f"mp3|{message_text}"),
            InlineKeyboardButton("🎬 MP4 (Video)", callback_data=f"mp4|{message_text}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📥 *Download Options*\n\n"
        "Choose your preferred format:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    format_type, url = data.split('|', 1)
    
    await query.edit_message_text(
        f"⏳ *Processing your {format_type.upper()} download...*\n\n"
        "This may take a few moments depending on the video length.",
        parse_mode='Markdown'
    )
    
    try:
        file_path = await download_media(url, format_type, context)
        
        if file_path:
            if format_type == 'mp3':
                await query.message.reply_audio(
                    audio=open(file_path, 'rb'),
                    caption=f"🎵 Your audio is ready!\n\n🔗 Original URL: {url}"
                )
            else:  # mp4
                await query.message.reply_video(
                    video=open(file_path, 'rb'),
                    caption=f"🎬 Your video is ready!\n\n🔗 Original URL: {url}",
                    supports_streaming=True
                )
            
            # Clean up file
            os.remove(file_path)
            
            # Notify admin
            if str(query.from_user.id) != str(ADMIN_ID):
                await context.bot.send_message(
                    ADMIN_ID,
                    f"📥 Download completed!\n"
                    f"User: @{query.from_user.username or query.from_user.id}\n"
                    f"Format: {format_type.upper()}\n"
                    f"URL: {url}"
                )
        else:
            await query.message.reply_text("❌ Download failed. Please try again later.")
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.message.reply_text(
            "❌ *Download Failed*\n\n"
            "This might be due to:\n"
            "• Private/restricted content\n"
            "• Unsupported format\n"
            "• Network issues\n"
            "• File too large\n\n"
            "Try another URL or contact support.",
            parse_mode='Markdown'
        )

async def download_media(url, format_type, context):
    """Download media using yt-dlp."""
    try:
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
        else:  # mp4
            ydl_opts = {
                'format': 'best[height<=720]',  # Limit to 720p for smaller files
                'outtmpl': 'downloads/%(title).50s.%(ext)s',
                'merge_output_format': 'mp4',
                'quiet': True,
            }
        
        # Create downloads directory
        os.makedirs('downloads', exist_ok=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            if format_type == 'mp3':
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            
            return file_path
            
    except Exception as e:
        logger.error(f"YT-DLP Error: {e}")
        return None

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and send error messages."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Notify admin of errors
    await context.bot.send_message(
        ADMIN_ID,
        f"🚨 Bot Error:\n{context.error}"
    )

def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)
    
    # Start bot
    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
