"""AURELIUS REST API package."""
try:
    from api.config import settings
except ImportError:
    # Handle relative imports when running as module
    from config import settings

__version__ = "1.0.0"
__author__ = "AURELIUS Team"

__all__ = ["settings"]
