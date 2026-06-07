"""
Main bot entry point
Initialize and run the Telegram bot
"""
import logging
import os
from telegram.ext import (
    Application, ChatMemberHandler, MessageHandler,
    filters, CommandHandler, ConversationHandler
)

# ─────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────

def setup_logging():
    """Configure root logger for the whole application."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file  = os.getenv("LOG_FILE", "")   # e.g. "bot.log" — empty = console only
    numeric_level = getattr(logging, log_level, logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=numeric_level,
        format=fmt,
        datefmt=datefmt,
        handlers=handlers,
        force=True,
    )

    if numeric_level > logging.DEBUG:
        # Silence overly verbose third-party loggers during normal runs.
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("telegram").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)

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
    handle_ai_command, handle_ai_tokens, handle_know_me,
    handle_switch_llm, handle_llm_status
)
from handlers.quiz_handler import register_quiz_handlers

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
        application.add_handler(CommandHandler('knowme', handle_know_me))
        application.add_handler(CommandHandler('switchllm', handle_switch_llm))
        application.add_handler(CommandHandler('llmstatus', handle_llm_status))
    
    # Quiz handler (always available if AI is enabled)
    if AI_ENABLED:
        register_quiz_handlers(application)
    
    return application

def main():
    """Main function to run the bot"""
    # Print configuration
    print_config()
    
    # Create application
    application = create_application()
    
    logger.info("🤖 BOT IS RUNNING!")
    logger.info("Features loaded: new-member announcements, admin panel, announcements & polls, fun greetings")
    if AI_ENABLED:
        logger.info("AI features loaded: /miki, /tokens, /switchllm, /quiz")
    
    # Run in selected mode
    if MODE == 'webhook':
        logger.info("Starting in WEBHOOK mode on 0.0.0.0:%s", PORT)
        if WEBHOOK_URL:
            logger.info("Webhook URL: %s/telegram (will be set automatically)", WEBHOOK_URL)
        else:
            logger.warning("WEBHOOK_URL not set — set it manually via setWebhook API call")
        
        # Start webhook server
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/telegram",
            webhook_url=f"{WEBHOOK_URL}/telegram" if WEBHOOK_URL else None,
            drop_pending_updates=True
        )
    else:
        logger.info("Starting in POLLING mode — waiting for messages...")
        application.run_polling(allowed_updates=["chat_member", "message"])

if __name__ == '__main__':
    main()
