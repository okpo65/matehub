from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self):
        """Initialize the client with configuration"""
        pass
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
    ) -> str:
        """Generate a response using the LLM"""
        pass
    
    async def cleanup(self):
        """Clean up resources (override if needed)"""
        pass
    
    def get_provider_name(self) -> str:
        """Get the name of the LLM provider"""
        return self.__class__.__name__.replace("Client", "").lower()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the LLM service"""
        try:
            models = await self.list_models()
            return {
                "status": "healthy",
                "provider": self.get_provider_name(),
                "models_available": len(models),
                "models": [model.get("name", "unknown") for model in models[:5]]  # First 5 models
            }
        except Exception as e:
            logger.error(f"Health check failed for {self.get_provider_name()}: {e}")
            return {
                "status": "unhealthy",
                "provider": self.get_provider_name(),
                "error": str(e)
            }


class LLMClientError(Exception):
    """Base exception for LLM client errors"""
    pass


class ModelNotFoundError(LLMClientError):
    """Raised when a requested model is not found"""
    pass


class GenerationError(LLMClientError):
    """Raised when text generation fails"""
    pass


class ConfigurationError(LLMClientError):
    """Raised when client configuration is invalid"""
    pass
