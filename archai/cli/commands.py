"""Built-in commands for the Archai CLI."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from archai.architects.base import ArchitectureType, get_architect, list_architectures
from archai.config.settings import get_settings
from archai.transformers.analyzer import CodeAnalyzer
from archai.transformers.converter import ArchitectureConverter

if TYPE_CHECKING:
    from archai.cli.app import ArchiApp


@dataclass
class CommandResult:
    """Result of command execution."""

    success: bool
    message: str = ""
    should_exit: bool = False


class CommandHandler:
    """Handles built-in commands."""

    def __init__(self, app: "ArchiApp") -> None:
        """Initialize command handler.

        Args:
            app: Main application instance
        """
        self.app = app
        self.commands: dict[str, Callable] = {
            "/help": self.cmd_help,
            "/config": self.cmd_config,
            "/clear": self.cmd_clear,
            "/providers": self.cmd_providers,
            "/architectures": self.cmd_architectures,
            "/analyze": self.cmd_analyze,
            "/exit": self.cmd_exit,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
        }

    def is_command(self, text: str) -> bool:
        """Check if text is a command.

        Args:
            text: Input text

        Returns:
            True if text is a command
        """
        text = text.strip().lower()
        return text.startswith("/") or text in ["exit", "quit"]

    async def execute(self, text: str) -> CommandResult:
        """Execute a command.

        Args:
            text: Command text

        Returns:
            CommandResult
        """
        parts = text.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in self.commands:
            return await self.commands[cmd](args)

        return CommandResult(
            success=False,
            message=f"Unknown command: {cmd}. Type /help for available commands.",
        )

    async def cmd_help(self, args: str) -> CommandResult:
        """Show help message.

        Args:
            args: Command arguments (unused)

        Returns:
            CommandResult
        """
        self.app.renderer.print_help()
        return CommandResult(success=True)

    async def cmd_config(self, args: str) -> CommandResult:
        """View or modify configuration.

        Args:
            args: "key value" to set, or empty to view

        Returns:
            CommandResult
        """
        settings = get_settings()

        if not args:
            config = {
                "default_provider": settings.default_provider,
                "default_language": settings.default_language,
                "theme": settings.theme,
            }
            for name, provider in settings.providers.items():
                config[f"providers.{name}.model"] = provider.model
            self.app.renderer.print_config(config)
            return CommandResult(success=True)

        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return CommandResult(
                success=False,
                message="Usage: /config <key> <value>",
            )

        key, value = parts

        if key == "provider":
            try:
                self.app.router.set_provider(value)
                settings.save()
                return CommandResult(
                    success=True,
                    message=f"Switched to provider: {value}",
                )
            except ValueError as e:
                return CommandResult(success=False, message=str(e))

        elif key == "model":
            self.app.router.set_model(value)
            settings.save()
            return CommandResult(
                success=True,
                message=f"Set model to: {value}",
            )

        elif key == "language":
            settings.default_language = value
            settings.save()
            return CommandResult(
                success=True,
                message=f"Set default language to: {value}",
            )

        else:
            return CommandResult(
                success=False,
                message=f"Unknown config key: {key}",
            )

    async def cmd_clear(self, args: str) -> CommandResult:
        """Clear the screen.

        Args:
            args: Command arguments (unused)

        Returns:
            CommandResult
        """
        self.app.renderer.clear()
        return CommandResult(success=True)

    async def cmd_providers(self, args: str) -> CommandResult:
        """List available providers.

        Args:
            args: Command arguments (unused)

        Returns:
            CommandResult
        """
        providers = self.app.router.get_available_providers()
        current = self.app.router.current_provider
        self.app.renderer.print_providers(providers, current)
        return CommandResult(success=True)

    async def cmd_architectures(self, args: str) -> CommandResult:
        """List supported architectures.

        Args:
            args: Command arguments (unused)

        Returns:
            CommandResult
        """
        self.app.renderer.print_architectures()
        return CommandResult(success=True)

    async def cmd_analyze(self, args: str) -> CommandResult:
        """Analyze an existing project.

        Args:
            args: Path to project

        Returns:
            CommandResult
        """
        if not args:
            return CommandResult(
                success=False,
                message="Usage: /analyze <path>",
            )

        path = Path(args).expanduser().resolve()
        analyzer = CodeAnalyzer(self.app.router)

        async for chunk in analyzer.analyze(path):
            self.app.renderer.print_streaming(chunk)

        self.app.renderer.print("")  # Newline
        return CommandResult(success=True)

    async def cmd_exit(self, args: str) -> CommandResult:
        """Exit the application.

        Args:
            args: Command arguments (unused)

        Returns:
            CommandResult with should_exit=True
        """
        return CommandResult(success=True, should_exit=True)


class RequestParser:
    """Parses natural language requests into actions."""

    # Patterns for different request types
    # Pattern with "at <path>" - capture architecture, description, and path
    CREATE_PATTERNS = [
        # "create a monolithic calculator app at ./path"
        r"(?:create|generate|build|make)\s+(?:a\s+)?(\w+)\s+(.+?)\s+(?:at|in|to)\s+(\S+)$",
        # "create a monolithic app called myapp"
        r"(?:create|generate|build|make)\s+(?:a\s+)?(\w+)\s+(?:app(?:lication)?|project)\s+called\s+(\S+)",
        # "create a monolithic app" (no path)
        r"(?:create|generate|build|make)\s+(?:a\s+)?(\w+)\s+(.+?)$",
    ]

    TRANSFORM_PATTERNS = [
        r"(?:rewrite|convert|transform|change)\s+(\S+)\s+(?:to|as|into)\s+(\w+)",
        r"(?:turn|make)\s+(\S+)\s+(?:into\s+)?(?:a\s+)?(\w+)",
    ]

    ANALYZE_PATTERNS = [
        r"analyze\s+(\S+)",
        r"(?:look at|examine|inspect)\s+(\S+)",
    ]

    def __init__(self) -> None:
        """Initialize parser."""
        self.architectures = {arch["name"] for arch in list_architectures()}

    def parse(self, text: str) -> Optional[dict]:
        """Parse a request into an action.

        Args:
            text: User input text

        Returns:
            Dict with action details or None
        """
        text = text.strip().lower()

        # Check for create/generate patterns
        for i, pattern in enumerate(self.CREATE_PATTERNS):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                arch = match.group(1)

                # Pattern 0: "create arch description at path" -> (arch, desc, path)
                # Pattern 1: "create arch app called name" -> (arch, name)
                # Pattern 2: "create arch description" -> (arch, desc)
                if i == 0 and match.lastindex >= 3:
                    # Has path
                    desc = match.group(2)
                    path = match.group(3)
                    name = None
                elif i == 1 and match.lastindex >= 2:
                    # Has name from "called"
                    name = match.group(2)
                    path = None
                    desc = f"{arch} app"
                else:
                    # Just description
                    desc = match.group(2) if match.lastindex >= 2 else f"{arch} app"
                    name = None
                    path = None

                # Find architecture type
                arch_type = self._match_architecture(arch)
                if arch_type:
                    return {
                        "action": "create",
                        "architecture": arch_type,
                        "name": name,
                        "path": path,
                        "description": desc.strip() if desc else text,
                    }

        # Check for transform patterns
        for pattern in self.TRANSFORM_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                source = match.group(1)
                target = match.group(2)

                arch_type = self._match_architecture(target)
                if arch_type:
                    return {
                        "action": "transform",
                        "source_path": source,
                        "target_architecture": arch_type,
                        "description": text,
                    }

        # Check for analyze patterns
        for pattern in self.ANALYZE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "action": "analyze",
                    "path": match.group(1),
                }

        # No pattern matched - treat as general AI request
        return {
            "action": "ai_chat",
            "message": text,
        }

    def _match_architecture(self, text: str) -> Optional[ArchitectureType]:
        """Match text to an architecture type.

        Args:
            text: Architecture name text

        Returns:
            ArchitectureType or None
        """
        text = text.lower().strip()

        # Direct matches
        for arch in ArchitectureType:
            if arch.value == text:
                return arch

        # Partial matches
        arch_mapping = {
            "mono": ArchitectureType.MONOLITHIC,
            "monolith": ArchitectureType.MONOLITHIC,
            "micro": ArchitectureType.MICROSERVICES,
            "microservice": ArchitectureType.MICROSERVICES,
            "server": ArchitectureType.SERVERLESS,
            "lambda": ArchitectureType.SERVERLESS,
            "event": ArchitectureType.EVENT_DRIVEN,
            "events": ArchitectureType.EVENT_DRIVEN,
            "hex": ArchitectureType.HEXAGONAL,
            "ports": ArchitectureType.HEXAGONAL,
            "clean": ArchitectureType.HEXAGONAL,
        }

        for key, arch in arch_mapping.items():
            if text.startswith(key):
                return arch

        return None
