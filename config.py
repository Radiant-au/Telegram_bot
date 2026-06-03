"""
Configuration management for Telegram Bot
Load environment variables and bot settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# TELEGRAM SETTINGS
# ============================================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))

# ============================================================================
# AI SETTINGS (Multi-LLM Support)
# ============================================================================
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
QWEN_API_KEY = os.getenv('QWEN_API_KEY')

# Default LLM provider ('gemini', 'deepseek', 'openrouter' or 'qwen')
DEFAULT_LLM = os.getenv('DEFAULT_LLM', 'gemini').lower()

# AI is enabled if at least one API key is present
AI_ENABLED = bool(GEMINI_API_KEY or DEEPSEEK_API_KEY or OPENROUTER_API_KEY or QWEN_API_KEY)

# ============================================================================
# GOOGLE SHEETS SETTINGS
# ============================================================================
import json
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS')
GOOGLE_CREDENTIALS = json.loads(GOOGLE_CREDENTIALS_JSON) if GOOGLE_CREDENTIALS_JSON else None
SHEET_NAME = os.getenv('SHEET_NAME')

# ============================================================================
# GROUP SETTINGS
# ============================================================================
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', 0))
ANNOUNCEMENT_TOPIC_ID = int(os.getenv('ANNOUNCEMENT_TOPIC_ID', 2))
MEMBER_TOPIC_ID = int(os.getenv('MEMBER_TOPIC_ID', 2))

# ============================================================================
# DEPLOYMENT SETTINGS
# ============================================================================
MODE = os.getenv('MODE', 'polling')  # 'webhook' or 'polling'
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 8080))

# ============================================================================
# CONVERSATION STATES
# ============================================================================
CHOOSING_ACTION = 0
ANNOUNCEMENT_TEXT = 1
POLL_QUESTION = 2
POLL_OPTIONS = 3

# ============================================================================
# VALIDATION
# ============================================================================
def validate_config():
    """Validate critical configuration"""
    errors = []
    
    if not TELEGRAM_TOKEN:
        errors.append("❌ TELEGRAM_TOKEN not set")
    
    if not BOT_OWNER_ID:
        errors.append("⚠️  BOT_OWNER_ID not set (admin features won't work)")
    
    if not AI_ENABLED:
        errors.append("⚠️  No AI API keys set (AI features disabled)")
    
    if DEFAULT_LLM not in ['gemini', 'deepseek', 'openrouter', 'qwen']:
        errors.append(f"⚠️  Invalid DEFAULT_LLM: {DEFAULT_LLM} (must be 'gemini', 'deepseek', 'openrouter' or 'qwen')")
    
    if not GOOGLE_CREDENTIALS:
        errors.append("⚠️  GOOGLE_CREDENTIALS not set (sheets features disabled)")
    
    if MODE == 'webhook' and not WEBHOOK_URL:
        errors.append("❌ WEBHOOK_URL required for webhook mode")
    
    return errors

def print_config():
    """Print current configuration"""
    print("\n" + "="*50)
    print("⚙️  CONFIGURATION")
    print("="*50)
    print(f"✅ Telegram Token: {'*' * 20}{TELEGRAM_TOKEN[-10:] if TELEGRAM_TOKEN else 'None'}")
    print(f"✅ Sheet Name: {SHEET_NAME}")
    print(f"✅ Bot Owner ID: {BOT_OWNER_ID}")
    print(f"✅ Group Chat ID: {GROUP_CHAT_ID if GROUP_CHAT_ID else 'Not set'}")
    print(f"✅ Announcement Topic: {ANNOUNCEMENT_TOPIC_ID}")
    print(f"✅ MEMBER Topic: {MEMBER_TOPIC_ID}")
    print(f"✅ AI Enabled: {AI_ENABLED}")
    if AI_ENABLED:
        if GEMINI_API_KEY:
            print(f"✅ Gemini API Key: {'*' * 20}{GEMINI_API_KEY[-10:]}")
        if DEEPSEEK_API_KEY:
            print(f"✅ DeepSeek API Key: {'*' * 20}{DEEPSEEK_API_KEY[-10:]}")
        if OPENROUTER_API_KEY:
            print(f"✅ OpenRouter API Key: {'*' * 20}{OPENROUTER_API_KEY[-10:]}")
        if QWEN_API_KEY:
            print(f"✅ Qwen API Key: {'*' * 20}{QWEN_API_KEY[-10:]}")
    print(f"✅ Mode: {MODE}")
    if MODE == 'webhook':
        print(f"✅ Webhook URL: {WEBHOOK_URL if WEBHOOK_URL else 'Not set'}")
        print(f"✅ Port: {PORT}")
    print("="*50 + "\n")

# Print configuration status
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 BOT CONFIGURATION")
    print("=" * 60)
    print(f"Mode: {MODE}")
    print(f"Telegram Token: {'✅ Set' if TELEGRAM_TOKEN else '❌ Missing'}")
    print(f"Bot Owner ID: {BOT_OWNER_ID if BOT_OWNER_ID else '❌ Not set'}")
    print()
    print("AI Configuration:")
    print(f"  Gemini API: {'✅ Set' if GEMINI_API_KEY else '❌ Not set'}")
    print(f"  DeepSeek API: {'✅ Set' if DEEPSEEK_API_KEY else '❌ Not set'}")
    print(f"  OpenRouter API: {'✅ Set' if OPENROUTER_API_KEY else '❌ Not set'}")
    print(f"  Qwen API: {'✅ Set' if QWEN_API_KEY else '❌ Not set'}")
    print(f"  Default LLM: {DEFAULT_LLM}")
    print(f"  AI Enabled: {AI_ENABLED}")
    print()
    print(f"Google Sheets: {'✅ Configured' if GOOGLE_CREDENTIALS else '❌ Not configured'}")
    print(f"Sheet Name: {SHEET_NAME if SHEET_NAME else '❌ Not set'}")
    print()
    print(f"Group Chat ID: {GROUP_CHAT_ID if GROUP_CHAT_ID else '❌ Not set'}")
    print("=" * 60)
    
    errors = validate_config()
    if errors:
        print("\n⚠️  Configuration Issues:")
        for error in errors:
            print(f"  {error}")
    else:
        print("\n✅ Configuration valid!")