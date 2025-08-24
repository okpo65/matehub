from typing import List, Dict, Any
import logging
import anthropic
from app.config import settings
from app.llm.clients.base_client import BaseLLMClient, ConfigurationError


logger = logging.getLogger(__name__)


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude LLM client implementation"""
    
    def __init__(self):
        super().__init__()
        
        self.api_key = settings.anthropic_api_key
        if not self.api_key:
            raise ConfigurationError("Anthropic API key is required. Set ANTHROPIC_API_KEY in environment or config.")
        
        # Configure the SDK
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def _convert_messages_to_claude_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style messages to Gemini format"""
        claude_messages = []
        system_instruction = ""
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                claude_messages.append({
                    "role": "user",
                    "content": content
                })
            elif role == "assistant" or role == "model":
                claude_messages.append({
                    "role": "model",
                    "content": content
                })
        
        return claude_messages, system_instruction
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
    ) -> str:
        """Generate a response using Gemini API"""

        # Convert messages to Gemini format
        claude_messages, system_instruction = self._convert_messages_to_claude_format(messages)
        
        # Try with system_instruction first, fallback if not supported
        response = self.client.messages.create(
            model=model,
            system=system_instruction,
            messages=claude_messages,
        )
        return response.content[0].text

