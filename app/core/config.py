import os
import secrets
import sys
from pathlib import Path
from typing import Annotated, Any, Optional, List
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from pydantic import Field, field_validator, model_validator

def find_aaroh_ai_path() -> Path:
    if os.getenv("AAROH_AI_PATH"):
        env_path = Path(os.getenv("AAROH_AI_PATH")).resolve()
        if env_path.exists():
            return env_path

    current_file = Path(__file__).resolve()
    for parent in current_file.parents:
        candidates = [
            parent / "Aaroh-AI",
            parent / "Aaroh-AI" / "Aaroh-AI",
            parent.parent / "Aaroh-AI",
            parent.parent / "Aaroh-AI" / "Aaroh-AI",
        ]
        for candidate in candidates:
            if candidate.exists() and (candidate / "src" / "aaroh").exists():
                return candidate

    return (current_file.parents[3] / "Aaroh-AI").resolve()

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
    CORS_ORIGINS: Annotated[List[str], NoDecode] = ["*"]

    # MongoDB - Authentication & Identity Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "aaroh_auth_db"
    MONGODB_USE_MOCK_FALLBACK: bool = True

    # PostgreSQL - Learning & Curriculum Database
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "aaroh_admin"
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "aaroh_learning_db"
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_DB_PATH: str = "data/aaroh_local.db"


    # JWT Authentication
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Demo access. These accounts are provisioned as real demo identities on first login.
    ENABLE_DEMO_LOGINS: bool = True
    DEMO_SCHOOL_ID: str = "SCH_DEMO_01"
    DEMO_SCHOOL_CODE: str = "DEMO01"
    DEMO_DISTRICT_ID: str = "DIST_DEMO_01"
    DEMO_TEACHER_LOGIN: str = "teacher@123"
    DEMO_TEACHER_PASSWORD: str = "teacher@123"
    DEMO_STUDENT_ROLL_NUMBER: str = "24"
    DEMO_STUDENT_PASSWORD: str = "1234"

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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "t", "yes", "y", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "f", "no", "n", "off", "release", "production", "prod"}:
                return False
        return bool(value)

    @field_validator(
        "DATABASE_URL",
        "POSTGRES_PASSWORD",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "OPENAI_API_KEY",
        "GROK_API_KEY",
        "TRANSLATION_API_KEY",
        "STT_API_KEY",
        "TTS_API_KEY",
        "S3_ENDPOINT",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "REDIS_URL",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return stripped
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_deployment_settings(self) -> "Settings":
        env = self.APP_ENV.strip().lower()
        is_production = env in {"production", "prod", "release", "staging"}

        if not self.JWT_SECRET_KEY:
            if is_production:
                raise ValueError("JWT_SECRET_KEY must be set for production deployments.")
            self.JWT_SECRET_KEY = secrets.token_urlsafe(48)

        jwt_secret_lower = self.JWT_SECRET_KEY.lower()
        looks_like_placeholder = (
            "change-me" in jwt_secret_lower
            or "placeholder" in jwt_secret_lower
            or ("secret" in jwt_secret_lower and ("aaroh" in jwt_secret_lower or "production" in jwt_secret_lower))
        )
        if is_production and looks_like_placeholder:
            raise ValueError("JWT_SECRET_KEY is using an unsafe placeholder value.")

        if is_production and self.CORS_ORIGINS == ["*"]:
            raise ValueError("CORS_ORIGINS must list explicit frontend origins in production.")

        if is_production and not self.USE_SQLITE_FALLBACK and not self.DATABASE_URL:
            missing = [
                key
                for key, value in {
                    "POSTGRES_USER": self.POSTGRES_USER,
                    "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
                    "POSTGRES_HOST": self.POSTGRES_HOST,
                    "POSTGRES_DB": self.POSTGRES_DB,
                }.items()
                if not value
            ]
            if missing:
                raise ValueError(f"Missing PostgreSQL settings for production: {', '.join(missing)}")

        return self


settings = Settings()
