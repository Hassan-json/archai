"""Base transformer class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator

from archai.ai.router import AIRouter


class Transformer(ABC):
    """Base class for code transformers."""

    def __init__(self, router: AIRouter) -> None:
        """Initialize transformer.

        Args:
            router: AI router for LLM interactions
        """
        self.router = router

    @abstractmethod
    async def transform(
        self,
        source_path: Path,
        target_path: Path,
    ) -> AsyncIterator[str]:
        """Transform code from source to target.

        Args:
            source_path: Source code path
            target_path: Target output path

        Yields:
            Progress messages
        """
        pass
