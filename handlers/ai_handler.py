"""
AI command handlers for Telegram bot
Handle /miki, /tokens, /knowme, and provider switching commands
"""
from telegram import Update
from telegram.ext import ContextTypes
from ai import ai_manager
from config import BOT_OWNER_ID, DAILY_TOKEN_LIMIT

async def handle_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or ""
    first_name = user.first_name or ""
    is_owner = user.id == BOT_OWNER_ID or await is_admin(update, context)

    # No question — Miki responds in character instead of showing a usage error
    if not context.args:
        remaining = ai_manager.get_remaining_tokens(user.id, is_owner)
        greetings = [
            f"yeah? you called me but said nothing 💀 what do you need",
            f"hello?? don't just summon me and go quiet lol. ask me something",
            f"i'm here, i'm here. what's the question?",
            f"you rang? 👀 ask away, i don't bite (much)",
        ]
        import random
        msg = random.choice(greetings)
        if not is_owner:
            msg += f"\n_(you've got {remaining} questions left today btw)_"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return

    question = ' '.join(context.args)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    result = await ai_manager.generate_response(
        prompt=question,
        user_id=user.id,
        username=username,
        first_name=first_name,
        is_owner=is_owner
    )

    if result['success']:
        response = result['response']

        # Subtle token reminder only when running low — not every single message
        if not is_owner:
            left = result['tokens_left']
            if left <= 3:
                response += f"\n\n_(psst, you only have {left} questions left today)_"
            elif left <= 0:
                response += f"\n\n_(that was your last one for today lol. come back tomorrow)_"
    else:
        response = result['response']

    try:
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        print(f"⚠️ Markdown parse failed: {e}")
        await update.message.reply_text(response)
    """
    Handle /miki command - Ask AI anything
    Usage: /miki <question>
    """
    user = update.effective_user
    username = user.username or ""
    first_name = user.first_name or ""
    is_owner = user.id == BOT_OWNER_ID or await is_admin(update, context)

    # Check if command has a question
    if not context.args:
        await update.message.reply_text(
            "💬 Usage: /miki <your question>\n"
            "Example: /miki What is Python?\n\n"
            f"You have {ai_manager.get_remaining_tokens(user.id, is_owner)} tokens left today."
        )
        return

    # Get the question
    question = ' '.join(context.args)

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Generate response (memory-aware)
    result = await ai_manager.generate_response(
        prompt=question,
        user_id=user.id,
        username=username,
        first_name=first_name,
        is_owner=is_owner
    )

    # Format response with provider info
    if result['success']:
        provider_emojis = {
            'gemini': '🔮',
            'deepseek': '🧠',
            'openrouter': '🌐',
            'qwen': '🐼'
        }
        provider_emoji = provider_emojis.get(result['provider'], '🤖')
        response = f"{result['response']}\n\n"

        if not is_owner:
            response += f"_Tokens left: {result['tokens_left']}/{DAILY_TOKEN_LIMIT}_ | {provider_emoji} {result['provider'].title()}"
        else:
            response += f"_Admin: ∞ tokens_ | {provider_emoji} {result['provider'].title()}"
    else:
        response = result['response']

    try:
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        print(f"⚠️ Telegram Markdown parsing failed: {e}. Falling back to plain text.")
        await update.message.reply_text(response)

async def handle_ai_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /tokens command - Check remaining AI tokens
    """
    user = update.effective_user
    is_owner = user.id == BOT_OWNER_ID or await is_admin(update, context)
    
    remaining = ai_manager.get_remaining_tokens(user.id, is_owner)
    
    if is_owner:
        message = (
            "👑 *Admin Status*\n"
            "You have unlimited AI tokens!\n\n"
            f"Current provider: {ai_manager.get_current_provider().title()}"
        )
    else:
        message = (
            f"🎫 *Your AI Tokens*\n"
            f"Remaining: {remaining}/{DAILY_TOKEN_LIMIT}\n"
            f"Resets: Daily at midnight\n\n"
            f"Current provider: {ai_manager.get_current_provider().title()}"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def handle_switch_llm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /switchllm command - Switch between AI providers (admin only)
    Usage: /switchllm <provider>
    """
    user = update.effective_user
    is_owner = user.id == BOT_OWNER_ID or await is_admin(update, context)
    
    if not is_owner:
        await update.message.reply_text("❌ This command is admin-only.")
        return
    
    if not context.args:
        available = ai_manager.get_available_providers()
        current = ai_manager.get_current_provider()
        
        message = (
            "🔄 *LLM Provider Switch*\n\n"
            f"Current: {current.title()}\n"
            f"Available: {', '.join([p.title() for p in available])}\n\n"
            f"Usage: /switchllm <provider>\n"
            f"Example: /switchllm deepseek"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    # Get target provider
    target_provider = context.args[0].lower()
    
    # Try to switch
    if ai_manager.switch_provider(target_provider):
        await update.message.reply_text(
            f"✅ Switched to {target_provider.title()}!",
            parse_mode='Markdown'
        )
    else:
        available = ai_manager.get_available_providers()
        await update.message.reply_text(
            f"❌ Cannot switch to '{target_provider}'.\n"
            f"Available providers: {', '.join(available)}",
            parse_mode='Markdown'
        )

async def handle_llm_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /llmstatus command - Show current LLM configuration
    """
    current = ai_manager.get_current_provider()
    available = ai_manager.get_available_providers()

    provider_emojis = {
        'gemini': '🔮',
        'deepseek': '🧠',
        'openrouter': '🌐',
        'qwen': '🐼'
    }

    message = "🤖 *AI Configuration*\n\n"
    message += f"Current: {provider_emojis.get(current, '🤖')} {current.title()}\n\n"
    message += "*Available Providers:*\n"

    for provider in available:
        emoji = provider_emojis.get(provider, '🤖')
        status = "✅" if provider == current else "⚪"
        message += f"{status} {emoji} {provider.title()}\n"

    await update.message.reply_text(message, parse_mode='Markdown')

async def handle_know_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /knowme command - Ask Miki if she knows you.
    Demonstrates the memory/identity feature.
    """
    user = update.effective_user
    username = user.username or ""
    first_name = user.first_name or ""

    response = ai_manager.handle_do_you_know_me(user.id, username, first_name)
    await update.message.reply_text(response)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is admin in the chat"""
    try:
        member = await context.bot.get_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id
        )
        return member.status in ['creator', 'administrator']
    except:
        return False
