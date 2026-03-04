"""LiteLLM AI provider implementation."""

from typing import Any, AsyncIterator, Optional

import litellm
from litellm import acompletion

from archai.ai.base import AIProvider, Message
from archai.config.settings import ProviderConfig
from archai.utils.logger import get_logger

logger = get_logger(__name__)

# Suppress LiteLLM verbose logging
litellm.suppress_debug_info = True


class LiteLLMProvider(AIProvider):
    """LiteLLM AI provider supporting multiple backends.

    IMPORTANT: Model names MUST include the provider prefix!
    Format: provider/model-name

    Examples:
        - anthropic/claude-sonnet-4.5
        - openai/gpt-4
        - ollama/llama3.2
        - groq/llama-3-70b

    LiteLLM supports custom endpoints via:
    - base_url: Custom API endpoint (e.g., http://localhost:8000/v1)
    - api_key: API key for the endpoint

    Example config for custom endpoint:
        providers:
          litellm:
            base_url: http://localhost:8000/v1
            api_key: your-api-key
            model: openai/my-local-model
    """

    # Known model prefixes for auto-detection
    MODEL_PREFIXES = {
        "claude": "anthropic",
        "gpt-": "openai",
        "gpt4": "openai",
        "o1": "openai",
        "llama": "ollama",
        "mistral": "ollama",
        "codellama": "ollama",
        "gemini": "google",
        "palm": "google",
    }

    # Cloud providers that have their own endpoints (don't use api_base)
    CLOUD_PROVIDERS = {
        "anthropic",
        "openai",
        "google",
        "cohere",
        "mistral",
        "groq",
        "together_ai",
        "anyscale",
        "perplexity",
        "fireworks_ai",
        "deepinfra",
        "ai21",
    }

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize LiteLLM provider.

        Args:
            config: Provider configuration
        """
        self._config = config
        self._model = self._normalize_model_name(config.model)
        self._base_url = config.base_url
        self._api_key = config.api_key

    def _normalize_model_name(self, model: str) -> str:
        """Ensure model name has provider prefix.

        Args:
            model: Model name (with or without prefix)

        Returns:
            Model name with provider prefix
        """
        # If we have a base_url (custom proxy), DON'T add provider prefix
        # The proxy handles routing internally, we just pass the model name
        if self._config.base_url:
            logger.info(f"Using custom proxy, passing model as-is: {model}")
            return model

        # Already has a prefix (contains /)
        if "/" in model:
            return model

        # Try to auto-detect provider from model name
        model_lower = model.lower()
        for prefix, provider in self.MODEL_PREFIXES.items():
            if model_lower.startswith(prefix):
                normalized = f"{provider}/{model}"
                logger.info(f"Auto-detected provider: {model} -> {normalized}")
                return normalized

        # Can't determine provider - warn user
        logger.warning(
            f"Model '{model}' has no provider prefix. "
            f"LiteLLM requires format: provider/model (e.g., anthropic/claude-sonnet-4.5)"
        )
        return model

    def _get_model_provider(self) -> Optional[str]:
        """Extract provider from model name.

        Returns:
            Provider name or None
        """
        if "/" in self._model:
            return self._model.split("/")[0].lower()
        return None

    def _is_cloud_provider(self) -> bool:
        """Check if current model uses a cloud provider.

        Returns:
            True if using a cloud provider (shouldn't use custom api_base)
        """
        provider = self._get_model_provider()
        return provider in self.CLOUD_PROVIDERS if provider else False

    def _get_completion_kwargs(self) -> dict[str, Any]:
        """Build kwargs for litellm completion call.

        Returns:
            Dict of kwargs to pass to acompletion
        """
        import os

        # When using custom base_url (proxy), use openai/ prefix to route through proxy
        # The proxy handles the actual provider routing internally
        if self._base_url:
            # For proxy: use openai/model format and set dummy key if none provided
            model_for_proxy = self._model
            if "/" not in model_for_proxy:
                model_for_proxy = f"openai/{model_for_proxy}"
            elif not model_for_proxy.startswith("openai/"):
                # Convert anthropic/claude -> openai/anthropic/claude for proxy
                model_for_proxy = f"openai/{model_for_proxy}"

            # Ensure URL ends with /v1 for OpenAI-compatible endpoints
            base_url = self._base_url.rstrip("/")
            if not base_url.endswith("/v1"):
                base_url = f"{base_url}/v1"

            kwargs: dict[str, Any] = {
                "model": model_for_proxy,
                "max_tokens": self._config.max_tokens,
                "timeout": self._config.timeout,
                "api_base": base_url,
                "api_key": self._api_key if self._api_key else "not-needed",  # Dummy key for proxy
            }
            return kwargs

        # Standard LiteLLM (no proxy) - route to actual providers
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._config.max_tokens,
            "timeout": self._config.timeout,
        }

        # Handle API key - LiteLLM uses different env vars per provider
        # If user provides api_key via CLI, set it for the appropriate provider
        provider = self._get_model_provider()

        if self._api_key:
            # Set provider-specific env var so LiteLLM picks it up
            if provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = self._api_key
            elif provider == "openai":
                os.environ["OPENAI_API_KEY"] = self._api_key
            elif provider in ("gemini", "google"):
                os.environ["GEMINI_API_KEY"] = self._api_key
            elif provider == "groq":
                os.environ["GROQ_API_KEY"] = self._api_key
            elif provider == "together_ai":
                os.environ["TOGETHER_API_KEY"] = self._api_key
            elif provider == "mistral":
                os.environ["MISTRAL_API_KEY"] = self._api_key
            else:
                # Generic fallback
                kwargs["api_key"] = self._api_key

        return kwargs

    @property
    def name(self) -> str:
        return "litellm"

    @property
    def model(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Send a chat request via LiteLLM.

        Args:
            messages: List of messages
            stream: Whether to stream the response

        Yields:
            Response chunks
        """
        message_dicts = [m.to_dict() for m in messages]

        try:
            kwargs = self._get_completion_kwargs()
            kwargs["messages"] = message_dicts
            kwargs["stream"] = stream

            if stream:
                response = await acompletion(**kwargs)
                async for chunk in response:
                    if (
                        chunk.choices
                        and chunk.choices[0].delta
                        and chunk.choices[0].delta.content
                    ):
                        yield chunk.choices[0].delta.content
            else:
                response = await acompletion(**kwargs)
                if response.choices and response.choices[0].message:
                    yield response.choices[0].message.content or ""

        except litellm.exceptions.BadRequestError as e:
            error_msg = str(e)
            if "Provider NOT provided" in error_msg or "provider" in error_msg.lower():
                logger.error(
                    f"LiteLLM error: Model '{self._model}' needs provider prefix. "
                    f"Use format: provider/model (e.g., anthropic/claude-sonnet-4.5, openai/gpt-4)"
                )
                raise ValueError(
                    f"Invalid model format: '{self._model}'. "
                    f"LiteLLM requires provider prefix. Examples:\n"
                    f"  - anthropic/claude-sonnet-4.5\n"
                    f"  - openai/gpt-4\n"
                    f"  - ollama/llama3.2\n"
                    f"  - groq/llama-3-70b"
                ) from e
            logger.error(f"LiteLLM error: {e}")
            raise
        except Exception as e:
            logger.error(f"LiteLLM error: {e}")
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
        """Get available LiteLLM models.

        Returns:
            List of commonly used model strings
        """
        # LiteLLM supports many providers, return common ones
        return [
            # Anthropic Claude
            "anthropic/claude-opus-4-20250514",
            "anthropic/claude-sonnet-4-20250514",
            "anthropic/claude-3-5-haiku-20241022",
            # Google Gemini
            "gemini/gemini-2.0-flash",
            "gemini/gemini-1.5-pro",
            "gemini/gemini-1.5-flash",
            # OpenAI
            "openai/gpt-4o",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            # Local
            "ollama/llama3.2",
            "ollama/mistral",
            # Other cloud
            "groq/llama-3.3-70b-versatile",
            "together_ai/meta-llama/Llama-3-70b-chat-hf",
        ]

    async def is_available(self) -> bool:
        """Check if LiteLLM is available.

        Returns:
            True (LiteLLM is a routing library, always available)
        """
        return True
