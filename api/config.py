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
    
    # Feature flags
    enable_background_tasks: bool = True
    enable_mock_data: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
