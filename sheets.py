"""
Google Sheets integration module
Handle all Google Sheets operations
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from config import GOOGLE_CREDENTIALS, SHEET_NAME

class SheetsManager:
    def __init__(self):
        """Initialize Google Sheets connection"""
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        self.sheet = client.open(SHEET_NAME).sheet1
        print(f"✅ Connected to Google Sheet: {SHEET_NAME}")
    
    def find_user_data(self, username):
        """
        Search for user in Google Sheet by Telegram username
        
        Args:
            username (str): Telegram username (with or without @)
            
        Returns:
            dict: User data if found, None otherwise
        """
        all_records = self.sheet.get_all_records()
        username_clean = username.lstrip('@').lower()
        
        for record in all_records:
            sheet_username = str(record.get('Telegram username', '')).lstrip('@').lower()
            if sheet_username == username_clean:
                return record
        return None
    
    def get_all_usernames(self):
        """
        Get all Telegram usernames from the sheet
        
        Returns:
            list: List of usernames (without @)
        """
        all_records = self.sheet.get_all_records()
        usernames = []
        
        for record in all_records:
            username = record.get('Telegram username', '').lstrip('@')
            if username:
                usernames.append(username)
        
        return usernames
    
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