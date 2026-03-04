"""Configuration settings for Archai."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""

    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: str = "llama3.2"
    timeout: int = 120
    max_tokens: int = 4096


class Settings(BaseModel):
    """Application settings."""

    default_provider: str = "ollama"
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    default_language: str = "python"
    theme: str = "dark"
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".archai")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        # Set up default providers if not provided
        if not self.providers:
            self.providers = {
                "anthropic": ProviderConfig(
                    api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                    model="claude-sonnet-4-20250514",
                ),
                "claude-cli": ProviderConfig(
                    model="claude-sonnet-4-20250514",
                    timeout=300,
                ),
                "ollama": ProviderConfig(
                    base_url="http://localhost:11434",
                    model="llama3.2",
                ),
                "openai": ProviderConfig(
                    api_key=os.getenv("OPENAI_API_KEY", ""),
                    model="gpt-4",
                ),
                "litellm": ProviderConfig(
                    model="anthropic/claude-3-sonnet",
                ),
                "gemini": ProviderConfig(
                    api_key=os.getenv("GOOGLE_API_KEY", ""),
                    model="gemini-2.0-flash",
                ),
            }

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from config file.

        Args:
            config_path: Optional path to config file

        Returns:
            Settings instance
        """
        if config_path is None:
            config_path = Path.home() / ".archai" / "config.yaml"

        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}

            # Expand environment variables in API keys
            if "providers" in data:
                for provider_name, provider_config in data["providers"].items():
                    if "api_key" in provider_config:
                        api_key = provider_config["api_key"]
                        if api_key and api_key.startswith("${") and api_key.endswith("}"):
                            env_var = api_key[2:-1]
                            provider_config["api_key"] = os.getenv(env_var, "")

            data["config_dir"] = config_path.parent
            return cls(**data)

        return cls()

    def save(self, config_path: Optional[Path] = None) -> None:
        """Save settings to config file.

        Args:
            config_path: Optional path to config file
        """
        if config_path is None:
            config_path = self.config_dir / "config.yaml"

        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = self.model_dump(exclude={"config_dir"})

        # Convert Path objects to strings for YAML
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_provider_config(self, provider: Optional[str] = None) -> ProviderConfig:
        """Get configuration for a provider.

        Args:
            provider: Provider name (uses default if None)

        Returns:
            ProviderConfig instance
        """
        provider = provider or self.default_provider
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        return self.providers[provider]

    def set_provider(self, provider: str) -> None:
        """Set the default provider.

        Args:
            provider: Provider name
        """
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        self.default_provider = provider

    def set_model(self, provider: str, model: str) -> None:
        """Set the model for a provider.

        Args:
            provider: Provider name
            model: Model name
        """
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        self.providers[provider].model = model


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance."""
    global _settings
    _settings = None
