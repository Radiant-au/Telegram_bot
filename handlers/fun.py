"""
Fun interaction handlers
Handle greetings, reactions, and fun features
"""
from telegram import Update
from telegram.ext import ContextTypes
import random
import re
from utils import save_group_id
from handlers.members import mention_all

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle messages in the group for fun interactions
    Greetings, @all mentions, blame game, etc.
    """
    if not update.message or not update.message.text:
        return
    
    # Store and save group chat ID permanently
    if update.effective_chat.type in ['group', 'supergroup']:
        save_group_id(update.effective_chat.id)
    
    text = update.message.text.lower()
    bot_username = context.bot.username.lower()
    
    # Check for @all mention (admin only)
    if '@all' in text:
        await mention_all(update, context)
        return
    
    # Greeting when mentioned
    if f'@{bot_username}' in text or ('hello' in text and bot_username in text):
        greetings = [
            f"Hellooo {update.effective_user.first_name}! 💖✨",
            f"Heyy there {update.effective_user.first_name}! 🌸😊",
            f"Hiiii! How can I help you today? 🥰",
            f"Hello hello! {update.effective_user.first_name} 💕",
            f"Aww hey! So nice to hear from you! 🌟💫",
        ]
        await update.message.reply_text(random.choice(greetings))
        return
    
    # Detect "blame @username" pattern
    blame_pattern = r'blame\s+@(\w+)'
    match = re.search(blame_pattern, text)
    
    if match:
        username = match.group(1)
        responses = [
            f"တောသား @{username} 😤",
            f"ဟုတ်ကဲ့ တောသား @{username} 🙄",
            f"@{username} တောသား! 😾",
        ]
        await update.message.reply_text(random.choice(responses))
        return