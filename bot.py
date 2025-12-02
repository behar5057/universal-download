import os
import logging
import yt_dlp
import hashlib
import threading
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from flask import Flask

# Bot configuration
BOT_TOKEN = "8268332814:AAGhskQ16kgCieoz8BBHX6iQWxDEGt5XPxg"
ADMIN_ID = 6120264201

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for web server
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Universal Downloader Bot is running! Send any URL to download."

def keep_alive():
    """Ping the Render URL every 10 minutes to keep it awake."""
    while True:
        try:
            requests.get("https://universal-download.onrender.com", timeout=10)
            print(f"✅ Pinged at {time.strftime('%H:%M:%S')}")
        except:
            print("⚠️ Ping failed")
        time.sleep(600)  # 10 minutes

def start_flask():
    """Start Flask web server."""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# Store URLs temporarily
user_urls = {}

def get_url_hash(url):
    """Create a short hash for the URL."""
    return hashlib.md5(url.encode()).hexdigest()[:10]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    welcome_text = """
🎬 *UNIVERSAL DOWNLOADER BOT* 🎵

I can download ANYTHING from ANY platform:
• Videos (YouTube, Instagram, TikTok, Facebook, Twitter, etc.)
• Music/MP3 from any video
• Pictures/Photos
• Reels, Stories, Posts
• And much more!

📝 *How to use:*
Just send me ANY media URL and I'll download it for you!

⚡ Fast • 🔒 Secure • 🆓 Free

🔗 *Examples:*
- YouTube: https://www.youtube.com/watch?v=...
- Instagram: https://www.instagram.com/p/... or /reel/...
- TikTok: https://www.tiktok.com/@.../video/...
- Twitter: https://twitter.com/.../status/...
- Facebook: https://facebook.com/watch/?v=...
- Pinterest: https://pinterest.com/pin/...
- Reddit: https://reddit.com/r/.../comments/...
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    logger.info("Start command received")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text.strip()
    logger.info(f"Received: {message_text}")
    
    # Check if it's a URL
    if any(prefix in message_text for prefix in ['http://', 'https://', 'www.']):
        url_hash = get_url_hash(message_text)
        user_urls[url_hash] = message_text
        
        # Create download options based on URL type
        keyboard = []
        
        # Always offer MP4/Video option
        keyboard.append([InlineKeyboardButton("🎬 Download Video", callback_data=f"video|{url_hash}")])
        
        # Offer MP3 for platforms that likely have audio
        if any(platform in message_text for platform in ['youtube', 'youtu.be', 'instagram', 'tiktok', 'facebook', 'twitter', 'soundcloud']):
            keyboard.append([InlineKeyboardButton("🎵 Download MP3/Audio", callback_data=f"audio|{url_hash}")])
        
        # Offer Image option for image platforms
        if any(platform in message_text for platform in ['instagram.com/p/', 'pinterest', 'imgur', 'flickr']):
            keyboard.append([InlineKeyboardButton("🖼️ Download Image", callback_data=f"image|{url_hash}")])
        
        # Best quality option
        keyboard.append([InlineKeyboardButton("⭐ Best Quality", callback_data=f"best|{url_hash}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📥 *Download Options*\n\nURL: `{message_text}`\n\nChoose what you want to download:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Please send a valid URL starting with http:// or https://\n\n"
            "Examples:\n"
            "• https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
            "• https://www.instagram.com/reel/...\n"
            "• https://www.tiktok.com/@.../video/...",
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
            await query.edit_message_text("❌ URL expired. Please send the URL again.")
            return
        
        format_names = {
            'video': 'Video',
            'audio': 'Audio/MP3', 
            'image': 'Image',
            'best': 'Best Quality'
        }
        
        await query.edit_message_text(f"⏳ Downloading {format_names.get(format_type, format_type)}...\n\nURL: {original_url}")
        
        # Download the media
        file_path = download_media(original_url, format_type)
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            
            # Check file size limit (50MB for Telegram)
            if file_size > 50:
                await query.message.reply_text(
                    f"❌ File too large ({file_size:.1f}MB). Telegram limit is 50MB.\n"
                    f"Try downloading audio or lower quality."
                )
                os.remove(file_path)
                return
            
            # Send based on file type
            if file_path.endswith('.mp3') or file_path.endswith('.m4a'):
                with open(file_path, 'rb') as audio_file:
                    await query.message.reply_audio(
                        audio=audio_file,
                        caption=f"🎵 Your audio is ready!\n\n🔗 {original_url}"
                    )
            elif file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                with open(file_path, 'rb') as image_file:
                    await query.message.reply_photo(
                        photo=image_file,
                        caption=f"🖼️ Your image is ready!\n\n🔗 {original_url}"
                    )
            else:  # Video or other files
                with open(file_path, 'rb') as media_file:
                    await query.message.reply_document(
                        document=media_file,
                        caption=f"📁 Your media is ready!\n\n🔗 {original_url}"
                    )
            
            # Clean up
            os.remove(file_path)
            logger.info(f"Successfully sent {format_type}")
            
        else:
            await query.message.reply_text(
                "❌ Download failed. This might be due to:\n"
                "• Private/restricted content\n"
                "• Unsupported platform\n"
                "• Network issues\n"
                "• File too large\n\n"
                "Try another URL or platform.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.message.reply_text(
            "❌ Error processing your request. Please try again with a different URL.",
            parse_mode='Markdown'
        )

def download_media(url, format_type):
    """Download media using yt-dlp with universal settings."""
    try:
        os.makedirs('downloads', exist_ok=True)
        
        # Universal downloader options
        ydl_opts = {
            'outtmpl': 'downloads/%(title).100s.%(ext)s',
            'quiet': True,
            'no_warnings': False,
            'format': 'best',  # Get the best available
            'merge_output_format': 'mp4',
            'windowsfilenames': True,
            'restrictfilenames': True,
        }
        
        # Special handling for different formats
        if format_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif format_type == 'image':
            ydl_opts.update({
                'format': 'best[ext=jpg]/best[ext=png]/best[ext=webp]/best',
            })
        elif format_type == 'video':
            ydl_opts.update({
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            })
        elif format_type == 'best':
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
            })
        
        # Platform-specific optimizations
        if 'instagram.com' in url:
            ydl_opts.update({
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            })
        elif 'twitter.com' in url or 'x.com' in url:
            ydl_opts.update({
                'format': 'best',
            })
        elif 'tiktok.com' in url:
            ydl_opts.update({
                'format': 'best',
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Handle audio conversion
            if format_type == 'audio' and 'postprocessors' in ydl_opts:
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            
            return file_path
            
    except Exception as e:
        logger.error(f"Download error for {url}: {e}")
        
        # Try a simpler approach if the first one fails
        try:
            return simple_download(url, format_type)
        except:
            return None

def simple_download(url, format_type):
    """Simple download as fallback."""
    try:
        os.makedirs('downloads', exist_ok=True)
        
        simple_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'best',
        }
        
        with yt_dlp.YoutubeDL(simple_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except:
        return None

def main():
    """Start everything."""
    print("🚀 Starting Universal Downloader Bot...")
    print("📥 Can download: Videos, Music, Images from ANY platform!")
    
    # Start keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Create Telegram application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot
    print("🤖 Bot is running! Send ANY URL to download.")
    print("🌐 Web server: https://universal-download.onrender.com")
    application.run_polling()

if __name__ == '__main__':
    main()
