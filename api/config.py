"""API configuration."""
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """API configuration settings."""

    # Server
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_reload: bool = os.getenv("API_RELOAD", "True").lower() == "true"

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "aurelius")
    db_user: str = os.getenv("DB_USER", "aurelius")
    db_password: str = os.getenv("DB_PASSWORD", "aurelius_dev")
    db_echo: bool = os.getenv("DB_ECHO", "False").lower() == "true"

    # Feature flags
    enable_background_tasks: bool = True
    enable_mock_data: bool = True
    enable_truth_backtests: bool = os.getenv("ENABLE_TRUTH_BACKTESTS", "true").lower() == "true"
    enable_truth_validation: bool = os.getenv("ENABLE_TRUTH_VALIDATION", "true").lower() == "true"
    enable_truth_gates: bool = os.getenv("ENABLE_TRUTH_GATES", "true").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


settings = Settings()
