"""
Configuration module for Telegram Bot
Load and manage all environment variables and settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# 🔧 TELEGRAM SETTINGS
# ============================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN not found!")

BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

# ============================================
# 📊 GOOGLE SHEETS SETTINGS
# ============================================
SHEET_NAME = os.getenv('SHEET_NAME')
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')

if not GOOGLE_CREDENTIALS:
    raise ValueError("❌ GOOGLE_CREDENTIALS not found!")

# ============================================
# 🤖 GEMINI AI SETTINGS
# ============================================
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
AI_ENABLED = bool(GEMINI_API_KEY)  # Enable AI only if API key is set

# ============================================
# 🎯 TOPIC/CHANNEL SETTINGS
# ============================================
ANNOUNCEMENT_TOPIC_ID = int(os.getenv('ANNOUNCEMENT_TOPIC_ID', '2'))
MEMBER_TOPIC_ID = int(os.getenv('MEMBER_TOPIC_ID', '2'))
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', '0')) if os.getenv('GROUP_CHAT_ID') else None

# ============================================
# 🌐 WEBHOOK SETTINGS
# ============================================
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 8080))
MODE = os.getenv('MODE', 'webhook')  # 'webhook' or 'polling'

# ============================================
# 📝 CONVERSATION STATES
# ============================================
CHOOSING_ACTION = 0
ANNOUNCEMENT_TEXT = 1
POLL_QUESTION = 2
POLL_OPTIONS = 3

def print_config():
    """Print current configuration"""
    print("\n" + "="*50)
    print("⚙️  CONFIGURATION")
    print("="*50)
    print(f"✅ Telegram Token: {'*' * 20}{TELEGRAM_TOKEN[-10:]}")
    print(f"✅ Sheet Name: {SHEET_NAME}")
    print(f"✅ Bot Owner ID: {BOT_OWNER_ID}")
    print(f"✅ Group Chat ID: {GROUP_CHAT_ID if GROUP_CHAT_ID else 'Not set'}")
    print(f"✅ Announcement Topic: {ANNOUNCEMENT_TOPIC_ID}")
    print(f"✅ MEMBER Topic: {MEMBER_TOPIC_ID}")
    print(f"✅ AI Enabled: {AI_ENABLED}")
    if AI_ENABLED:
        print(f"✅ Gemini API Key: {'*' * 20}{GEMINI_API_KEY[-10:]}")
    print(f"✅ Mode: {MODE}")
    if MODE == 'webhook':
        print(f"✅ Webhook URL: {WEBHOOK_URL if WEBHOOK_URL else 'Not set'}")
        print(f"✅ Port: {PORT}")
    print("="*50 + "\n")