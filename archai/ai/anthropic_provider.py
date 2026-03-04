"""Anthropic Claude AI provider implementation."""

from typing import Any, AsyncIterator

import anthropic

from archai.ai.base import AIProvider, Message, Role
from archai.config.settings import ProviderConfig
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider(AIProvider):
    """Anthropic Claude AI provider.

    Supports Claude models via the official Anthropic SDK.

    Models:
        - claude-opus-4-5-20250514 (most capable)
        - claude-sonnet-4-20250514 (balanced)
        - claude-3-5-haiku-20241022 (fast)

    Configuration:
        providers:
          anthropic:
            api_key: ${ANTHROPIC_API_KEY}
            model: claude-sonnet-4-20250514
            max_tokens: 4096
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize Anthropic provider.

        Args:
            config: Provider configuration
        """
        self._config = config
        self._model = config.model or self.DEFAULT_MODEL
        self._api_key = config.api_key
        self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    def _prepare_messages(
        self, messages: list[Message]
    ) -> tuple[str | None, list[dict[str, str]]]:
        """Prepare messages for Anthropic API.

        Anthropic requires system message to be passed separately.

        Args:
            messages: List of Message objects

        Returns:
            Tuple of (system_prompt, message_list)
        """
        system_prompt = None
        api_messages = []

        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_prompt = msg.content
            else:
                api_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        return system_prompt, api_messages

    def _get_completion_kwargs(self) -> dict[str, Any]:
        """Build kwargs for Anthropic completion call.

        Returns:
            Dict of kwargs to pass to messages.create
        """
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._config.max_tokens,
        }

        # Add timeout if specified
        if self._config.timeout:
            kwargs["timeout"] = self._config.timeout

        return kwargs

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Send a chat request via Anthropic API.

        Args:
            messages: List of messages
            stream: Whether to stream the response

        Yields:
            Response chunks
        """
        system_prompt, api_messages = self._prepare_messages(messages)

        try:
            kwargs = self._get_completion_kwargs()
            kwargs["messages"] = api_messages

            if system_prompt:
                kwargs["system"] = system_prompt

            if stream:
                async with self._client.messages.stream(**kwargs) as stream_response:
                    async for text in stream_response.text_stream:
                        yield text
            else:
                response = await self._client.messages.create(**kwargs)
                if response.content and len(response.content) > 0:
                    yield response.content[0].text

        except anthropic.AuthenticationError as e:
            logger.error(f"Anthropic authentication error: {e}")
            raise ValueError(
                "Invalid Anthropic API key. Set ANTHROPIC_API_KEY environment variable "
                "or configure api_key in ~/.archai/config.yaml"
            ) from e
        except anthropic.RateLimitError as e:
            logger.error(f"Anthropic rate limit error: {e}")
            raise ValueError("Anthropic API rate limit exceeded. Please try again later.") from e
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def chat_complete(
        self,
        messages: list[Message],
    ) -> str:
        """Send a chat request and get complete response.

        Args:
            messages: List of messages

        Returns:
            Complete response text
        """
        result = []
        async for chunk in self.chat(messages, stream=False):
            result.append(chunk)
        return "".join(result)

    async def get_models(self) -> list[str]:
        """Get available Anthropic Claude models.

        Returns:
            List of model strings
        """
        return [
            "claude-opus-4-5-20250514",
            "claude-sonnet-4-20250514",
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    async def is_available(self) -> bool:
        """Check if Anthropic API is available.

        Returns:
            True if API key is configured and valid
        """
        if not self._api_key:
            return False

        try:
            # Make a minimal API call to verify credentials
            await self._client.messages.create(
                model=self._model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception as e:
            logger.debug(f"Anthropic availability check failed: {e}")
            return False
