"""
OpenRouter LLM provider implementation
"""
import logging
from openai import OpenAI
from .base import BaseLLM
from .constants import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class OpenRouterLLM(BaseLLM):
    """OpenRouter AI provider"""
    def __init__(self, api_key):
        super().__init__(api_key)
        if not api_key:
            logger.warning("OpenRouter disabled (no API key)")
            return
        
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            self.enabled = True
            logger.info("OpenRouter AI initialized")
        except Exception as e:
            logger.error("Failed to initialize OpenRouter: %s", e, exc_info=True)
    
    async def generate(self, prompt, system_prompt=None):
        """Generate response using OpenRouter"""
        system = system_prompt if system_prompt else SYSTEM_PROMPT
        response = self.client.chat.completions.create(
            model="google/gemma-4-31b-it",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300,
            stream=False
        )
        return response.choices[0].message.content.strip()
