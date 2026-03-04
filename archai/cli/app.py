"""Main REPL application for Archai."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from archai import __version__
from archai.ai.base import Message, Role
from archai.ai.router import AIRouter
from archai.architects.base import get_architect
from archai.cli.commands import CommandHandler, RequestParser
from archai.cli.renderer import Renderer
from archai.config.prompts import SYSTEM_PROMPT
from archai.config.settings import Settings, get_settings
from archai.transformers.analyzer import CodeAnalyzer
from archai.transformers.converter import ArchitectureConverter
from archai.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


# Prompt toolkit style
PROMPT_STYLE = Style.from_dict(
    {
        "prompt": "ansicyan bold",
        "": "",
    }
)


class ArchiApp:
    """Main Archai application."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize application.

        Args:
            settings: Optional settings instance
        """
        self.settings = settings or get_settings()
        self.router = AIRouter(self.settings)
        self.renderer = Renderer()
        self.command_handler = CommandHandler(self)
        self.request_parser = RequestParser()
        self.conversation: list[Message] = []

        # Set up prompt session with history
        history_file = self.settings.config_dir / "history"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        self.session: PromptSession = PromptSession(
            history=FileHistory(str(history_file)),
            style=PROMPT_STYLE,
        )

    def _reset_conversation(self) -> None:
        """Reset conversation history."""
        self.conversation = [
            Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
        ]

    async def _handle_create(self, parsed: dict) -> None:
        """Handle create/generate request.

        Args:
            parsed: Parsed request dict
        """
        architecture = parsed["architecture"]
        description = parsed["description"]

        # Determine output path
        if parsed.get("path"):
            output_path = Path(parsed["path"]).expanduser().resolve()
        elif parsed.get("name"):
            output_path = Path.cwd() / parsed["name"]
        else:
            output_path = Path.cwd() / f"new-{architecture.value}-app"

        architect = get_architect(architecture, self.router)

        async for chunk in architect.generate(
            description=description,
            output_path=output_path,
            language=self.settings.default_language,
        ):
            self.renderer.print_streaming(chunk)

        self.renderer.print("")  # Final newline

    async def _handle_transform(self, parsed: dict) -> None:
        """Handle transform/convert request.

        Args:
            parsed: Parsed request dict
        """
        source_path = Path(parsed["source_path"]).expanduser().resolve()
        target_arch = parsed["target_architecture"]

        converter = ArchitectureConverter(self.router)

        async for chunk in converter.convert(
            source_path=source_path,
            target_architecture=target_arch,
        ):
            self.renderer.print_streaming(chunk)

        self.renderer.print("")  # Final newline

    async def _handle_analyze(self, parsed: dict) -> None:
        """Handle analyze request.

        Args:
            parsed: Parsed request dict
        """
        path = Path(parsed["path"]).expanduser().resolve()
        analyzer = CodeAnalyzer(self.router)

        async for chunk in analyzer.analyze(path):
            self.renderer.print_streaming(chunk)

        self.renderer.print("")  # Final newline

    async def _handle_ai_chat(self, parsed: dict) -> None:
        """Handle general AI chat.

        Args:
            parsed: Parsed request dict
        """
        user_message = parsed["message"]

        # Add user message to conversation
        self.conversation.append(Message(role=Role.USER, content=user_message))

        # Get AI response
        response_text = ""
        async for chunk in self.router.chat(self.conversation, stream=True):
            self.renderer.print_streaming(chunk)
            response_text += chunk

        self.renderer.print("")  # Final newline

        # Add assistant response to conversation
        self.conversation.append(Message(role=Role.ASSISTANT, content=response_text))

    async def process_input(self, text: str) -> bool:
        """Process user input.

        Args:
            text: User input

        Returns:
            True if should continue, False to exit
        """
        text = text.strip()

        if not text:
            return True

        # Check for commands
        if self.command_handler.is_command(text):
            result = await self.command_handler.execute(text)

            if result.message:
                if result.success:
                    self.renderer.print_success(result.message)
                else:
                    self.renderer.print_error(result.message)

            return not result.should_exit

        # Parse and handle request
        try:
            parsed = self.request_parser.parse(text)

            if parsed["action"] == "create":
                await self._handle_create(parsed)
            elif parsed["action"] == "transform":
                await self._handle_transform(parsed)
            elif parsed["action"] == "analyze":
                await self._handle_analyze(parsed)
            elif parsed["action"] == "ai_chat":
                await self._handle_ai_chat(parsed)

        except Exception as e:
            logger.exception("Error processing request")
            self.renderer.print_error(f"Error: {e}")

        return True

    async def run(self) -> None:
        """Run the main REPL loop."""
        self._reset_conversation()

        # Print banner
        self.renderer.print_banner(
            version=__version__,
            provider=self.router.current_provider,
            model=self.router.current_model,
        )

        while True:
            try:
                text = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.session.prompt("> "),
                )

                should_continue = await self.process_input(text)
                if not should_continue:
                    self.renderer.print("Goodbye!", style="muted")
                    break

            except KeyboardInterrupt:
                self.renderer.print("\nUse 'exit' or '/exit' to quit.", style="muted")
                continue

            except EOFError:
                self.renderer.print("\nGoodbye!", style="muted")
                break


@click.command()
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["anthropic", "claude-cli", "ollama", "openai", "litellm", "gemini"]),
    help="AI provider to use",
)
@click.option(
    "--model",
    "-m",
    help="Model to use (e.g., 'gpt-4', 'ollama/llama3.2', 'anthropic/claude-3-sonnet')",
)
@click.option(
    "--base-url",
    "-u",
    help="Custom API endpoint URL (e.g., 'http://localhost:8000/v1')",
)
@click.option(
    "--api-key",
    "-k",
    help="API key for the provider",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to config file",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging",
)
@click.version_option(version=__version__)
def main(
    provider: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
    api_key: Optional[str],
    config: Optional[str],
    debug: bool,
) -> None:
    """Archai - AI Architecture Assistant.

    An interactive CLI tool for generating and transforming software architectures.

    \b
    Examples:
      archai                                      # Use default config
      archai -p ollama -m llama3.2                # Use Ollama with llama3.2
      archai -p openai -m gpt-4 -k $OPENAI_KEY    # Use OpenAI with API key
      archai -p litellm -m openai/model -u http://localhost:8000/v1  # Custom endpoint
    """
    # Set up logging
    import logging

    setup_logging(level=logging.DEBUG if debug else logging.WARNING)

    # Load settings
    config_path = Path(config) if config else None
    settings = Settings.load(config_path)

    # Apply CLI overrides
    if provider:
        settings.set_provider(provider)

    current_provider = provider or settings.default_provider

    if model:
        settings.set_model(current_provider, model)

    if base_url:
        settings.providers[current_provider].base_url = base_url

    if api_key:
        settings.providers[current_provider].api_key = api_key

    # Create and run app
    app = ArchiApp(settings)

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
