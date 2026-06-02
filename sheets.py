"""
Google Sheets integration module
Handle all Google Sheets operations
"""
import gspread
from config import GOOGLE_CREDENTIALS, SHEET_NAME

class SheetsManager:
    def __init__(self):
        """Initialize Google Sheets connection"""
        self.sheet = None
        self.enabled = False
        
        if not GOOGLE_CREDENTIALS:
            print("⚠️  GOOGLE_CREDENTIALS not configured. Sheets features will be disabled.")
            return
            
        try:
            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            client = gspread.service_account_from_dict(GOOGLE_CREDENTIALS, scopes=scopes)
            self.sheet = client.open(SHEET_NAME).sheet1
            self.enabled = True
            print(f"✅ Connected to Google Sheet: {SHEET_NAME}")
        except Exception as e:
            print(f"❌ Failed to connect to Google Sheet: {e}")
    
    def find_user_data(self, username):
        """
        Search for user in Google Sheet by Telegram username
        
        Args:
            username (str): Telegram username (with or without @)
            
        Returns:
            dict: User data if found, None otherwise
        """
        if not self.sheet:
            return None
            
        try:
            all_records = self.sheet.get_all_records()
            username_clean = username.lstrip('@').lower()
            
            for record in all_records:
                sheet_username = str(record.get('Telegram username', '')).lstrip('@').lower()
                if sheet_username == username_clean:
                    return record
        except Exception as e:
            print(f"❌ Error reading user data from Google Sheet: {e}")
        return None
    
    def get_all_usernames(self):
        """
        Get all Telegram usernames from the sheet
        
        Returns:
            list: List of usernames (without @)
        """
        if not self.sheet:
            return []
            
        try:
            all_records = self.sheet.get_all_records()
            usernames = []
            
            for record in all_records:
                username = record.get('Telegram username', '').lstrip('@')
                if username:
                    usernames.append(username)
            return usernames
        except Exception as e:
            print(f"❌ Error reading usernames from Google Sheet: {e}")
        return []
    
    def format_interests(self, interests_str):
        """
        Format the interests field nicely
        
        Args:
            interests_str (str): Comma-separated interests
            
        Returns:
            str: Formatted interests string
        """
        if not interests_str:
            return "Not specified"
        interests = [i.strip() for i in str(interests_str).split(',')]
        return '\n   • '.join(interests)

# Create global instance
sheets_manager = SheetsManager()