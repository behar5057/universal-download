import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ⚠️ ⚠️ ⚠️ REPLACE THIS WITH YOUR NEW TOKEN ⚠️ ⚠️ ⚠️
BOT_TOKEN = "YOUR_NEW_BOT_TOKEN_HERE"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🎬 *UNIVERSAL DOWNLOADER BOT* 🎵

I can download videos and audio from any platform!

📝 *How to use:*
1. Send me any media URL
2. Choose MP3 or MP4
3. Get your file!

✅ *Working Platforms:*
• YouTube
• Instagram
• TikTok
• Twitter/X
• Facebook
• And 1000+ more!

⚡ Fast • 🔒 Secure • 🆓 Free
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    
    if message_text.startswith(('http://', 'https://')):
        keyboard = [
            [
                InlineKeyboardButton("🎬 MP4 Video", callback_data=f"mp4|{message_text}"),
                InlineKeyboardButton("🎵 MP3 Audio", callback_data=f"mp3|{message_text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📥 *Download Options*\n\n`{message_text}`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        format_type, url = data.split('|', 1)
        
        await query.edit_message_text(f"⏳ *Downloading {format_type.upper()}...*\n\nPlease wait...", parse_mode='Markdown')
        
        # For now, just send a test message
        if format_type == 'mp3':
            await query.message.reply_text(f"🎵 MP3 download for:\n{url}\n\n(This is a test - real download will work after setup)")
        else:
            await query.message.reply_text(f"🎬 MP4 download for:\n{url}\n\n(This is a test - real download will work after setup)")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text("❌ Error. Please try again.")

def main():
    print("🤖 Starting Universal Downloader Bot...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        print(f"✅ Bot token: {BOT_TOKEN[:10]}...")
        print("🤖 Bot is running and waiting for messages...")
        print("💡 Send /start to test")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔄 Restarting in 10 seconds...")
        import time
        time.sleep(10)
        main()

if __name__ == '__main__':
    main()
