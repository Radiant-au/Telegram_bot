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