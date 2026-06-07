"""
Member-related handlers
Handle new member joins and member management
"""
from telegram import Update
from telegram.ext import ContextTypes
from config import MEMBER_TOPIC_ID
from sheets import sheets_manager
from utils import save_group_id

async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle new members joining the group
    Send welcome message with user info from Google Sheets
    """
    save_group_id(update.effective_chat.id)
    
    result = update.chat_member
    
    if result.new_chat_member.status in ["member", "administrator"]:
        user = result.new_chat_member.user
        username = user.username
        
        if username:
            user_data = sheets_manager.find_user_data(username)
            
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
   • {sheets_manager.format_interests(interests)}

━━━━━━━━━━━━━━━━━━━━━━
Welcome to the community! 🚀
"""
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    message_thread_id=MEMBER_TOPIC_ID,
                    text=message
                )

async def mention_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Mention all members - send clean message + separate mentions
    Only admins can use this
    """
    user = update.effective_user
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
    
    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text("⚠️ Only admins can use @all")
        return
    
    try:
        usernames = sheets_manager.get_all_usernames()
        mentions = [f"@{username}" for username in usernames]
        
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

async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /getinfo command - Admin only
    Usage: /getinfo @username
    Shows detailed user information from Google Sheets
    """
    user_id = update.effective_user.id
    
    # Check if user is admin
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text("⚠️ Only admins can use this command!")
        return
    
    # Check if username provided
    if not context.args:
        await update.message.reply_text(
            "💡 **Usage:**\n"
            "`/getinfo @username`\n\n"
            "**Example:**\n"
            "`/getinfo @john_doe`"
        )
        return
    
    # Get username (remove @ if present)
    username = context.args[0].lstrip('@')
    
    # Search for user in sheets
    user_data = sheets_manager.find_user_data(username)
    
    if not user_data:
        await update.message.reply_text(
            f"❌ User @{username} not found in database!\n\n"
            "Make sure:\n"
            "• Username is spelled correctly\n"
            "• User is registered in the Google Sheet"
        )
        return
    
    # Format user information
    name = user_data.get('Name', 'N/A')
    phone = user_data.get('Phone', 'N/A')
    major = user_data.get('Major', 'N/A')
    year = user_data.get('Year', 'N/A')
    interests = user_data.get('What fields are u interested in?', 'Not specified')
    
    info_message = f"""

👤 USER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━

📱 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺: @{username}
👤 𝗡𝗮𝗺𝗲: {name}
📞 𝗣𝗵𝗼𝗻𝗲: {phone}

🎓 𝗔𝗰𝗮𝗱𝗲𝗺𝗶𝗰 𝗜𝗻𝗳𝗼:
   • Major: {major}
   • Year: {year}

💻 𝗜𝗻𝘁𝗲𝗿𝗲𝘀𝘁𝗲𝗱 𝗶𝗻:
   • {sheets_manager.format_interests(interests)}

━━━━━━━━━━━━━━━━━━━━━━
"""
    
    await update.message.reply_text(info_message)

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command
    Show Bot usage guide for all users
    """
    
    user_id = update.effective_user.id
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    is_admin = chat_member.status in ['administrator', 'creator']
    
    help_text = f"""
🤖 Bot Help

Commands:
- /miki <question> - Ask the AI anything
- /tokens - Check remaining tokens
- /llmstatus - Show current AI model status
- /help - Show this help message
- /knowme - Show your known profile information

Usage Examples:
- /miki What is machine learning?

Admin Commands:
- @all - Mention all users in the group
- /getinfo @username - Get user info from Google Sheets
- /switchllm <provider> - Switch AI provider (gemini/deepseek/openrouter/qwen)

Token System:
{"👑 You have unlimited tokens (Admin)" if is_admin else "🎟️ You get 10 tokens per day"}
🔄 Tokens reset at midnight
💡 Use tokens wisely!

Tips:
- Be specific with your questions
- You can ask about coding, tech, science, etc.
- The AI is powered by Gemini, DeepSeek, OpenRouter & Qwen

Happy chatting! 🚀
"""
    
    await update.message.reply_text(help_text)
