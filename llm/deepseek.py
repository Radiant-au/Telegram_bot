"""
DeepSeek LLM provider implementation
"""
from openai import OpenAI
from .base import BaseLLM
from .constants import SYSTEM_PROMPT

class DeepSeekLLM(BaseLLM):
    """DeepSeek AI provider"""
    def __init__(self, api_key):
        super().__init__(api_key)
        if not api_key:
            print("⚠️  DeepSeek disabled (no API key)")
            return
        
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            self.enabled = True
            print("✅ DeepSeek AI initialized")
        except Exception as e:
            print(f"❌ Failed to initialize DeepSeek: {e}")
    
    async def generate(self, prompt):
        """Generate response using DeepSeek"""
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300,
            stream=False
        )
        return response.choices[0].message.content.strip()
