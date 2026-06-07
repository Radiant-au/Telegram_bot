"""
Gemini LLM provider implementation
"""
import logging
import google.generativeai as genai
from .base import BaseLLM
from .constants import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class GeminiLLM(BaseLLM):
    """Gemini AI provider"""
    def __init__(self, api_key):
        super().__init__(api_key)
        if not api_key:
            logger.warning("Gemini disabled (no API key)")
            return
        
        try:
            genai.configure(api_key=api_key)

            self.generation_config = {
                "temperature": 0.6,
                "top_p": 0.9,
                "max_output_tokens": 100,
            }
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=SYSTEM_PROMPT
            )
            self.enabled = True
            logger.info("Gemini AI initialized")
        except Exception as e:
            logger.error("Failed to initialize Gemini: %s", e, exc_info=True)
    
    async def generate(self, prompt, system_prompt=None):
        """Generate response using Gemini"""
        model = self.model
        if system_prompt and system_prompt != SYSTEM_PROMPT:
            # Create a temporary model with custom system instruction
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=system_prompt
            )
        response = model.generate_content(
            prompt,
            generation_config=self.generation_config
        )
        return response.text.strip()
