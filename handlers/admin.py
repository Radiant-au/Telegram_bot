"""
Admin panel handlers
Handle announcements and polls (owner-only)
"""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    BOT_OWNER_ID, ANNOUNCEMENT_TOPIC_ID,
    CHOOSING_ACTION, ANNOUNCEMENT_TEXT, POLL_QUESTION, POLL_OPTIONS
)
from utils import get_group_chat_id

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command - only for bot owner
    Show admin menu
    """
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
        "👑 Welcome AKS! What would you like to do?",
        reply_markup=reply_markup
    )
    
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's choice from the menu"""
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
    group_chat_id = get_group_chat_id()
    
    if not group_chat_id:
        await update.message.reply_text(
            "❌ I don't know which group to post to yet!\n"
            "Please wait for someone to join the group first, or send a message in the group."
        )
        return ConversationHandler.END
    
    try:
        # Post to ANNOUNCEMENT topic
        await context.bot.send_message(
            chat_id=group_chat_id,
            message_thread_id=ANNOUNCEMENT_TOPIC_ID,
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
    group_chat_id = get_group_chat_id()
    
    if not group_chat_id:
        await update.message.reply_text("❌ I don't know which group to post to yet!")
        return ConversationHandler.END
    
    try:
        # Create poll in ANNOUNCEMENT topic
        await context.bot.send_poll(
            chat_id=group_chat_id,
            message_thread_id=ANNOUNCEMENT_TOPIC_ID,
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