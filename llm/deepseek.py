"""
DeepSeek LLM provider implementation
"""
import logging
from openai import OpenAI
from .base import BaseLLM
from .constants import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class DeepSeekLLM(BaseLLM):
    """DeepSeek AI provider"""
    def __init__(self, api_key):
        super().__init__(api_key)
        if not api_key:
            logger.warning("DeepSeek disabled (no API key)")
            return
        
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            self.enabled = True
            logger.info("DeepSeek AI initialized")
        except Exception as e:
            logger.error("Failed to initialize DeepSeek: %s", e, exc_info=True)
    
    async def generate(self, prompt, system_prompt=None):
        """Generate response using DeepSeek"""
        system = system_prompt if system_prompt else SYSTEM_PROMPT
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300,
            stream=False
        )
        return response.choices[0].message.content.strip()
