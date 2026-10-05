import os
import sys
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

def find_aaroh_ai_path() -> Path:
    # 1. Check environment variable
    if os.getenv("AAROH_AI_PATH"):
        env_path = Path(os.getenv("AAROH_AI_PATH")).resolve()
        if env_path.exists():
            return env_path

    # 2. Check standard directory relative to this config file
    # backend/app/core/config.py -> parents[3] is Aaroh-Frontend
    current_file = Path(__file__).resolve()
    for parent in current_file.parents:
        candidate = parent / "Aaroh-AI"
        if candidate.exists() and (candidate / "src" / "aaroh").exists():
            return candidate
        # Also check parent's parent
        candidate_sibling = parent.parent / "Aaroh-AI"
        if candidate_sibling.exists() and (candidate_sibling / "src" / "aaroh").exists():
            return candidate_sibling

    # Fallback to default desktop path
    fallback = Path("C:/Users/Mayank/OneDrive/Desktop/Aaroh-AI")
    return fallback

AAROH_AI_DIR = find_aaroh_ai_path()

# Automatically add Aaroh-AI and its src directory to sys.path so modules resolve directly
if str(AAROH_AI_DIR) not in sys.path:
    sys.path.insert(0, str(AAROH_AI_DIR))
if str(AAROH_AI_DIR / "src") not in sys.path:
    sys.path.insert(0, str(AAROH_AI_DIR / "src"))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AAROH Platform API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["*"]

    # MongoDB - Authentication & Identity Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "aaroh_auth_db"
    MONGODB_USE_MOCK_FALLBACK: bool = True

    # PostgreSQL - Learning & Curriculum Database
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "aaroh_admin"
    POSTGRES_PASSWORD: str = "aaroh_secure_pass_2026"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "aaroh_learning_db"
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_DB_PATH: str = "data/aaroh_local.db"


    # JWT Authentication
    JWT_SECRET_KEY: str = "aaroh_jwt_super_secret_production_key_indic_2026_xyz!"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Aaroh-AI Core Integration
    AAROH_AI_PATH: str = str(AAROH_AI_DIR)
    AAROH_AI_CONFIG_PATH: str = str(AAROH_AI_DIR / "config" / "config.yaml")
    AAROH_AI_MODEL_CONFIG_PATH: str = str(AAROH_AI_DIR / "config" / "model_config.yaml")
    AAROH_AI_PROMPT_CONFIG_PATH: str = str(AAROH_AI_DIR / "config" / "prompt_config.yaml")

    # AI & Cloud API Keys (Loaded from environment, never hardcoded)
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROK_API_KEY: Optional[str] = None
    TRANSLATION_API_KEY: Optional[str] = None
    STT_API_KEY: Optional[str] = None
    TTS_API_KEY: Optional[str] = None

    # Storage (S3 / Local Object Storage)
    S3_ENDPOINT: Optional[str] = None
    S3_BUCKET: str = "aaroh-content-storage"
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    LOCAL_STORAGE_DIR: str = "data/storage"

    # Cache & Queue
    REDIS_URL: Optional[str] = None


settings = Settings()
