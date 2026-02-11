"""
Shortlist — Application Configuration

All secrets and config loaded from environment variables.
NEVER hardcode secrets. NEVER commit .env files.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, computed_field
from functools import lru_cache
from typing import Optional
import secrets

class Settings(BaseSettings):
    """
    Immutable, validated application configuration.
    All values sourced from environment variables or .env file.
    """

    # Application
    APP_NAME: str = "Shortlist"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|testing|staging|production)$")
    DEBUG: bool = False
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    ALLOWED_ORIGINS=https://shortlist-seven.vercel.app,http://localhost:3000
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    MAX_REQUEST_SIZE_MB: int = 10

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # LLM Providers
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: Optional[str] = None

    # Model selection
    LLM_ANALYSIS_MODEL: str = "llama-3.3-70b-versatile"
    LLM_CODE_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = Field(default=0.15, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int = Field(default=8192, ge=256, le=32768)

    # GitHub Repo Analyzer
    GITHUB_TOKEN: Optional[str] = None  # Optional: for higher API rate limits
    REPO_CLONE_TIMEOUT_SECONDS: int = 120
    REPO_ANALYSIS_TIMEOUT_SECONDS: int = 60
    REPO_MAX_SIZE_MB: int = 500
    TEMP_CLONE_DIR: str = "/tmp/shortlist_repos"

    # Validators
    @field_validator("SUPABASE_URL")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        if v and not v.startswith("https://"):
            raise ValueError("SUPABASE_URL must use HTTPS")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure production uses an explicitly set secret key."""
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and (not v or len(v) < 32):
            raise ValueError(
                "SECRET_KEY must be explicitly set (≥32 chars) in production. "
                "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

@lru_cache()
def get_settings() -> Settings:
    """
    Singleton settings instance — cached after first load.
    Reload requires process restart (secure by design).
    """
    return Settings()
