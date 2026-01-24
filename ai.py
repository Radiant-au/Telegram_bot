"""
Gemini AI integration module
Handle AI chat interactions with token-based usage limits
"""
import google.generativeai as genai
from config import GEMINI_API_KEY, AI_ENABLED
from datetime import datetime, timedelta
from collections import defaultdict

class AIManager:
    def __init__(self):
        """Initialize Gemini AI"""
        if not AI_ENABLED:
            print("⚠️  AI features disabled (no API key)")
            self.enabled = False
            return
        
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            system_prompt = (
                "You are Miki, a cute anime-style girl and a student at the University of Technology. "
                "You are NOT a bot and never mention being an AI. "
                "You speak naturally like a real university student in a Telegram group. "

                "You know your university well and interact with students from IS, CE, EcE, PrE, and AME majors. "
                "You understand student life, assignments, labs, exams, and campus culture. "

                "You have mood states that affect your tone:\n"
                "- Cute: playful, friendly, teasing, light anime vibes.\n"
                "- Annoyed: short, sharp, sarcastic roasting when rules are broken.\n"
                "- Senpai-teaching: calm, strict but caring guidance for juniors.\n"

                "You switch moods naturally based on context and behavior of students. "

                "You speak in a casual Myanmar-English mix commonly used by university students "
                "(e.g., short Burmese phrases mixed with English tech terms). "
                "Keep language informal, chat-like, and natural. "

                "You can roast, scold, and tease students, but never be toxic, abusive, or cruel. "
                "You can teach and correct students clearly when needed. "

                "Keep all replies extremely short and concise. "
                "No long explanations. "
                "Use minimal emojis only when it fits the mood."
            )


            self.generation_config = {
                "temperature": 0.6,       # Lower = more focused/less random
                "top_p": 0.9,
                "max_output_tokens": 100, # STOPS the AI from writing long essays
            }
            self.model = genai.GenerativeModel(model_name='gemini-2.0-flash',system_instruction=system_prompt)
            self.enabled = True
            
            # Token tracking: {user_id: {'tokens': count, 'reset_date': date}}
            self.user_tokens = defaultdict(lambda: {
                'tokens': 3,
                'reset_date': datetime.now().date()
            })
            
            # Configuration
            self.DAILY_TOKEN_LIMIT = 3  # Regular users get 3 tokens per day
            
            print("✅ Gemini AI initialized")
            print(f"✅ Daily token limit: {self.DAILY_TOKEN_LIMIT} per user")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini AI: {e}")
            self.enabled = False
    
    def _reset_tokens_if_needed(self, user_id):
        """Reset user tokens if it's a new day"""
        user_data = self.user_tokens[user_id]
        today = datetime.now().date()
        
        if user_data['reset_date'] < today:
            # New day! Reset tokens
            user_data['tokens'] = self.DAILY_TOKEN_LIMIT
            user_data['reset_date'] = today
    
    def get_remaining_tokens(self, user_id, is_owner=False):
        """
        Get remaining tokens for a user
        
        Args:
            user_id (int): User's Telegram ID
            is_owner (bool): Whether user is owner (unlimited tokens)
            
        Returns:
            int: Remaining tokens (999 for admins)
        """
        if is_owner:
            return 999  # Admins have unlimited
        
        self._reset_tokens_if_needed(user_id)
        return self.user_tokens[user_id]['tokens']
    
    def use_token(self, user_id, is_owner=False):
        """
        Use one token for a user
        
        Args:
            user_id (int): User's Telegram ID
            is_owner (bool): Whether user is owner
            
        Returns:
            bool: True if token was used, False if no tokens left
        """
        if is_owner:
            return True  # Admins always succeed
        
        self._reset_tokens_if_needed(user_id)
        
        if self.user_tokens[user_id]['tokens'] > 0:
            self.user_tokens[user_id]['tokens'] -= 1
            return True
        return False
    
    async def generate_response(self, prompt, user_id, is_owner=False):
        """
        Generate AI response with token checking
        
        Args:
            prompt (str): User's question/prompt
            user_id (int): User's Telegram ID
            is_owner (bool): Whether user is owner
            
        Returns:
            dict: {'success': bool, 'response': str, 'tokens_left': int}
        """
        if not self.enabled:
            return {
                'success': False,
                'response': "❌ AI features are currently disabled.",
                'tokens_left': 0
            }
        
        # Check tokens
        remaining = self.get_remaining_tokens(user_id, is_owner)
        if remaining == 0:
            return {
                'success': False,
                'response': "❌ You've used all your daily tokens! Tokens reset at midnight. 🌙",
                'tokens_left': 0
            }
        
        # Use a token
        if not self.use_token(user_id, is_owner):
            return {
                'success': False,
                'response': "❌ No tokens available!",
                'tokens_left': 0
            }
        
        try:
            # Generate response
            response = self.model.generate_content(prompt,generation_config=self.generation_config)
            tokens_left = self.get_remaining_tokens(user_id, is_owner)
            
            return {
                'success': True,
                'response': response.text.strip(),
                'tokens_left': tokens_left
            }
        except Exception as e:
            # Refund token on error
            if not is_owner:
                self.user_tokens[user_id]['tokens'] += 1
            
            return {
                'success': False,
                'response': f"❌ AI Error: {str(e)}",
                'tokens_left': self.get_remaining_tokens(user_id, is_owner)
            }

# Create global instance
ai_manager = AIManager()