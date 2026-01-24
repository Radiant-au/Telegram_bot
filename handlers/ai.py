"""
AI chat handlers
Handle AI interactions in the group
"""
from telegram import Update
from telegram.ext import ContextTypes
from ai import ai_manager
from config import AI_ENABLED

async def handle_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /ai command
    Usage: /ai What is Python?
    """
    if not AI_ENABLED:
        await update.message.reply_text(
            "❌ AI features are currently disabled.\n"
            "Contact the bot owner to enable them!"
        )
        return
    
    # Get the question (everything after /ai)
    if not context.args:
        await update.message.reply_text(
            "💡 **How to use AI:**\n\n"
            "`/ai <your question>`\n\n"
            "**Examples:**\n"
            "• `/ai What is Python?`\n"
            "• `/ai Explain quantum computing`\n"
            "• `/ai Write a poem about coding`\n\n"
            f"📊 You get **3 tokens per day**\n"
            "🔄 Tokens reset at midnight\n"
            "👑 Admins have unlimited tokens"
        )
        return
    
    # Get user info
    user_id = update.effective_user.id
    
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    is_admin = chat_member.status in ['creator']
    
    # Join the question
    question = " ".join(context.args)
    
    # Show "typing..." indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    # Get AI response
    result = await ai_manager.generate_response(question, user_id, is_admin)
    
    # Format response
    if result['success']:
        token_info = f"\n\n🎟️ Tokens left: {result['tokens_left']}" if not is_admin else "\n\n👑 Admin (Unlimited)"
        response_text = f"🤖 **AI Response:**\n\n{result['response']}{token_info}"
    else:
        response_text = result['response']
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

async def handle_ai_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /tokens command
    Check remaining AI tokens
    """
    if not AI_ENABLED:
        await update.message.reply_text("❌ AI features are currently disabled.")
        return
    
    user_id = update.effective_user.id
    
    # Check if admin
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    is_owner = chat_member.status in ['creator']
    
    if is_owner:
        await update.message.reply_text(
            "👑 **Admin Status**\n\n"
            "You have **unlimited AI tokens**! 🎉\n\n"
            "Use `/ai <question>` anytime!"
        )
    else:
        remaining = ai_manager.get_remaining_tokens(user_id, is_owner)
        await update.message.reply_text(
            f"🎟️ **Your AI Tokens**\n\n"
            f"Remaining: **{remaining}/3**\n"
            f"Resets: Midnight 🌙\n\n"
            f"Use `/ai <question>` to ask anything!"
        )

async def handle_ai_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /aihelp command
    Show AI usage guide
    """
    if not AI_ENABLED:
        await update.message.reply_text("❌ AI features are currently disabled.")
        return
    
    user_id = update.effective_user.id
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    is_admin = chat_member.status in ['administrator', 'creator']
    
    help_text = f"""
🤖 **AI Assistant Help**

**Commands:**
• `/ai <question>` - Ask the AI anything
• `/tokens` - Check remaining tokens
• `/aihelp` - Show this help message

**Usage Examples:**
• `/ai What is machine learning?`
• `/ai Explain blockchain simply`
• `/ai Write a haiku about technology`
• `/ai Help me debug this code: ...`

**Token System:**
{"👑 You have unlimited tokens (Admin)" if is_admin else "🎟️ You get 3 tokens per day"}
🔄 Tokens reset at midnight
💡 Use tokens wisely!

**Tips:**
• Be specific with your questions
• You can ask about coding, tech, science, etc.
• The AI is powered by Google Gemini

Happy chatting! 🚀
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')