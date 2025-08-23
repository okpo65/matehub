import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.config import settings
from app.llm.base_client import BaseLLMClient, ModelNotFoundError, GenerationError
import logging

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """Ollama LLM client implementation"""
    
    def __init__(self):
        super().__init__()
        self.base_url = settings.ollama_base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def cleanup(self):
        """Clean up HTTP client"""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose()
    
    async def generate_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
    ) -> str:
        """Generate a response using Ollama chat API"""
        try:
            # Prepare the request payload
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                }
            }
            
            payload["options"]["num_predict"] = 4000
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return data["message"]["content"]
            
        except ModelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error generating Ollama response: {e}")
            raise GenerationError(f"Ollama generation failed: {str(e)}")
