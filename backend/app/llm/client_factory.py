from typing import Dict, Type, Optional, List
from app.llm.base_client import BaseLLMClient, ConfigurationError
from app.llm.ollama_client import OllamaClient
from app.llm.gemini_client import GeminiClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """Factory for creating and managing LLM clients"""
    
    # Registry of available client classes
    _clients: Dict[str, Type[BaseLLMClient]] = {
        "ollama": OllamaClient,
        "gemini": GeminiClient,
    }
    # Default models for each provider
    _default_models: Dict[str, str] = {
        "ollama": "llama3.2",
        "gemini": "gemini-2.0-flash",
    }
    
    # Model to provider mapping
    _model_providers: Dict[str, str] = {
        # Ollama models
        "gemma3:12b": "ollama",
        "gemma3:27b": "ollama",
        "gemini-1.5-flash": "gemini",
        "gemini-2.0-flash": "gemini",
        "gemini-2.0-flash-lite": "gemini",
        "gemini-2.0-flash-exp": "gemini",
        "gemini-2.0-pro": "gemini",
        "gemini-2.0-pro-exp": "gemini",
    }

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers"""
        return list(cls._clients.keys())

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get the models for all providers"""
        return list(cls._model_providers.keys())
    
    @classmethod
    def register_client(cls, provider: str, client_class: Type[BaseLLMClient]):
        """Register a new LLM client"""
        cls._clients[provider] = client_class
        logger.info(f"Registered LLM client: {provider}")
    
    @classmethod
    def get_provider_for_model(cls, model: str) -> str:
        """Get the provider name for a given model"""
        return cls._model_providers[model]
    
    @classmethod
    def create_client(cls, model: str) -> BaseLLMClient:
        """Create an LLM client instance"""

        provider = cls._model_providers[model]

        if provider is None:
            raise ConfigurationError(f"Unknown model: {model}")

        if provider not in cls._clients:
            raise ConfigurationError(f"Unknown LLM provider: {provider}")
        
        client_class = cls._clients[provider]
        return client_class()
