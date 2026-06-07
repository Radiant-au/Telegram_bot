from ai import logger
import os
import json
import asyncio

DATA_FILE = "data/quiz_data.json"

class QuizStorage:
    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self.data = {}
        self._lock = asyncio.Lock()
        
        # 1. Ensure the directory exists (creates 'data/' if missing)
        dir_name = os.path.dirname(self.filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        # 2. Load data (and create file if it doesn't exist)
        self._load()

    def _load(self):
        """Load data from JSON file synchronously, create if it doesn't exist"""
        if not os.path.exists(self.filepath):
            logger.info("Quiz data file not found. Creating empty file at %s", self.filepath)
            self.data = {}
            self._save_sync()  # Create the file immediately
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info("Loaded quiz data from %s", self.filepath)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load quiz data: %s. Starting fresh.", e)
            self.data = {}
            self._save_sync()  # Overwrite corrupted file

    def _save_sync(self):
        """Helper to save synchronously during initialization"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error("Failed to create/overwrite quiz data file: %s", e)

    def _save_data(self):
        """
        Internal method to save data to disk synchronously. 
        WARNING: MUST be called while already holding self._lock!
        """
        try:
            # Write to temp file first to prevent corruption if crash occurs during write
            temp_path = f"{self.filepath}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            
            # Atomic rename
            os.replace(temp_path, self.filepath)
            logger.debug("Saved quiz data to %s", self.filepath)
        except Exception as e:
            logger.error("Failed to save quiz data: %s", e)

    async def get_last_quiz_time(self, user_id: int) -> float:
        """Get timestamp of last quiz for user"""
        async with self._lock:
            user_key = str(user_id)
            # Just return 0 if not found. No need to modify or save data just for reading!
            return self.data.get(user_key, {}).get("last_quiz", 0)

    async def set_last_quiz_time(self, user_id: int, timestamp: float):
        """Set timestamp of last quiz for user and save"""
        async with self._lock:
            user_key = str(user_id)
            if user_key not in self.data:
                self.data[user_key] = {}
            
            self.data[user_key]["last_quiz"] = timestamp
            
            # Call the internal synchronous save method (no await needed)
            self._save_data()

# Initialize global storage instance
quiz_storage = QuizStorage()