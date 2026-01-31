"""Alembic configuration."""
import os
from alembic import config as alembic_config


def get_config():
    """Get Alembic configuration."""
    cfg = alembic_config.Config("alembic.ini")
    return cfg
