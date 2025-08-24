from typing import Dict, List
import logging
from .client_factory import LLMClientFactory

logger = logging.getLogger(__name__)


async def generate_ai_response(
    messages: List[Dict[str, str]],
    model: str
) -> str:
    try:
        client = LLMClientFactory.create_client(model)
        logger.info(f"Created client for model: {model} with provider: {client.get_provider_name()}")
        
        # Generate response
        response = await client.generate_response(
            messages=messages,
            model=model,
        )
        
        if not response or not response.strip():
            raise RuntimeError("Generated response is empty")
            
        return response.strip()
        
    except Exception as e:
        logger.error(f"Failed to generate AI response: {str(e)}")
        raise RuntimeError(f"AI response generation failed: {str(e)}")
