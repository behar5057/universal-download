import os
import logging
import yt_dlp
import requests
import re
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

# Supported domains - expanded list
SUPPORTED_DOMAINS = [
    'youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 
    'fb.watch', 'pinterest.com', 'tiktok.com', 'twitter.com', 'x.com',
    'vimeo.com', 'soundcloud.com', 'twitch.tv', 'dailymotion.com',
    'reddit.com', 'linkedin.com', 'vk.com', 'likee.com', 'ok.ru'
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
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def is_valid_url(text):
    """Check if text contains a valid URL."""
    url_pattern = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'(([A-Z0-9-]+\.)+[A-Z]{2,})'  # domain
        r'(/[\w\-\.~!*\'();:@&=+$,/?%#[\]]*)?$',  # path
        re.IGNORECASE
    )
    return bool(url_pattern.match(text.strip()))

def is_supported_url(url):
    """Check if the URL is from a supported domain."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in SUPPORTED_DOMAINS)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    try:
        message_text = update.message.text.strip()
        logger.info(f"Received message: {message_text}")
        
        # Check if it's a valid URL
        if not is_valid_url(message_text):
            await update.message.reply_text(
                "❌ *Invalid URL Format*\n\n"
                "Please send a valid URL starting with http:// or https://",
                parse_mode='Markdown'
            )
            return
        
        # Check if it's supported
        if not is_supported_url(message_text):
            await update.message.reply_text(
                "❌ *Unsupported Platform*\n\n"
                "I currently don't support this platform. "
                "Supported platforms include:\n"
                "• YouTube, Instagram, Facebook\n"
                "• TikTok, Twitter/X, Pinterest\n"
                "• SoundCloud, Vimeo, and many more!",
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
            f"📥 *Download Options*\n\n"
            f"URL: `{message_text}`\n\n"
            f"Choose your preferred format:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text(
            "❌ *Error processing URL*\n\n"
            "Please make sure the URL is correct and try again.",
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
            f"⏳ *Processing your {format_type.upper()} download...*\n\n"
            f"URL: `{url}`\n"
            "This may take a few moments depending on the media size.",
            parse_mode='Markdown'
        )
        
        # Download the media
        file_path = await download_media(url, format_type)
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            
            if file_size > 50:  # Telegram file size limit ~50MB
                await query.message.reply_text(
                    "❌ *File Too Large*\n\n"
                    "The downloaded file exceeds Telegram's size limit (50MB).\n"
                    "Try downloading as MP3 or try a shorter video.",
                    parse_mode='Markdown'
                )
                os.remove(file_path)
                return
            
            if format_type == 'mp3':
                await query.message.reply_audio(
                    audio=open(file_path, 'rb'),
                    caption=f"🎵 *Your audio is ready!*\n\n🔗 Original URL: {url}",
                    parse_mode='Markdown'
                )
            else:  # mp4
                await query.message.reply_video(
                    video=open(file_path, 'rb'),
                    caption=f"🎬 *Your video is ready!*\n\n🔗 Original URL: {url}",
                    supports_streaming=True,
                    parse_mode='Markdown'
                )
            
            # Clean up file
            os.remove(file_path)
            
            logger.info(f"Successfully sent {format_type} for {url}")
            
        else:
            await query.message.reply_text(
                "❌ *Download Failed*\n\n"
                "This might be due to:\n"
                "• Private/restricted content\n"
                "• Unsupported format\n"
                "• Network issues\n"
                "• Platform restrictions\n\n"
                "Try another URL or contact support.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        await query.message.reply_text(
            "❌ *Processing Error*\n\n"
            "An error occurred while processing your request. Please try again.",
            parse_mode='Markdown'
        )

async def download_media(url, format_type):
    """Download media using yt-dlp."""
    try:
        # Create downloads directory
        os.makedirs('downloads', exist_ok=True)
        
        if format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title).100s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': False,
            }
        else:  # mp4
            ydl_opts = {
                'format': 'best[height<=720]/best',  # Prefer up to 720p
                'outtmpl': 'downloads/%(title).100s.%(ext)s',
                'merge_output_format': 'mp4',
                'quiet': False,
                'no_warnings': False,
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
    """Log errors and send error messages."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_error_handler(error_handler)
        
        # Start bot
        print("🤖 Bot is running and waiting for messages...")
        logger.info("Bot started successfully")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"Bot failed to start: {e}")

if __name__ == '__main__':
    main()
