from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Expense Analyser API"
    
    # Security
    SECRET_KEY: str = "supersecretkey"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str = "postgresql://expense_user:expense_password@localhost:5432/expense_db"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Database configuration (used in docker-compose)
    POSTGRES_USER: str = "expense_user"
    POSTGRES_PASSWORD: str = "expense_password"
    POSTGRES_DB: str = "expense_db"
    
    # API Secret Key (for docker-compose)
    API_SECRET_KEY: str = "supersecretkey"
    
    # LLM Integration
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "gemini"
    
    # Redis Cache Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Auth0 Configuration
    AUTH0_DOMAIN: str = ""
    AUTH0_CLIENT_ID: str = ""
    AUTH0_CLIENT_SECRET: str = ""
    AUTH0_API_AUDIENCE: str = ""
    
    # Pydantic v2 uses model_config instead of Config class
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
