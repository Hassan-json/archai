"""OpenAI AI provider implementation."""

from typing import AsyncIterator

from openai import AsyncOpenAI, OpenAIError

from archai.ai.base import AIProvider, Message
from archai.config.settings import ProviderConfig
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI AI provider."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        self._config = config
        self._model = config.model
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            timeout=config.timeout,
        )

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Send a chat request to OpenAI.

        Args:
            messages: List of messages
            stream: Whether to stream the response

        Yields:
            Response chunks
        """
        message_dicts = [m.to_dict() for m in messages]

        try:
            if stream:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=message_dicts,
                    max_tokens=self._config.max_tokens,
                    stream=True,
                )
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=message_dicts,
                    max_tokens=self._config.max_tokens,
                    stream=False,
                )
                if response.choices:
                    yield response.choices[0].message.content or ""

        except OpenAIError as e:
            logger.error(f"OpenAI error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error communicating with OpenAI: {e}")
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
        """Get available OpenAI models.

        Returns:
            List of model names
        """
        try:
            response = await self._client.models.list()
            # Filter for chat models
            chat_models = [
                model.id
                for model in response.data
                if "gpt" in model.id.lower()
            ]
            return sorted(chat_models)
        except Exception as e:
            logger.error(f"Error listing OpenAI models: {e}")
            return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

    async def is_available(self) -> bool:
        """Check if OpenAI is available.

        Returns:
            True if available and API key is set
        """
        if not self._config.api_key:
            return False
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
