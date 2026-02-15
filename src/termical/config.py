"""Configuration management for termical."""
import os
from pathlib import Path
from typing import Any

import toml
import keyring
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application constants
APP_NAME = "termical"
CONFIG_DIR = Path.home() / f".{APP_NAME}"
CONFIG_FILE = CONFIG_DIR / "config.toml"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"

# Keyring service name
KEYRING_SERVICE = "termical"
KEYRING_OPENAI_KEY = "openai_api_key"


class Config:
    """Configuration manager."""
    
    def __init__(self):
        """Initialize configuration."""
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self._data: dict[str, Any] = {}
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing config if available
        if self.config_file.exists():
            self.load()
    
    def load(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                self._data = toml.load(f)
    
    def save(self) -> None:
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            toml.dump(self._data, f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
    
    def get_database_url(self) -> str:
        """Get PostgreSQL connection string.
        
        Returns:
            Database connection URL
            
        Raises:
            ValueError: If database configuration is incomplete
        """
        host = self.get("database.host")
        port = self.get("database.port", 5432)
        user = self.get("database.user")
        password = self.get("database.password")
        database = self.get("database.name")
        
        if not all([host, user, password, database]):
            raise ValueError("Incomplete database configuration. Run 'termical setup'.")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def is_configured(self) -> bool:
        """Check if application is configured.
        
        Returns:
            True if configured, False otherwise
        """
        try:
            # Check database config
            self.get_database_url()
            
            # Check OpenAI API key
            if not get_openai_key():
                return False
            
            # Check Google credentials exist
            if not CREDENTIALS_FILE.exists():
                return False
            
            return True
        except (ValueError, KeyError):
            return False


class SecretManager:
    """Secure secret storage using system keyring."""
    
    @staticmethod
    def set_secret(key: str, value: str) -> None:
        """Store a secret securely.
        
        Args:
            key: Secret identifier
            value: Secret value
        """
        keyring.set_password(KEYRING_SERVICE, key, value)
    
    @staticmethod
    def get_secret(key: str) -> str | None:
        """Retrieve a secret.
        
        Args:
            key: Secret identifier
            
        Returns:
            Secret value or None if not found
        """
        return keyring.get_password(KEYRING_SERVICE, key)
    
    @staticmethod
    def delete_secret(key: str) -> None:
        """Delete a secret.
        
        Args:
            key: Secret identifier
        """
        try:
            keyring.delete_password(KEYRING_SERVICE, key)
        except keyring.errors.PasswordDeleteError:
            pass


def get_openai_key() -> str | None:
    """Get OpenAI API key from secure storage.
    
    Returns:
        API key or None if not configured
    """
    # Try environment variable first (for development)
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    
    # Then try keyring
    return SecretManager.get_secret(KEYRING_OPENAI_KEY)


def set_openai_key(api_key: str) -> None:
    """Store OpenAI API key securely.
    
    Args:
        api_key: OpenAI API key
    """
    SecretManager.set_secret(KEYRING_OPENAI_KEY, api_key)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
