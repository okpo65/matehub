from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_result_expires: int = 3600
    
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Database Configuration
    database_url: str = "postgresql://matehub:password@localhost:5432/matehub"
    
    # PostgreSQL specific settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "matehub"
    postgres_password: str = "password"
    postgres_db: str = "matehub"
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_model: str = "gpt-3.5-turbo"
    max_tokens: int = 2048
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
    # Kakao OAuth Configuration
    kakao_rest_api_key: Optional[str] = None
    kakao_client_secret: Optional[str] = None
    kakao_redirect_uri: str = "http://localhost:8000/auth/kakao/callback/page"
    
    # JWT Configuration
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 24
    jwt_refresh_token_expire_days: int = 30
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL URL from components"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()
