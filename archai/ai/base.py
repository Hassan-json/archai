"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator


class Role(str, Enum):
    """Message role."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A chat message."""

    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary format.

        Returns:
            Dictionary with role and content
        """
        return {"role": self.role.value, "content": self.content}


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name
        """
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Get the current model name.

        Returns:
            Model name
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Send a chat request.

        Args:
            messages: List of messages
            stream: Whether to stream the response

        Yields:
            Response chunks
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_models(self) -> list[str]:
        """Get available models.

        Returns:
            List of model names
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available.

        Returns:
            True if available
        """
        pass
