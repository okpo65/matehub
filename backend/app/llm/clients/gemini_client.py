from typing import List, Dict, Any
import logging
from google import genai
from google.genai import types
from app.config import settings
from app.llm.clients.base_client import BaseLLMClient, ConfigurationError

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini LLM client implementation"""
    
    def __init__(self):
        super().__init__()
        
        self.api_key = settings.gemini_api_key
        if not self.api_key:
            raise ConfigurationError("Gemini API key is required. Set GEMINI_API_KEY in environment or config.")
        
        # Configure the SDK
        self.client = genai.Client(api_key=self.api_key)
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style messages to Gemini format"""
        gemini_messages = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant" or role == "model":
                gemini_messages.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })
        
        return gemini_messages
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
    ) -> str:
        """Generate a response using Gemini API"""

        # Convert messages to Gemini format
        gemini_messages = self._convert_messages_to_gemini_format(messages)
        
        # Create the model instance
        generation_config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=4000,
            top_p=0.8,
            top_k=40,
            safety_settings=[
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE
                ),
            ]
        )
        # Try with system_instruction first, fallback if not supported
        response = self.client.models.generate_content(
            model=model,
            contents=gemini_messages,
            config=generation_config,
        )
        # Extract response text
        if response.text:
            return response.text.strip()
        else:
            raise GenerationError("Empty response from Gemini API")

