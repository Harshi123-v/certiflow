from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "CertiFlow - Bulk Certificate Generation & Tracking System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration (SQLite by default, PostgreSQL fully supported)
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'certiflow.db'}"
    
    # Storage configuration
    STORAGE_DIR: Path = BASE_DIR / "storage" / "certificates"
    
    # Constraints
    MAX_BATCH_SIZE: int = 500
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure storage directory exists
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
