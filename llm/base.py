"""
Base LLM class definition
"""

class BaseLLM:
    """Base class for LLM providers"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.enabled = False

    async def generate(self, prompt, system_prompt=None):
        """Generate response - to be implemented by subclasses"""
        raise NotImplementedError
