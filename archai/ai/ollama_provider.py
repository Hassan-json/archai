"""Ollama AI provider implementation."""

from typing import AsyncIterator

import ollama
from ollama import AsyncClient

from archai.ai.base import AIProvider, Message
from archai.config.settings import ProviderConfig
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(AIProvider):
    """Ollama AI provider."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize Ollama provider.

        Args:
            config: Provider configuration
        """
        self._config = config
        self._model = config.model
        self._client = AsyncClient(host=config.base_url)

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Send a chat request to Ollama.

        Args:
            messages: List of messages
            stream: Whether to stream the response

        Yields:
            Response chunks
        """
        message_dicts = [m.to_dict() for m in messages]

        try:
            if stream:
                response = await self._client.chat(
                    model=self._model,
                    messages=message_dicts,
                    stream=True,
                )
                async for chunk in response:
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]
            else:
                response = await self._client.chat(
                    model=self._model,
                    messages=message_dicts,
                    stream=False,
                )
                yield response["message"]["content"]

        except ollama.ResponseError as e:
            logger.error(f"Ollama error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {e}")
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
        """Get available Ollama models.

        Returns:
            List of model names
        """
        try:
            response = await self._client.list()
            return [model["name"] for model in response.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    async def is_available(self) -> bool:
        """Check if Ollama is available.

        Returns:
            True if available
        """
        try:
            await self._client.list()
            return True
        except Exception:
            return False
