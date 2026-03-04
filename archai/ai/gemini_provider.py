"""Google Gemini AI provider implementation."""

from typing import AsyncIterator

from archai.ai.base import AIProvider, Message
from archai.config.settings import ProviderConfig
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(AIProvider):
    """Google Gemini AI provider.

    Uses the google-generativeai library for Gemini API access.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize Gemini provider.

        Args:
            config: Provider configuration
        """
        self._config = config
        self._model = config.model or "gemini-2.0-flash"
        self._client = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Gemini client."""
        if not self._initialized:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._config.api_key)
                self._client = genai.GenerativeModel(self._model)
                self._initialized = True
            except ImportError:
                raise ImportError(
                    "google-generativeai package is required for Gemini provider. "
                    "Install with: pip install google-generativeai"
                )

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model(self) -> str:
        return self._model

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert messages to Gemini format.

        Gemini uses 'user' and 'model' roles, and has a different format.
        System messages are prepended to the first user message.
        """
        gemini_messages = []
        system_content = ""

        for msg in messages:
            role = msg.role.value
            content = msg.content

            if role == "system":
                system_content = content + "\n\n"
            elif role == "user":
                # Prepend system content to first user message
                if system_content:
                    content = system_content + content
                    system_content = ""
                gemini_messages.append({
                    "role": "user",
                    "parts": [content]
                })
            elif role == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [content]
                })

        return gemini_messages

    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Send a chat request to Gemini.

        Args:
            messages: List of messages
            stream: Whether to stream the response

        Yields:
            Response chunks
        """
        self._ensure_initialized()

        gemini_messages = self._convert_messages(messages)

        try:
            if stream:
                # Start chat with history (all but last message)
                history = gemini_messages[:-1] if len(gemini_messages) > 1 else []
                chat = self._client.start_chat(history=history)

                # Get the last user message
                last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""

                # Stream response
                response = await chat.send_message_async(
                    last_message,
                    stream=True
                )

                async for chunk in response:
                    if chunk.text:
                        yield chunk.text
            else:
                # Non-streaming
                history = gemini_messages[:-1] if len(gemini_messages) > 1 else []
                chat = self._client.start_chat(history=history)

                last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""

                response = await chat.send_message_async(last_message)
                yield response.text

        except Exception as e:
            logger.error(f"Gemini error: {e}")
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
        """Get available Gemini models.

        Returns:
            List of model names
        """
        return [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ]

    async def is_available(self) -> bool:
        """Check if Gemini is available.

        Returns:
            True if available and API key is set
        """
        if not self._config.api_key:
            return False
        try:
            self._ensure_initialized()
            return True
        except Exception:
            return False
