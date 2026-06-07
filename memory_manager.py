"""
Memory Manager for Miki Telegram Bot
Handles user profile lookup, creation, updates, and context building
for token-efficient personalized conversations.

Sheet column mapping (enrollment form + memory columns):
  0: Timestamp
  1: Name
  2: Phone
  3: Major
  4: Year
  5: Telegram username
  6: What fields are u interested in?  → mapped as "interests"
  7: Telegram ID  (NEW — auto-linked)
  8: Last Summary  (NEW)
  9: Last Updated  (NEW)
"""
import asyncio
import logging
from datetime import datetime
from sheets import sheets_manager

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages long-term user memory via Google Sheets.

    Profile lookup uses 3-tier matching:
      1. Telegram ID (stable, auto-linked after first match)
      2. Telegram username (form username == actual username)
      3. Name (+ optional Major filter) — fallback when username is wrong
    """

    # Column indices (0-based) matching the enrollment form sheet
    COL_TIMESTAMP = 0
    COL_NAME = 1
    COL_PHONE = 2
    COL_MAJOR = 3
    COL_YEAR = 4
    COL_TELEGRAM_USERNAME = 5
    COL_INTERESTS = 6       # "What fields are u interested in?"
    COL_TELEGRAM_ID = 7     # NEW
    COL_LAST_SUMMARY = 8    # NEW
    COL_LAST_UPDATED = 9    # NEW

    def __init__(self):
        self._chat_history: dict[int, list[dict]] = {}
        self.MAX_HISTORY = 5  # sliding window size

    # ─── Profile Lookup (3-tier) ────────────────────────────────────

    def get_profile(self, user_id: int, username: str = "", first_name: str = "") -> dict | None:
        """
        Look up a user profile using 3-tier matching:
          1. Telegram ID (most stable)
          2. Telegram username
          3. Name (from Telegram first_name)

        If matched by name for the first time, auto-link the Telegram ID.

        Returns:
            dict with keys {name, interests, major, year, phone, last_summary,
                            status, username, _record, _row_idx}
            or None if not found.
        """
        if not sheets_manager.enabled:
            return None

        record = None
        match_method = None

        # Tier 1: Match by Telegram ID
        record = sheets_manager.find_user_by_id(user_id)
        if record:
            match_method = "id"

        # Tier 2: Match by Telegram username
        if not record and username:
            record = sheets_manager.find_user_data(username)
            if record:
                match_method = "username"

        # Tier 3: Match by Name (first_name from Telegram)
        if not record and first_name:
            record = sheets_manager.find_user_by_name(first_name)
            if record:
                match_method = "name"

        if not record:
            return None

        # Build profile dict
        name = str(record.get("Name", "")).strip()
        interests = str(record.get("What fields are u interested in?", "")).strip()
        major = str(record.get("Major", "")).strip()
        year = str(record.get("Year", "")).strip()
        phone = str(record.get("Phone", "")).strip()
        last_summary = str(record.get("Last Summary", "")).strip()
        sheet_username = str(record.get("Telegram username", "")).strip()

        profile = {
            "name": name if name else None,
            "interests": interests if interests else None,
            "major": major if major else None,
            "year": year if year else None,
            "phone": phone if phone else None,
            "last_summary": last_summary if last_summary else None,
            "status": "known",
            "username": sheet_username,
            "_record": record,
            "_row_idx": sheets_manager.find_row_index_by_record(record),
        }

        # Auto-link: if matched by username or name but no Telegram ID yet
        sheet_id = str(record.get("Telegram ID", "")).strip()
        if not sheet_id and profile["_row_idx"] is not None:
            if sheets_manager.link_telegram_id(profile["_row_idx"], user_id):
                logger.info("Auto-linked Telegram ID %s for user %s (%s)", user_id, name, match_method)

        return profile

    def create_profile(
        self, user_id: int, username: str, name: str = "", interests: str = "",
        major: str = "", year: str = "", phone: str = ""
    ) -> bool:
        """
        Create a new user profile row in the sheet.

        Returns True on success.
        """
        if not sheets_manager.enabled:
            return False

        try:
            now = datetime.now().isoformat()
            row = [now, name, phone, major, year, username.lstrip("@"), interests, str(user_id), "", now]
            sheets_manager.sheet.append_row(row, value_input_option="USER_ENTERED")
            logger.info("Created profile for user %s (%s)", user_id, name)
            return True
        except Exception as e:
            logger.error("Failed to create profile for user %s: %s", user_id, e)
            return False

    def update_profile(self, user_id: int, new_facts: dict) -> bool:
        """
        Update specific fields for an existing user profile.

        Args:
            user_id: Telegram user ID
            new_facts: dict with keys from {name, interests, last_summary}

        Returns True on success.
        """
        if not sheets_manager.enabled:
            return False

        try:
            row_idx = sheets_manager.find_row_index_by_id(user_id)
            if row_idx is None:
                logger.warning("Cannot update: user %s not found in sheet", user_id)
                return False

            now = datetime.now().isoformat()
            updates = []

            col_map = {
                "name": self.COL_NAME + 1,
                "interests": self.COL_INTERESTS + 1,
                "last_summary": self.COL_LAST_SUMMARY + 1,
            }

            for key, value in new_facts.items():
                col_idx = col_map.get(key)
                if col_idx:
                    col_letter = self._col_index_to_letter(col_idx)
                    if col_letter:
                        cell = f"{col_letter}{row_idx}"
                        updates.append((cell, str(value)))

            if updates:
                updated_col = self._col_index_to_letter(self.COL_LAST_UPDATED + 1)
                updates.append((f"{updated_col}{row_idx}", now))
                sheets_manager.sheet.update_cells(
                    [
                        sheets_manager.sheet.acell(cell, value=val)
                        for cell, val in updates
                    ]
                )
                logger.info("Updated profile for user %s: %s", user_id, list(new_facts.keys()))
                return True

            return False
        except Exception as e:
            logger.error("Failed to update profile for user %s: %s", user_id, e)
            return False

    def _col_index_to_letter(self, index: int) -> str:
        """Convert 1-based column index to Excel letter (1->A, 2->B, etc.)."""
        result = ""
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result
        return result

    # ─── Chat History (sliding window) ──────────────────────────────

    def add_message(self, user_id: int, role: str, content: str):
        """Add a message to the user's sliding-window chat history."""
        if user_id not in self._chat_history:
            self._chat_history[user_id] = []

        self._chat_history[user_id].append({"role": role, "content": content})

        # Trim to MAX_HISTORY turns (each turn = user + assistant)
        max_entries = self.MAX_HISTORY * 2
        if len(self._chat_history[user_id]) > max_entries:
            self._chat_history[user_id] = self._chat_history[user_id][-max_entries:]

    def get_history(self, user_id: int) -> list[dict]:
        """Get the current chat history for a user."""
        return self._chat_history.get(user_id, [])

    def clear_history(self, user_id: int):
        """Clear chat history for a user."""
        self._chat_history.pop(user_id, None)

    # ─── Context Building ───────────────────────────────────────────

    def build_context(self, profile: dict | None, chat_history: list[dict]) -> str:
        """
        Build the optimized context string for the LLM prompt.

        Combines:
          - User profile (name, interests, major, year, last_summary) if available
          - Recent chat history (sliding window)
        """
        context_parts = []

        # Profile section
        if profile and profile.get("status") == "known":
            parts = []
            if profile.get("name"):
                parts.append(f"Name: {profile['name']}")
            if profile.get("major"):
                parts.append(f"Major: {profile['major']}")
            if profile.get("year"):
                parts.append(f"Year: {profile['year']}")
            if profile.get("interests"):
                parts.append(f"Interested in: {profile['interests']}")
            if profile.get("last_summary"):
                parts.append(f"Past conversation summary: {profile['last_summary']}")

            if parts:
                context_parts.append("USER PROFILE:\n" + "\n".join(parts))
        else:
            context_parts.append(
                "USER PROFILE: This is a new user. You don't know their name or interests yet. "
                "Be friendly and invite them to share about themselves."
            )

        # Chat history section
        if chat_history:
            history_lines = []
            for msg in chat_history:
                role_label = "User" if msg["role"] == "user" else "Miki"
                history_lines.append(f"{role_label}: {msg['content']}")
            context_parts.append("RECENT CONVERSATION:\n" + "\n".join(history_lines))
        else:
            context_parts.append("RECENT CONVERSATION: No prior messages in this session.")

        return "\n\n---\n\n".join(context_parts)

    # ─── Fact Extraction ────────────────────────────────────────────

    def extract_new_facts(self, user_message: str) -> dict:
        """
        Heuristic extraction of potential permanent facts from user messages.

        Looks for patterns like:
          - "my name is X" / "call me X" / "I'm X"
          - "I love/like/enjoy X" / "I'm into X" / "I'm interested in X"
          - "I study X" / "I'm a X major"

        Returns dict with keys from {name, interests} if found.
        """
        facts = {}
        msg_lower = user_message.lower().strip()

        # Name patterns
        name_patterns = [
            "my name is ", "call me ", "i'm ", "i am ",
            "name's ", "people call me ", "just call me ",
        ]
        for pattern in name_patterns:
            idx = msg_lower.find(pattern)
            if idx >= 0:
                import re
                candidate = user_message[idx + len(pattern):].strip()
                match = re.match(r"([A-Za-z][A-Za-z' -]{0,25})", candidate)
                if match:
                    name = match.group(1).strip().rstrip(".")
                    if len(name) > 1 and not name.lower().startswith(("i ", "my ", "the ")):
                        facts["name"] = name
                        break

        # Interest patterns
        interest_patterns = [
            ("i love ", "love"),
            ("i like ", "like"),
            ("i enjoy ", "enjoy"),
            ("i'm into ", "into"),
            ("i am into ", "into"),
            ("i'm interested in ", "interested in"),
            ("i am interested in ", "interested in"),
            ("i study ", "study"),
            ("i'm a ", "major/hobby"),
            ("my hobby is ", "hobby"),
            ("my hobbies are ", "hobbies"),
            ("i play ", "play"),
            ("i listen to ", "listen to"),
            ("i'm a fan of ", "fan of"),
            ("i am a fan of ", "fan of"),
        ]

        interests_found = []
        for pattern, _label in interest_patterns:
            idx = msg_lower.find(pattern)
            if idx >= 0:
                import re
                candidate = user_message[idx + len(pattern):].strip()
                match = re.match(r"([^.!?,]{2,60})", candidate)
                if match:
                    interest = match.group(1).strip()
                    if interest and len(interest) > 2:
                        interests_found.append(interest)

        if interests_found:
            facts["interests"] = ", ".join(interests_found)

        return facts

    # ─── Async Sheet Update ─────────────────────────────────────────

    async def async_update_profile(self, user_id: int, facts: dict):
        """Update profile asynchronously to avoid blocking the polling loop."""
        if not facts:
            return

        loop = asyncio.get_event_loop()

        def _update():
            return self.update_profile(user_id, facts)

        try:
            success = await loop.run_in_executor(None, _update)
            if success:
                logger.info("Async profile update succeeded for user %s", user_id)
            else:
                logger.warning("Async profile update returned False for user %s", user_id)
        except Exception as e:
            logger.error("Async profile update failed for user %s: %s", user_id, e)


# Create global instance
memory_manager = MemoryManager()
