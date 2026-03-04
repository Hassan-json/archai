"""Base architect class for architecture generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Optional

from archai.ai.router import AIRouter
from archai.ai.base import Message, Role
from archai.config.prompts import SYSTEM_PROMPT, get_architecture_prompt


class ArchitectureType(str, Enum):
    """Supported architecture types."""

    MONOLITHIC = "monolithic"
    MICROSERVICES = "microservices"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"
    HEXAGONAL = "hexagonal"


@dataclass
class GeneratedFile:
    """Represents a generated file."""

    path: Path
    content: str
    description: str = ""


@dataclass
class GenerationResult:
    """Result of architecture generation."""

    architecture: ArchitectureType
    root_path: Path
    files: list[GeneratedFile] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


class Architect(ABC):
    """Base class for architecture generators."""

    def __init__(self, router: AIRouter) -> None:
        """Initialize architect.

        Args:
            router: AI router for LLM interactions
        """
        self.router = router

    @property
    @abstractmethod
    def architecture_type(self) -> ArchitectureType:
        """Get the architecture type.

        Returns:
            ArchitectureType enum value
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get architecture description.

        Returns:
            Human-readable description
        """
        pass

    def get_system_prompt(self) -> str:
        """Get the system prompt for this architecture.

        Returns:
            System prompt string
        """
        base_prompt = SYSTEM_PROMPT
        arch_prompt = get_architecture_prompt(self.architecture_type.value)
        return f"{base_prompt}\n\n{arch_prompt}"

    @abstractmethod
    async def generate(
        self,
        description: str,
        output_path: Path,
        language: str = "python",
    ) -> AsyncIterator[str]:
        """Generate architecture based on description.

        Args:
            description: Natural language description of the app
            output_path: Where to create the project
            language: Target programming language

        Yields:
            Progress messages and AI responses
        """
        pass

    @abstractmethod
    def get_template_structure(self, app_name: str) -> dict[str, str]:
        """Get the template directory structure.

        Args:
            app_name: Name of the application

        Returns:
            Dict mapping file paths to descriptions
        """
        pass

    async def _ask_ai(
        self,
        user_message: str,
        context: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Send a message to the AI and stream the response.

        Args:
            user_message: User message
            context: Optional additional context

        Yields:
            Response chunks
        """
        messages = [
            Message(role=Role.SYSTEM, content=self.get_system_prompt()),
        ]

        if context:
            messages.append(Message(role=Role.USER, content=context))
            messages.append(
                Message(
                    role=Role.ASSISTANT,
                    content="I understand the context. Please proceed with your request.",
                )
            )

        messages.append(Message(role=Role.USER, content=user_message))

        async for chunk in self.router.chat(messages, stream=True):
            yield chunk

    async def _get_ai_response(
        self,
        user_message: str,
        context: Optional[str] = None,
    ) -> str:
        """Get a complete AI response.

        Args:
            user_message: User message
            context: Optional additional context

        Returns:
            Complete response text
        """
        messages = [
            Message(role=Role.SYSTEM, content=self.get_system_prompt()),
        ]

        if context:
            messages.append(Message(role=Role.USER, content=context))
            messages.append(
                Message(
                    role=Role.ASSISTANT,
                    content="I understand the context. Please proceed with your request.",
                )
            )

        messages.append(Message(role=Role.USER, content=user_message))

        return await self.router.chat_complete(messages)


def get_architect(
    architecture: ArchitectureType | str,
    router: AIRouter,
) -> Architect:
    """Get an architect instance for the specified architecture.

    Args:
        architecture: Architecture type
        router: AI router

    Returns:
        Architect instance
    """
    from archai.architects.monolithic import MonolithicArchitect
    from archai.architects.microservices import MicroservicesArchitect
    from archai.architects.serverless import ServerlessArchitect
    from archai.architects.event_driven import EventDrivenArchitect
    from archai.architects.hexagonal import HexagonalArchitect

    if isinstance(architecture, str):
        architecture = ArchitectureType(architecture)

    architects = {
        ArchitectureType.MONOLITHIC: MonolithicArchitect,
        ArchitectureType.MICROSERVICES: MicroservicesArchitect,
        ArchitectureType.SERVERLESS: ServerlessArchitect,
        ArchitectureType.EVENT_DRIVEN: EventDrivenArchitect,
        ArchitectureType.HEXAGONAL: HexagonalArchitect,
    }

    architect_class = architects.get(architecture)
    if not architect_class:
        raise ValueError(f"Unknown architecture: {architecture}")

    return architect_class(router)


def list_architectures() -> list[dict[str, str]]:
    """List all available architectures.

    Returns:
        List of dicts with name and description
    """
    return [
        {
            "name": ArchitectureType.MONOLITHIC.value,
            "description": "Single deployable unit with layered structure",
        },
        {
            "name": ArchitectureType.MICROSERVICES.value,
            "description": "Independent services with API gateway",
        },
        {
            "name": ArchitectureType.SERVERLESS.value,
            "description": "Function-based, event-driven, cloud-native",
        },
        {
            "name": ArchitectureType.EVENT_DRIVEN.value,
            "description": "Message queues, pub/sub, async processing",
        },
        {
            "name": ArchitectureType.HEXAGONAL.value,
            "description": "Ports & adapters, dependency inversion",
        },
    ]
