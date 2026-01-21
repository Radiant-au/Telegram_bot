from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Poll
from telegram.ext import (
    Application, ChatMemberHandler, ContextTypes, MessageHandler, 
    filters, CommandHandler, ConversationHandler
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from dotenv import load_dotenv
import re
import random

# Load environment variables
load_dotenv()

# ============================================
# 🔧 CONFIGURATION - CHANGE THESE VALUES!
# ============================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
SHEET_NAME = os.getenv('SHEET_NAME')

# 👇 ADD YOUR TELEGRAM USER ID HERE (get it from @userinfobot)
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))  # ⚠️ CHANGE THIS!

# 👇 ADD YOUR ANNOUNCEMENT TOPIC ID HERE (right-click topic → copy link → check ID)
ANNOUNCEMENT_TOPIC_ID = int(os.getenv('ANNOUNCEMENT_TOPIC_ID', '2'))  # ⚠️ CHANGE THIS!

# 👇 ADD YOUR GENERAL/MAIN TOPIC ID HERE (where new members are announced)
GENERAL_TOPIC_ID = int(os.getenv('GENERAL_TOPIC_ID', '2'))  # ⚠️ CHANGE THIS!

# 👇 ADD YOUR GROUP CHAT ID HERE (get it from @raw_data_bot or @userinfobot)
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', '0')) if os.getenv('GROUP_CHAT_ID') else None  # ⚠️ CHANGE THIS!

# 🌐 WEBHOOK SETTINGS
# For local testing: Leave empty or use ngrok URL
# For Cloud Run: Set to your Cloud Run URL
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')  # e.g., https://your-bot.run.app
PORT = int(os.getenv('PORT', 8080))

# Mode: 'webhook' or 'polling' (for local testing you can use polling)
MODE = os.getenv('MODE', 'webhook')  # Change to 'polling' for easy local testing

# ============================================

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN not found!")

print(f"✅ Token loaded")
print(f"✅ Sheet name: {SHEET_NAME}")
print(f"✅ Bot Owner ID: {BOT_OWNER_ID}")
print(f"✅ Group Chat ID: {GROUP_CHAT_ID}")
print(f"✅ Announcement Topic ID: {ANNOUNCEMENT_TOPIC_ID}")
print(f"✅ General Topic ID: {GENERAL_TOPIC_ID}")
print(f"✅ Mode: {MODE}")
if MODE == 'webhook':
    print(f"✅ Webhook URL: {WEBHOOK_URL}")
    print(f"✅ Port: {PORT}")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.getenv('GOOGLE_CREDENTIALS')
if not creds_json:
    raise ValueError("❌ GOOGLE_CREDENTIALS not found!")

creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1
print(f"✅ Connected to Google Sheet")

# Conversation states
CHOOSING_ACTION, ANNOUNCEMENT_TEXT, POLL_QUESTION, POLL_OPTIONS = range(4)

# Store group chat ID - can be overridden by messages
BACKUP_GROUP_ID = GROUP_CHAT_ID  # Keep a backup

def save_group_id(chat_id):
    """Update group chat ID if detected from messages"""
    global GROUP_CHAT_ID
    if GROUP_CHAT_ID is None:  # Only update if not set in .env
        GROUP_CHAT_ID = chat_id
        print(f"✅ Detected Group ID: {chat_id}")

def find_user_data(username):
    """Search for user in Google Sheet by Telegram username"""
    all_records = sheet.get_all_records()
    username_clean = username.lstrip('@').lower()
    
    for record in all_records:
        sheet_username = str(record.get('Telegram username', '')).lstrip('@').lower()
        if sheet_username == username_clean:
            return record
    return None

def format_interests(interests_str):
    """Format the interests field nicely"""
    if not interests_str:
        return "Not specified"
    interests = [i.strip() for i in str(interests_str).split(',')]
    return '\n   • '.join(interests)

async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members joining the group"""
    save_group_id(update.effective_chat.id)  # Save group chat ID permanently
    
    result = update.chat_member
    
    if result.new_chat_member.status in ["member", "administrator"]:
        user = result.new_chat_member.user
        username = user.username
        
        if username:
            user_data = find_user_data(username)
            
            if user_data:
                name = user_data.get('Name', 'N/A')
                phone = user_data.get('Phone', 'N/A')
                major = user_data.get('Major', 'N/A')
                year = user_data.get('Year', 'N/A')
                interests = user_data.get('What fields are u interested in?', 'Not specified')
                
                message = f"""
    🎉 NEW MEMBER ALERT! 🎉
━━━━━━━━━━━━━━━━━━━━━━

👤 𝗡𝗮𝗺𝗲: {name}
📱 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺: @{username}
📞 𝗣𝗵𝗼𝗻𝗲: {phone}

🎓 𝗔𝗰𝗮𝗱𝗲𝗺𝗶𝗰 𝗜𝗻𝗳𝗼:
   • Major: {major}
   • Year: {year}

💻 𝗜𝗻𝘁𝗲𝗿𝗲𝘀𝘁𝗲𝗱 𝗶𝗻:
   • {format_interests(interests)}

━━━━━━━━━━━━━━━━━━━━━━
Welcome to the community! 🚀
"""
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    message_thread_id=GENERAL_TOPIC_ID,  # Posts in general topic
                    text=message
                )

async def mention_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mention all members - IMPROVED VERSION with separate mention message"""
    user = update.effective_user
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
    
    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text("⚠️ Only admins can use @all")
        return
    
    try:
        all_records = sheet.get_all_records()
        mentions = []
        
        for record in all_records:
            username = record.get('Telegram username', '').lstrip('@')
            if username:
                mentions.append(f"@{username}")
        
        if mentions:
            message_parts = update.message.text.split('@all', 1)
            additional_message = message_parts[1].strip() if len(message_parts) > 1 else ""
            
            # Send main message (clean and readable)
            await update.message.reply_text(
                f"📢 **ATTENTION EVERYONE!**\n\n{additional_message}",
                message_thread_id=update.message.message_thread_id
            )
            
            # Send mentions in a separate message (so people get notified)
            mention_text = " ".join(mentions)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                message_thread_id=update.message.message_thread_id,
                text=f"👥 {mention_text}"
            )
            
    except Exception as e:
        print(f"Error in mention_all: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

# ============================================
# ADMIN PANEL: Announcements & Polls
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - only for bot owner"""
    user_id = update.effective_user.id
    
    # Check if user is the bot owner
    if user_id != BOT_OWNER_ID:
        await update.message.reply_text(
            "👋 Hello! I'm the Technologia Club bot!\n\n"
            "I help manage the group. If you need help, contact an admin! 💫"
        )
        return ConversationHandler.END
    
    # Bot owner menu
    keyboard = [
        [KeyboardButton("📢 Make Announcement")],
        [KeyboardButton("📊 Create Poll")],
        [KeyboardButton("❌ Cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "👑 Welcome Boss! What would you like to do?",
        reply_markup=reply_markup
    )
    
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's choice"""
    text = update.message.text
    
    if text == "📢 Make Announcement":
        await update.message.reply_text(
            "📝 Please send me your announcement message.\n\n"
            "I'll post it in the announcement topic!",
            reply_markup=ReplyKeyboardRemove()
        )
        return ANNOUNCEMENT_TEXT
    
    elif text == "📊 Create Poll":
        await update.message.reply_text(
            "❓ What's your poll question?\n\n"
            "Example: What topic should we cover next week?",
            reply_markup=ReplyKeyboardRemove()
        )
        return POLL_QUESTION
    
    elif text == "❌ Cancel":
        await update.message.reply_text(
            "Operation cancelled! 👋",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def handle_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Post announcement to the group in ANNOUNCEMENT topic"""
    announcement_text = update.message.text
    
    if not GROUP_CHAT_ID:
        await update.message.reply_text(
            "❌ I don't know which group to post to yet!\n"
            "Please wait for someone to join the group first, or send a message in the group."
        )
        return ConversationHandler.END
    
    try:
        # Post to ANNOUNCEMENT topic
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=ANNOUNCEMENT_TOPIC_ID,  # Posts in announcement topic
            text=f"📢 **ANNOUNCEMENT**\n━━━━━━━━━━━━━━\n\n{announcement_text}"
        )
        
        await update.message.reply_text(
            "✅ Announcement posted successfully in the announcement topic! 🎉",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error posting announcement: {e}\n\n"
            f"Make sure ANNOUNCEMENT_TOPIC_ID is correct!",
            reply_markup=ReplyKeyboardRemove()
        )
    
    return ConversationHandler.END

async def handle_poll_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save poll question and ask for options"""
    context.user_data['poll_question'] = update.message.text
    
    await update.message.reply_text(
        "Great! Now send me the poll options.\n\n"
        "📝 Format: One option per line\n\n"
        "Example:\n"
        "Web Development\n"
        "AI & Machine Learning\n"
        "Cybersecurity\n"
        "Mobile Development"
    )
    
    return POLL_OPTIONS

async def handle_poll_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create and post the poll in ANNOUNCEMENT topic"""
    options_text = update.message.text
    options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
    
    if len(options) < 2:
        await update.message.reply_text(
            "❌ You need at least 2 options!\n"
            "Please send the options again."
        )
        return POLL_OPTIONS
    
    if len(options) > 10:
        await update.message.reply_text(
            "❌ Maximum 10 options allowed!\n"
            "Please send the options again."
        )
        return POLL_OPTIONS
    
    question = context.user_data.get('poll_question', 'Poll')
    
    if not GROUP_CHAT_ID:
        await update.message.reply_text(
            "❌ I don't know which group to post to yet!"
        )
        return ConversationHandler.END
    
    try:
        # Create poll in ANNOUNCEMENT topic
        await context.bot.send_poll(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=ANNOUNCEMENT_TOPIC_ID,  # Posts in announcement topic
            question=question,
            options=options,
            is_anonymous=False,
            allows_multiple_answers=False
        )
        
        await update.message.reply_text(
            "✅ Poll created successfully in the announcement topic! 📊",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error creating poll: {e}\n\n"
            f"Make sure ANNOUNCEMENT_TOPIC_ID is correct!",
            reply_markup=ReplyKeyboardRemove()
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text(
        "Operation cancelled! 👋",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ============================================
# FUN FEATURES: Greetings and Reactions
# ============================================

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in the group for fun interactions"""
    
    if not update.message or not update.message.text:
        return
    
    # Store and save group chat ID permanently
    if update.effective_chat.type in ['group', 'supergroup']:
        save_group_id(update.effective_chat.id)
    
    text = update.message.text.lower()
    bot_username = context.bot.username.lower()
    
    # Check for @all mention (admin only)
    if '@all' in text:
        await mention_all(update, context)
        return
    
    # Greeting when mentioned
    if f'@{bot_username}' in text or ('hello' in text and bot_username in text):
        greetings = [
            f"Hellooo {update.effective_user.first_name}! 💖✨",
            f"Heyy there {update.effective_user.first_name}! 🌸😊",
            f"Hello hello! {update.effective_user.first_name} 💕",
            f"Aww hey! So nice to hear from you! 🌟💫",
        ]
        await update.message.reply_text(random.choice(greetings))
        return
    
    # Detect "blame @username" pattern
    blame_pattern = r'blame\s+@(\w+)'
    match = re.search(blame_pattern, text)
    
    if match:
        username = match.group(1)
        responses = [
            f"တောသား @{username} 😤",
            f"ဟုတ်ကဲ့ တောသား @{username} 🙄",
            f"@{username} တောသား! 😾",
        ]
        await update.message.reply_text(random.choice(responses))
        return

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Conversation handler for admin panel
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            CHOOSING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            ANNOUNCEMENT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_announcement)],
            POLL_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_poll_question)],
            POLL_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_poll_options)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(ChatMemberHandler(on_new_member, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))
    
    print("\n" + "="*50)
    print("🤖 BOT IS RUNNING!")
    print("="*50)
    print("\n✅ Configuration:")
    print(f"   • Bot Owner ID: {BOT_OWNER_ID}")
    print(f"   • Group Chat ID: {GROUP_CHAT_ID if GROUP_CHAT_ID else 'Not set - will detect automatically'}")
    print(f"   • Announcement Topic: {ANNOUNCEMENT_TOPIC_ID}")
    print(f"   • General Topic: {GENERAL_TOPIC_ID}")
    print(f"   • Mode: {MODE}")
    print("\n✅ Features loaded:")
    print("   • New member announcements (General Topic)")
    print("   • @all mentions with separate notification")
    print("   • Admin panel (/start) - Owner only")
    print("   • Announcements (Announcement Topic)")
    print("   • Polls (Announcement Topic)")
    print("   • Fun greetings & reactions")
    print("\n⚠️  IMPORTANT:")
    print("   • Only you can use /start (your ID is set)")
    print("   • Announcements/Polls go to Announcement Topic")
    print("   • New members announced in General Topic")
    print("\n" + "="*50)
    
    # Choose mode: webhook or polling
    if MODE == 'webhook':
        print(f"🌐 Starting in WEBHOOK mode...")
        print(f"   Listening on: 0.0.0.0:{PORT}")
        
        if WEBHOOK_URL:
            print(f"   Webhook URL: {WEBHOOK_URL}/telegram")
            print("   Webhook will be set automatically")
        else:
            print("⚠️  WEBHOOK_URL not set!")
            print("   Bot will listen for requests but webhook needs to be set manually")
            print("   After deployment, run:")
            print("   curl 'https://api.telegram.org/bot<TOKEN>/setWebhook?url=<YOUR_URL>/telegram'")
        
        print("\n" + "="*50 + "\n")
        
        # Start webhook server (don't set webhook URL yet if not provided)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/telegram",
            webhook_url=f"{WEBHOOK_URL}/telegram" if WEBHOOK_URL else None,
            drop_pending_updates=True  # Skip old updates on startup
        )
    else:
        print(f"📡 Starting in POLLING mode (for local testing)...")
        print("   Bot will continuously check for updates")
        print("\n" + "="*50)
        print("Waiting for messages...\n")
        
        application.run_polling(allowed_updates=["chat_member", "message"])

if __name__ == '__main__':
    main()