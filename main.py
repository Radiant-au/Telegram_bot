"""
Main bot entry point
Initialize and run the Telegram bot
"""
from telegram.ext import (
    Application, ChatMemberHandler, MessageHandler,
    filters, CommandHandler, ConversationHandler
)

# Import configuration
from config import (
    TELEGRAM_TOKEN, MODE, PORT, WEBHOOK_URL, AI_ENABLED,
    CHOOSING_ACTION, ANNOUNCEMENT_TEXT, POLL_QUESTION, POLL_OPTIONS,
    print_config
)

# Import handlers
from handlers.admin import (
    start_command, choose_action, handle_announcement,
    handle_poll_question, handle_poll_options, cancel
)
from handlers.members import on_new_member, get_user_info, handle_help
from handlers.ai_handler import (
    handle_ai_command, handle_ai_tokens,
    handle_switch_llm, handle_llm_status
)

def create_application():
    """Create and configure the bot application"""
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
    application.add_handler(CommandHandler('getinfo', get_user_info))
    application.add_handler(CommandHandler('help', handle_help))
    
    # AI handlers (if enabled)
    if AI_ENABLED:
        application.add_handler(CommandHandler('miki', handle_ai_command))
        application.add_handler(CommandHandler('tokens', handle_ai_tokens)) 
        application.add_handler(CommandHandler('switchllm', handle_switch_llm))
        application.add_handler(CommandHandler('llmstatus', handle_llm_status))
    
    return application

def main():
    """Main function to run the bot"""
    # Print configuration
    print_config()
    
    # Create application
    application = create_application()
    
    print("="*50)
    print("🤖 BOT IS RUNNING!")
    print("="*50)
    print("\n✅ Features loaded:")
    print("   • New member announcements")
    print("   • @all mentions with separate notification")
    print("   • Admin panel (/start) - Owner only")
    print("   • Announcements & Polls")
    print("   • Fun greetings & reactions")
    if AI_ENABLED:
        print("   • AI Chat (Gemini) - /ai command")
        print("   • Token system: 3 tokens/day per user")
        print("   • Admins: Unlimited tokens")
    print("\n" + "="*50 + "\n")
    
    # Run in selected mode
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
        
        # Start webhook server
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/telegram",
            webhook_url=f"{WEBHOOK_URL}/telegram" if WEBHOOK_URL else None,
            drop_pending_updates=True
        )
    else:
        print(f"📡 Starting in POLLING mode (for local testing)...")
        print("   Bot will continuously check for updates")
        print("\n" + "="*50)
        print("Waiting for messages...\n")
        
        application.run_polling(allowed_updates=["chat_member", "message"])

if __name__ == '__main__':
    main()