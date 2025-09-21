"""
YAML configuration handler for database settings.
"""

import yaml
import os
from typing import Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """Database configuration model."""

    host: str
    port: int = Field(default=5432, ge=1, le=65535)
    database: str
    username: str
    password: str
    ssl: bool = False


def get_config_path() -> str:
    """Get path to database configuration file."""
    # Always use project root data directory
    # If running from backend directory, go up one level
    current_dir = os.getcwd()
    if current_dir.endswith("/backend") or current_dir.endswith("\\backend"):
        config_dir = "../data/settings"
    else:
        config_dir = "./data/settings"

    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "database.yaml")


def load_database_config() -> Optional[DatabaseConfig]:
    """
    Load database config from YAML file or environment variables.

    Priority:
    1. Environment variables (NOC_DATABASE, NOC_USERNAME, NOC_PASSWORD)
    2. YAML configuration file (./data/settings/database.yaml)

    Returns:
        DatabaseConfig if configuration found, None otherwise
    """
    # Check environment variables first
    env_host = os.getenv("NOC_DATABASE")
    env_username = os.getenv("NOC_USERNAME")
    env_password = os.getenv("NOC_PASSWORD")
    env_port = os.getenv("NOC_DATABASE_PORT", "5432")
    env_database = os.getenv("NOC_DATABASE_NAME", "noc_canvas")
    env_ssl = os.getenv("NOC_DATABASE_SSL", "false").lower() in ("true", "1", "yes")

    if env_host and env_username and env_password:
        logger.info("Loading database configuration from environment variables")
        try:
            config = DatabaseConfig(
                host=env_host,
                port=int(env_port),
                database=env_database,
                username=env_username,
                password=env_password,
                ssl=env_ssl,
            )

            # Auto-create YAML config from environment variables if it doesn't exist
            config_path = get_config_path()
            if not os.path.exists(config_path):
                logger.info("Creating database.yaml from environment variables")
                if save_database_config(config):
                    logger.info(f"Database configuration saved to {config_path}")
                else:
                    logger.warning("Failed to save database configuration to YAML")

            return config
        except ValueError as e:
            logger.error(f"Invalid environment variable configuration: {e}")
            return None

    # Fall back to YAML file
    config_path = get_config_path()
    if os.path.exists(config_path):
        logger.info("Loading database configuration from YAML file")
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
                if config_data:
                    return DatabaseConfig(**config_data)
        except (yaml.YAMLError, ValueError) as e:
            logger.error(f"Failed to load YAML configuration: {e}")
            return None
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config_path}")
            return None

    logger.warning(
        "No database configuration found in environment variables or YAML file"
    )
    return None


def save_database_config(config: DatabaseConfig) -> bool:
    """
    Save database config to YAML file.

    Args:
        config: DatabaseConfig object to save

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        config_path = get_config_path()

        # Convert to dict and ensure proper formatting
        config_dict = config.dict()

        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        logger.info(f"Database configuration saved to {config_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save database configuration: {e}")
        return False


def validate_database_config(config: Optional[DatabaseConfig]) -> bool:
    """
    Validate database configuration.

    Args:
        config: DatabaseConfig to validate

    Returns:
        True if configuration is valid, False otherwise
    """
    if not config:
        return False

    # Check required fields
    if not all([config.host, config.database, config.username, config.password]):
        logger.error("Missing required database configuration fields")
        return False

    # Validate port range
    if not (1 <= config.port <= 65535):
        logger.error(f"Invalid database port: {config.port}")
        return False

    return True


def get_database_url(config: Optional[DatabaseConfig] = None) -> str:
    """
    Get PostgreSQL database URL from config.

    Args:
        config: Optional DatabaseConfig, will load if not provided

    Returns:
        PostgreSQL connection URL

    Raises:
        RuntimeError: If no valid configuration found
    """
    if not config:
        config = load_database_config()

    if not config or not validate_database_config(config):
        raise RuntimeError(
            "No valid database configuration found. "
            "Please set environment variables (NOC_DATABASE, NOC_USERNAME, NOC_PASSWORD) "
            "or create ./data/settings/database.yaml"
        )

    # Build connection URL
    if config.ssl:
        return f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}?sslmode=require"
    else:
        return f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"


def create_sample_config() -> bool:
    """
    Create a sample database configuration file.

    Returns:
        True if sample created successfully, False otherwise
    """
    try:
        config_path = get_config_path()

        # Don't overwrite existing config
        if os.path.exists(config_path):
            logger.info(f"Configuration file already exists: {config_path}")
            return False

        sample_config = {
            "host": "localhost",
            "port": 5432,
            "database": "noc_canvas",
            "username": "noc_user",
            "password": "change_me",
            "ssl": False,
        }

        with open(config_path, "w") as f:
            f.write("# NOC Canvas Database Configuration\n")
            f.write("# This file contains sensitive information - keep it secure!\n\n")
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)

        # Set restrictive permissions
        os.chmod(config_path, 0o600)

        logger.info(f"Sample database configuration created: {config_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create sample configuration: {e}")
        return False
