"""
Utility functions
Helper functions used across the bot
"""
from config import GROUP_CHAT_ID as INITIAL_GROUP_CHAT_ID

# Global variable to store detected group chat ID
_group_chat_id = INITIAL_GROUP_CHAT_ID

def save_group_id(chat_id):
    """
    Update group chat ID if detected from messages
    Args:
        chat_id (int): The chat ID to save
    """
    global _group_chat_id
    if _group_chat_id is None:  # Only update if not set in .env
        _group_chat_id = chat_id
        print(f"✅ Detected Group ID: {chat_id}")

def get_group_chat_id():
    """
    Get the current group chat ID
    
    Returns:
        int: Group chat ID or None
    """
    return _group_chat_id