"""
Qwen LLM provider implementation
"""
import logging
from openai import OpenAI
from .base import BaseLLM
from .constants import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class QwenLLM(BaseLLM):
    """Qwen AI provider (via DashScope compatible mode)"""
    def __init__(self, api_key):
        super().__init__(api_key)
        if not api_key:
            logger.warning("Qwen disabled (no API key)")
            return
        
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://ws-u6kc5v05dd01tpkn.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
            )
            self.enabled = True
            logger.info("Qwen AI initialized")
        except Exception as e:
            logger.error("Failed to initialize Qwen: %s", e, exc_info=True)
            
    async def generate(self, prompt):
        """Generate response using Qwen"""
        response = self.client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300,
            stream=False
        )
        return response.choices[0].message.content.strip()
