import os
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"

    MONGODB_URI: str = "mongodb+srv://jainovatechnologies_db_user:zPYPIkqhpza6FTmu@jainova.tpljalq.mongodb.net/"
    MONGODB_DATABASE: str = "estate_intelligence"

    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API Key")
    OPENROUTER_MODEL: str = "nvidia/nemotron-3.5-lightning:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    FRONTEND_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ADMIN_API_KEY: str = "estate_intel_admin_secret_key"

    INGESTION_RATE_LIMIT_DELAY: float = 1.0
    INGESTION_MAX_PAGES_PER_DOMAIN: int = 50
    INGESTION_REQUEST_TIMEOUT: int = 15
    USER_AGENT: str = "EstateIntelligenceBot/1.0 (+https://estateintelligence.ai/bot)"

    @property
    def cors_origins(self) -> List[str]:
        if not self.FRONTEND_ORIGINS:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]


settings = Settings()
