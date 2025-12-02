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

I can download ANYTHING from ANY platform!

📝 *How to use:*
1. Send me ANY media URL
2. Choose download option
3. Get your file!

✅ *Working Platforms:*
• YouTube (Videos & MP3)
• Instagram (Reels, Posts, Stories)
• TikTok (Videos)
• Twitter/X (Videos, Images)
• Facebook (Videos)
• Pinterest (Images)
• Reddit (Videos, Images)
• SoundCloud (Music)
• And 1000+ more sites!

⚡ Fast • 🔒 Secure • 🆓 Free
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    logger.info("Start command received")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text.strip()
    logger.info(f"Received URL: {message_text}")
    
    # Check if it's a URL
    if message_text.startswith(('http://', 'https://', 'www.')):
        # Clean the URL
        if message_text.startswith('www.'):
            message_text = 'https://' + message_text
        
        url_hash = get_url_hash(message_text)
        user_urls[url_hash] = message_text
        
        # Create download options
        keyboard = [
            [InlineKeyboardButton("🎬 Download Video", callback_data=f"video|{url_hash}")],
            [InlineKeyboardButton("🎵 Download MP3/Audio", callback_data=f"audio|{url_hash}")],
            [InlineKeyboardButton("🖼️ Try Download", callback_data=f"try|{url_hash}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📥 *URL Received*\n\n`{message_text}`\n\nChoose download option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Please send a valid URL.\n\n"
            "Examples:\n"
            "• https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
            "• https://www.instagram.com/reel/Cx9JtVpMhQy/\n"
            "• https://twitter.com/.../status/...",
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
            await query.edit_message_text("❌ URL expired. Please send it again.")
            return
        
        format_names = {
            'video': 'Video',
            'audio': 'Audio/MP3', 
            'try': 'Media'
        }
        
        await query.edit_message_text(f"🔄 *Downloading {format_names.get(format_type, format_type)}...*\n\n`{original_url}`\n\n⏳ Please wait...", parse_mode='Markdown')
        
        # Download the media with multiple attempts
        file_path = None
        error_msg = None
        
        if format_type == 'try':
            # Try multiple approaches
            for attempt in ['video', 'audio', 'image']:
                file_path = download_media(original_url, attempt)
                if file_path and os.path.exists(file_path):
                    format_type = attempt
                    break
        
        if not file_path:
            file_path = download_media(original_url, format_type)
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            
            # Check file size
            if file_size > 50:
                await query.message.reply_text(
                    f"❌ File too large ({file_size:.1f}MB). Telegram limit is 50MB.\n"
                    f"Try downloading audio instead."
                )
                os.remove(file_path)
                return
            
            # Send the file
            await send_file(query.message, file_path, original_url, format_type)
            
            # Clean up
            os.remove(file_path)
            logger.info(f"Successfully sent {format_type}")
            
        else:
            # Try direct download as last resort
            await query.message.reply_text("🔄 Trying alternative download method...")
            file_path = direct_download(original_url)
            
            if file_path and os.path.exists(file_path):
                await send_file(query.message, file_path, original_url, 'direct')
                os.remove(file_path)
            else:
                await query.message.reply_text(
                    "❌ *Could not download this content*\n\n"
                    "Possible reasons:\n"
                    "• Content is private/restricted\n"
                    "• Platform blocks downloads\n"
                    "• URL format not supported\n"
                    "• Server timeout\n\n"
                    "💡 *Try:*\n"
                    "1. Different URL from same platform\n"
                    "2. YouTube URLs work best\n"
                    "3. Check if content is public\n"
                    "4. Try again later",
                    parse_mode='Markdown'
                )
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text(
            "❌ *Download Error*\n\n"
            "Please try:\n"
            "1. A different URL\n"
            "2. YouTube video (most reliable)\n"
            "3. Check your internet connection",
            parse_mode='Markdown'
        )

async def send_file(message, file_path, original_url, format_type):
    """Send file based on its type."""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.mp3', '.m4a', '.ogg', '.wav']:
            with open(file_path, 'rb') as f:
                await message.reply_audio(
                    audio=f,
                    caption=f"🎵 *Audio Downloaded*\n🔗 {original_url}",
                    parse_mode='Markdown'
                )
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            with open(file_path, 'rb') as f:
                await message.reply_photo(
                    photo=f,
                    caption=f"🖼️ *Image Downloaded*\n🔗 {original_url}",
                    parse_mode='Markdown'
                )
        elif file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            with open(file_path, 'rb') as f:
                await message.reply_video(
                    video=f,
                    caption=f"🎬 *Video Downloaded*\n🔗 {original_url}",
                    supports_streaming=True,
                    parse_mode='Markdown'
                )
        else:
            with open(file_path, 'rb') as f:
                await message.reply_document(
                    document=f,
                    caption=f"📁 *File Downloaded*\n🔗 {original_url}",
                    parse_mode='Markdown'
                )
                
    except Exception as e:
        logger.error(f"Send error: {e}")
        # Try as document if other methods fail
        with open(file_path, 'rb') as f:
            await message.reply_document(
                document=f,
                caption=f"📁 Downloaded: {original_url}"
            )

def download_media(url, format_type):
    """Download media using yt-dlp with multiple fallbacks."""
    try:
        os.makedirs('downloads', exist_ok=True)
        
        # Base options
        ydl_opts = {
            'outtmpl': 'downloads/%(title).80s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'extractor_args': {
                'instagram': {
                    'requested_formats': ['dash', 'hls'],
                    'posts': 'single',
                },
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/',
            },
        }
        
        # Format specific options
        if format_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif format_type == 'video':
            ydl_opts.update({
                'format': 'best[height<=720]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            })
        elif format_type == 'image':
            ydl_opts.update({
                'format': 'best[ext=jpg]/best[ext=png]/best[ext=webp]/best',
            })
        else:
            ydl_opts['format'] = 'best'
        
        # Platform specific tweaks
        if 'instagram.com' in url:
            ydl_opts.update({
                'format': 'best',
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            })
        elif 'tiktok.com' in url:
            ydl_opts.update({
                'format': 'best',
            })
        elif 'twitter.com' in url or 'x.com' in url:
            ydl_opts.update({
                'format': 'best',
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if not info:
                return None
                
            file_path = ydl.prepare_filename(info)
            
            # Convert to mp3 if audio was requested
            if format_type == 'audio' and 'postprocessors' in ydl_opts:
                mp3_path = file_path.rsplit('.', 1)[0] + '.mp3'
                if os.path.exists(mp3_path):
                    return mp3_path
            
            return file_path if os.path.exists(file_path) else None
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None

def direct_download(url):
    """Try direct download as last resort."""
    try:
        import random
        import string
        
        os.makedirs('downloads', exist_ok=True)
        
        # Generate random filename
        filename = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        file_path = f"downloads/{filename}.mp4"
        
        # Use yt-dlp with simplest options
        ydl_opts = {
            'outtmpl': file_path,
            'format': 'best',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return file_path if os.path.exists(file_path) else None
            
    except:
        return None

def main():
    """Start everything."""
    print("🚀 Starting Universal Downloader Bot...")
    print("📥 Will try multiple methods to download ANYTHING!")
    
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
    print("🤖 Bot is running! Testing with YouTube...")
    print("🌐 Web server: https://universal-download.onrender.com")
    application.run_polling()

if __name__ == '__main__':
    main()
