"""
# Architect: Meet Kumar
# InsightAI - Core Configuration
"""

from pydantic_settings import BaseSettings, SettingsConfigDict as ConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file explicitly
load_dotenv(override=True)
print(f"DEBUG: GROQ_API_KEY from os.environ: {'SET' if os.environ.get('GROQ_API_KEY') else 'NOT SET'}")

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "InsightAI"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/insightai"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None

    # Groq
    GROQ_API_KEY: Optional[str] = None
    
    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "temp_data"
    MAX_FILE_SIZE: int = 104857600  # 100MB
    
    # Docker Sandbox
    DOCKER_TIMEOUT: int = 300
    DOCKER_MEMORY_LIMIT: str = "512m"
    DOCKER_CPU_LIMIT: float = 1.0
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
print(f"DEBUG: GROQ_API_KEY is {'set' if settings.GROQ_API_KEY else 'NOT set'}")
