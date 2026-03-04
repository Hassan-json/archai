"""AI provider router for managing multiple providers."""

from typing import AsyncIterator, Optional

from archai.ai.base import AIProvider, Message
from archai.ai.anthropic_provider import AnthropicProvider
from archai.ai.claude_cli_provider import ClaudeCLIProvider
from archai.ai.ollama_provider import OllamaProvider
from archai.ai.openai_provider import OpenAIProvider
from archai.ai.litellm_provider import LiteLLMProvider
from archai.ai.gemini_provider import GeminiProvider
from archai.config.settings import Settings, get_settings
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class AIRouter:
    """Routes AI requests to the configured provider."""

    PROVIDER_CLASSES = {
        "anthropic": AnthropicProvider,
        "claude-cli": ClaudeCLIProvider,
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "litellm": LiteLLMProvider,
        "gemini": GeminiProvider,
    }

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize the router.

        Args:
            settings: Optional settings (uses global if None)
        """
        self._settings = settings or get_settings()
        self._providers: dict[str, AIProvider] = {}
        self._current_provider: Optional[str] = None

    @property
    def current_provider(self) -> str:
        """Get current provider name.

        Returns:
            Provider name
        """
        return self._current_provider or self._settings.default_provider

    @property
    def current_model(self) -> str:
        """Get current model name.

        Returns:
            Model name
        """
        provider = self._get_provider()
        return provider.model

    def _get_provider(self, name: Optional[str] = None) -> AIProvider:
        """Get or create a provider instance.

        Args:
            name: Provider name (uses current if None)

        Returns:
            AIProvider instance
        """
        name = name or self.current_provider

        if name not in self._providers:
            if name not in self.PROVIDER_CLASSES:
                raise ValueError(f"Unknown provider: {name}")

            config = self._settings.get_provider_config(name)
            provider_class = self.PROVIDER_CLASSES[name]
            self._providers[name] = provider_class(config)

        return self._providers[name]

    def set_provider(self, name: str) -> None:
        """Set the current provider.

        Args:
            name: Provider name
        """
        if name not in self.PROVIDER_CLASSES:
            raise ValueError(f"Unknown provider: {name}")
        self._current_provider = name
        self._settings.set_provider(name)
        logger.info(f"Switched to provider: {name}")

    def set_model(self, model: str, provider: Optional[str] = None) -> None:
        """Set the model for a provider.

        Args:
            model: Model name
            provider: Provider name (uses current if None)
        """
        provider = provider or self.current_provider
        self._settings.set_model(provider, model)

        # Clear cached provider to pick up new model
        if provider in self._providers:
            del self._providers[provider]

        logger.info(f"Set model for {provider}: {model}")

    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
        provider: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Send a chat request.

        Args:
            messages: List of messages
            stream: Whether to stream the response
            provider: Optional provider override

        Yields:
            Response chunks
        """
        ai_provider = self._get_provider(provider)
        async for chunk in ai_provider.chat(messages, stream):
            yield chunk

    async def chat_complete(
        self,
        messages: list[Message],
        provider: Optional[str] = None,
    ) -> str:
        """Send a chat request and get complete response.

        Args:
            messages: List of messages
            provider: Optional provider override

        Returns:
            Complete response text
        """
        ai_provider = self._get_provider(provider)
        return await ai_provider.chat_complete(messages)

    async def get_models(self, provider: Optional[str] = None) -> list[str]:
        """Get available models for a provider.

        Args:
            provider: Provider name (uses current if None)

        Returns:
            List of model names
        """
        ai_provider = self._get_provider(provider)
        return await ai_provider.get_models()

    async def is_available(self, provider: Optional[str] = None) -> bool:
        """Check if a provider is available.

        Args:
            provider: Provider name (uses current if None)

        Returns:
            True if available
        """
        ai_provider = self._get_provider(provider)
        return await ai_provider.is_available()

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names.

        Returns:
            List of provider names
        """
        return list(self.PROVIDER_CLASSES.keys())

    async def check_all_providers(self) -> dict[str, bool]:
        """Check availability of all providers.

        Returns:
            Dict mapping provider names to availability
        """
        results = {}
        for name in self.PROVIDER_CLASSES:
            try:
                results[name] = await self.is_available(name)
            except Exception:
                results[name] = False
        return results
