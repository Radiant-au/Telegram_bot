"""
Memory Manager for Miki Telegram Bot
Handles user profile lookup via Google Sheets.
"""
import logging
from sheets import sheets_manager

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages user profile lookup from Google Sheets.
    Profile lookup uses 3-tier matching:
      1. Telegram ID (stable)
      2. Telegram username
      3. Name
    """
    def __init__(self):
        pass

    def get_profile(self, user_id: int, username: str = "", first_name: str = "") -> dict | None:
        """
        Look up a user profile using 3-tier matching:
          1. Telegram ID (most stable)
          2. Telegram username
          3. Name (from Telegram first_name)

        Returns:
            dict with keys {name, interests, major, year, phone, status, username, _record}
            or None if not found.
        """
        if not sheets_manager.enabled:
            return None

        record = None

        # Tier 1: Match by Telegram ID
        record = sheets_manager.find_user_by_id(user_id)

        # Tier 2: Match by Telegram username
        if not record and username:
            record = sheets_manager.find_user_data(username)

        # Tier 3: Match by Name (first_name from Telegram)
        if not record and first_name:
            record = sheets_manager.find_user_by_name(first_name)

        if not record:
            return None

        # Build profile dict
        name = str(record.get("Name", "")).strip()
        interests = str(record.get("What fields are u interested in?", "")).strip()
        major = str(record.get("Major", "")).strip()
        year = str(record.get("Year", "")).strip()
        phone = str(record.get("Phone", "")).strip()
        sheet_username = str(record.get("Telegram username", "")).strip()

        profile = {
            "name": name if name else None,
            "interests": interests if interests else None,
            "major": major if major else None,
            "year": year if year else None,
            "phone": phone if phone else None,
            "status": "known",
            "username": sheet_username,
            "_record": record,
        }

        return profile

# Create global instance
memory_manager = MemoryManager()
