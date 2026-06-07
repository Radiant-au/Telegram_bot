"""
Multi-LLM integration module
Supports Gemini and DeepSeek with easy switching and token-based usage limits
Integrated with MemoryManager for personalized, token-efficient conversations.
"""
import json
import logging
from config import (
    GEMINI_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY, QWEN_API_KEY,
    AI_ENABLED, DEFAULT_LLM, DAILY_TOKEN_LIMIT
)
from datetime import datetime
from collections import defaultdict
from llm import GeminiLLM, DeepSeekLLM, OpenRouterLLM, QwenLLM
from memory_manager import memory_manager
from prompts import build_system_prompt

logger = logging.getLogger(__name__)

class AIManager:
    """Main AI manager supporting multiple LLM providers with memory awareness"""
    def __init__(self):
        """Initialize AI manager with all available LLMs"""
        # Initialize providers
        self.providers = {
            'gemini': GeminiLLM(GEMINI_API_KEY),
            'deepseek': DeepSeekLLM(DEEPSEEK_API_KEY),
            'openrouter': OpenRouterLLM(OPENROUTER_API_KEY),
            'qwen': QwenLLM(QWEN_API_KEY)
        }

        # Set default provider
        self.current_provider = DEFAULT_LLM

        # Check if any provider is enabled
        self.enabled = any(p.enabled for p in self.providers.values())

        if not self.enabled:
            logger.warning("AI features disabled (no API keys)")
            return

        # Token tracking: {user_id: {'tokens': count, 'reset_date': date}}
        self.user_tokens = defaultdict(lambda: {
            'tokens': DAILY_TOKEN_LIMIT,
            'reset_date': datetime.now().date()
        })

        # Configuration
        self.DAILY_TOKEN_LIMIT = DAILY_TOKEN_LIMIT

        logger.info("AI Manager initialized")
        logger.info("Available providers: %s", [k for k, v in self.providers.items() if v.enabled])
        logger.info("Current provider: %s", self.current_provider)
        logger.info("Daily token limit: %d per user", self.DAILY_TOKEN_LIMIT)

    def switch_provider(self, provider_name):
        """
        Switch to a different LLM provider

        Args:
            provider_name (str): Provider name ('gemini', 'deepseek', 'openrouter' or 'qwen')

        Returns:
            bool: True if switched successfully
        """
        provider_name = provider_name.lower()

        if provider_name not in self.providers:
            return False

        if not self.providers[provider_name].enabled:
            return False

        self.current_provider = provider_name
        return True

    def get_current_provider(self):
        """Get current provider name"""
        return self.current_provider

    def get_available_providers(self):
        """Get list of available providers"""
        return [k for k, v in self.providers.items() if v.enabled]

    def _reset_tokens_if_needed(self, user_id):
        """Reset user tokens if it's a new day"""
        user_data = self.user_tokens[user_id]
        today = datetime.now().date()

        if user_data['reset_date'] < today:
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
            return 999

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
            return True

        self._reset_tokens_if_needed(user_id)

        if self.user_tokens[user_id]['tokens'] > 0:
            self.user_tokens[user_id]['tokens'] -= 1
            return True
        return False

    def record_message(self, user_id: int, role: str, content: str):
        """Record a message in the user's sliding-window chat history."""
        memory_manager.add_message(user_id, role, content)

    async def generate_response(self, prompt, user_id, username="", first_name="", is_owner=False, provider=None):
        """
        Generate AI response with memory awareness and token checking.

        Fetches user profile, builds optimized context, sends to LLM,
        and records the conversation in the sliding window.

        Args:
            prompt (str): User's question/prompt
            user_id (int): User's Telegram ID
            username (str): User's Telegram username
            first_name (str): User's Telegram first name (for name-based matching)
            is_owner (bool): Whether user is owner
            provider (str, optional): Override default provider for this request

        Returns:
            dict: {'success': bool, 'response': str, 'tokens_left': int, 'provider': str}
        """
        if not self.enabled:
            return {
                'success': False,
                'response': "❌ AI features are currently disabled.",
                'tokens_left': 0,
                'provider': None
            }

        # Determine which provider to use
        use_provider = provider if provider else self.current_provider

        # Check if provider is valid and enabled
        if use_provider not in self.providers or not self.providers[use_provider].enabled:
            return {
                'success': False,
                'response': f"❌ Provider '{use_provider}' is not available.",
                'tokens_left': self.get_remaining_tokens(user_id, is_owner),
                'provider': use_provider
            }

        # Check tokens
        remaining = self.get_remaining_tokens(user_id, is_owner)
        if remaining == 0:
            return {
                'success': False,
                'response': "❌ You've used all your daily tokens! Tokens reset at midnight. 🌙",
                'tokens_left': 0,
                'provider': use_provider
            }

        # ─── Memory-aware flow ───────────────────────────────────
        # 1. Fetch profile (once, low token cost — not in prompt)
        profile = memory_manager.get_profile(user_id, username, first_name)

        # 2. Record user message in history
        memory_manager.add_message(user_id, "user", prompt)

        # 3. Build optimized context (profile + sliding window)
        chat_history = memory_manager.get_history(user_id)
        user_context = memory_manager.build_context(profile, chat_history)

        # 4. Build dynamic system prompt with memory injection
        system_prompt = build_system_prompt(profile, user_context)

        # Combine context + user prompt for the LLM
        full_prompt = f"{user_context}\n\n---\n\nUser: {prompt}"

        # Use a token
        if not self.use_token(user_id, is_owner):
            return {
                'success': False,
                'response': "❌ No tokens available!",
                'tokens_left': 0,
                'provider': use_provider
            }

        try:
            # Generate response using selected provider with dynamic system prompt
            response_text = await self.providers[use_provider].generate(
                full_prompt, system_prompt=system_prompt
            )
            tokens_left = self.get_remaining_tokens(user_id, is_owner)

            # Record assistant response in history
            memory_manager.add_message(user_id, "assistant", response_text)

            # Async: extract and save new facts from user message
            facts = memory_manager.extract_new_facts(prompt)
            if facts:
                if profile and profile.get("status") == "known":
                    # Update existing profile
                    await memory_manager.async_update_profile(user_id, facts)
                elif facts.get("name"):
                    # New user shared their name — create profile
                    memory_manager.create_profile(
                        user_id, username, name=facts.get("name", ""),
                        interests=facts.get("interests", "")
                    )

            return {
                'success': True,
                'response': response_text,
                'tokens_left': tokens_left,
                'provider': use_provider
            }
        except Exception as e:
            # Refund token on error
            if not is_owner:
                self.user_tokens[user_id]['tokens'] += 1

            return {
                'success': False,
                'response': f"❌ AI Error ({use_provider}): {str(e)}",
                'tokens_left': self.get_remaining_tokens(user_id, is_owner),
                'provider': use_provider
            }

    def handle_do_you_know_me(self, user_id: int, username: str = "", first_name: str = "") -> str:
        """
        Handle the explicit 'do you know me?' scenario.

        Returns a personalized response based on whether the user has a profile.
        """
        from prompts import build_identity_response
        profile = memory_manager.get_profile(user_id, username, first_name)
        return build_identity_response(profile)

# Create global instance
ai_manager = AIManager()
