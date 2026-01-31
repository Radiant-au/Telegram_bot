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
    Handle /miki command
    Usage: /miki What is Python?
    """
    if not AI_ENABLED:
        await update.message.reply_text(
            "❌ AI features are currently disabled.\n"
            "Contact the bot owner to enable them!"
        )
        return
    
    # Get the question (everything after /miki)
    if not context.args:
        await update.message.reply_text(
            "💡 **How to use AI:**\n\n"
            "`/miki <your question>`\n\n"
            "**Examples:**\n"
            "• `/miki What is Python?`\n"
            "• `/miki Explain quantum computing`\n"
            "• `/miki Write a poem about coding`\n\n"
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
            "Use `/miki <question>` anytime!"
        )
    else:
        remaining = ai_manager.get_remaining_tokens(user_id, is_owner)
        await update.message.reply_text(
            f"🎟️ **Your AI Tokens**\n\n"
            f"Remaining: **{remaining}/3**\n"
            f"Resets: Midnight 🌙\n\n"
            f"Use `/miki <question>` to ask anything!"
        )