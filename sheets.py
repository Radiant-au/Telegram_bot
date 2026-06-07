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

    def find_user_by_id(self, user_id):
        """
        Search for user in Google Sheet by Telegram user ID.

        Args:
            user_id (int): Telegram numeric user ID

        Returns:
            dict: User data if found, None otherwise
        """
        if not self.sheet:
            return None

        try:
            all_records = self.sheet.get_all_records()

            for record in all_records:
                sheet_id = str(record.get('Telegram ID', '')).strip()
                if sheet_id == str(user_id):
                    return record
        except Exception as e:
            print(f"❌ Error reading user data by ID from Google Sheet: {e}")
        return None

    def find_user_by_name(self, name, major=None):
        """
        Search for user in Google Sheet by Name (with optional Major filter).
        Used as fallback when Telegram ID and username don't match.

        Args:
            name (str): User's name from Telegram profile
            major (str, optional): User's major to narrow down matches

        Returns:
            dict: User data if found, None otherwise. If multiple matches,
                  returns None (ambiguous).
        """
        if not self.sheet:
            return None

        try:
            all_records = self.sheet.get_all_records()
            name_clean = name.strip().lower()

            matches = []
            for record in all_records:
                sheet_name = str(record.get('Name', '')).strip().lower()
                sheet_major = str(record.get('Major', '')).strip().lower()

                if sheet_name == name_clean:
                    if major is None or sheet_major == major.strip().lower():
                        matches.append(record)

            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                print(f"⚠️ Ambiguous name match for '{name}': {len(matches)} matches")
                return None
        except Exception as e:
            print(f"❌ Error reading user data by name from Google Sheet: {e}")
        return None

    def find_row_index_by_id(self, user_id):
        """
        Find the 1-based row index for a user identified by Telegram ID.

        Args:
            user_id (int): Telegram numeric user ID

        Returns:
            int: 1-based row index (including header), or None
        """
        if not self.sheet:
            return None

        try:
            all_records = self.sheet.get_all_records()
            for i, record in enumerate(all_records, start=2):
                if str(record.get('Telegram ID', '')).strip() == str(user_id):
                    return i
        except Exception:
            pass
        return None

    def find_row_index_by_record(self, record):
        """
        Find the 1-based row index for a known record by matching on Name + Phone.

        Args:
            record (dict): A record returned from find_user_data / find_user_by_name

        Returns:
            int: 1-based row index (including header), or None
        """
        if not self.sheet or not record:
            return None

        try:
            all_records = self.sheet.get_all_records()
            target_name = str(record.get('Name', '')).strip().lower()
            target_phone = str(record.get('Phone', '')).strip()

            for i, rec in enumerate(all_records, start=2):
                if (str(rec.get('Name', '')).strip().lower() == target_name
                        and str(rec.get('Phone', '')).strip() == target_phone):
                    return i
        except Exception:
            pass
        return None

    def link_telegram_id(self, row_idx, user_id):
        """
        Write a Telegram ID into the sheet for a user row (auto-linking).

        Args:
            row_idx (int): 1-based row index
            user_id (int): Telegram numeric user ID

        Returns:
            bool: True on success
        """
        if not self.sheet:
            return False

        try:
            headers = self.sheet.row_values(1)
            col_idx = None
            for i, header in enumerate(headers, start=1):
                if header.strip().lower() == 'telegram id':
                    col_idx = i
                    break

            if col_idx is None:
                print("⚠️ 'Telegram ID' column not found in sheet — cannot auto-link")
                return False

            self.sheet.update_cell(row_idx, col_idx, str(user_id))
            return True
        except Exception as e:
            print(f"❌ Error linking Telegram ID for row {row_idx}: {e}")
            return False

    def append_row(self, row, value_input_option="USER_ENTERED"):
        """
        Append a row to the sheet.

        Args:
            row (list): List of cell values
            value_input_option (str): How to interpret values

        Returns:
            dict: Response from the API or None on failure
        """
        if not self.sheet:
            return None

        try:
            return self.sheet.append_row(row, value_input_option=value_input_option)
        except Exception as e:
            print(f"❌ Error appending row to Google Sheet: {e}")
            return None

    def update_cell_by_id(self, user_id, column_name, value):
        """
        Update a specific cell for a user identified by Telegram ID.

        Args:
            user_id (int): Telegram numeric user ID
            column_name (str): Header name of the column to update
            value: New value for the cell

        Returns:
            bool: True on success, False on failure
        """
        if not self.sheet:
            return False

        try:
            all_records = self.sheet.get_all_records()
            row_idx = None

            # Find the row (1-indexed, header is row 1)
            for i, record in enumerate(all_records, start=2):
                if str(record.get('Telegram ID', '')).strip() == str(user_id):
                    row_idx = i
                    break

            if row_idx is None:
                print(f"⚠️ User {user_id} not found in sheet for update")
                return False

            # Find the column index
            headers = self.sheet.row_values(1)
            col_idx = None
            for i, header in enumerate(headers, start=1):
                if header.strip().lower() == column_name.lower():
                    col_idx = i
                    break

            if col_idx is None:
                print(f"⚠️ Column '{column_name}' not found in sheet")
                return False

            # Update the cell
            self.sheet.update_cell(row_idx, col_idx, value)
            return True
        except Exception as e:
            print(f"❌ Error updating cell for user {user_id}: {e}")
            return False

    def get_headers(self):
        """
        Get the header row of the sheet.

        Returns:
            list: List of header names, or empty list on failure
        """
        if not self.sheet:
            return []

        try:
            return self.sheet.row_values(1)
        except Exception as e:
            print(f"❌ Error reading sheet headers: {e}")
            return []
    
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