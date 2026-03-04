"""Rich-based output rendering for the CLI."""

from contextlib import contextmanager
from typing import Optional, Generator

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from archai.architects.base import list_architectures


# Custom theme
ARCHAI_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "prompt": "bold blue",
        "muted": "dim",
        "highlight": "bold magenta",
    }
)


class Renderer:
    """Handles all Rich-based output rendering."""

    def __init__(self) -> None:
        """Initialize renderer."""
        self.console = Console(theme=ARCHAI_THEME)
        self._current_live: Optional[Live] = None

    def print(self, message: str, style: Optional[str] = None) -> None:
        """Print a message.

        Args:
            message: Message to print
            style: Optional Rich style
        """
        self.console.print(message, style=style)

    def print_info(self, message: str) -> None:
        """Print an info message.

        Args:
            message: Message to print
        """
        self.console.print(message, style="info")

    def print_success(self, message: str) -> None:
        """Print a success message.

        Args:
            message: Message to print
        """
        self.console.print(f"[success]{message}[/success]")

    def print_warning(self, message: str) -> None:
        """Print a warning message.

        Args:
            message: Message to print
        """
        self.console.print(f"[warning]Warning:[/warning] {message}")

    def print_error(self, message: str) -> None:
        """Print an error message.

        Args:
            message: Message to print
        """
        self.console.print(f"[error]Error:[/error] {message}")

    def print_banner(self, version: str, provider: str, model: str) -> None:
        """Print the application banner.

        Args:
            version: Application version
            provider: Current AI provider
            model: Current model
        """
        banner = Text()
        banner.append("Archai", style="bold magenta")
        banner.append(f" v{version}", style="muted")
        banner.append(" - AI Architecture Assistant\n", style="")
        banner.append(f"Provider: ", style="muted")
        banner.append(f"{provider}", style="info")
        banner.append(f" ({model})", style="muted")

        self.console.print(Panel(banner, border_style="blue"))
        self.console.print()

    def print_help(self) -> None:
        """Print help message."""
        table = Table(title="Commands", border_style="blue")
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        commands = [
            ("/help", "Show this help message"),
            ("/config [key] [value]", "View or modify configuration"),
            ("/clear", "Clear the screen"),
            ("/providers", "List available AI providers"),
            ("/architectures", "List supported architectures"),
            ("/analyze <path>", "Analyze an existing project"),
            ("exit, /exit, quit", "Exit the application"),
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        self.console.print(table)
        self.console.print()

        self.console.print("[bold]Examples:[/bold]")
        self.console.print("  create a monolithic todo app at ./my-app", style="muted")
        self.console.print("  rewrite ./my-app as microservices", style="muted")
        self.console.print("  build a serverless API at ./api", style="muted")
        self.console.print()

    def print_providers(self, providers: list[str], current: str) -> None:
        """Print available providers.

        Args:
            providers: List of provider names
            current: Currently selected provider
        """
        table = Table(title="AI Providers", border_style="blue")
        table.add_column("Provider", style="cyan")
        table.add_column("Status")

        for provider in providers:
            status = "[success](current)[/success]" if provider == current else ""
            table.add_row(provider, status)

        self.console.print(table)
        self.console.print()

    def print_architectures(self) -> None:
        """Print supported architectures."""
        table = Table(title="Supported Architectures", border_style="blue")
        table.add_column("Architecture", style="cyan")
        table.add_column("Description")

        for arch in list_architectures():
            table.add_row(arch["name"], arch["description"])

        self.console.print(table)
        self.console.print()

    def print_config(self, config: dict) -> None:
        """Print current configuration.

        Args:
            config: Configuration dictionary
        """
        table = Table(title="Configuration", border_style="blue")
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        for key, value in config.items():
            if isinstance(value, dict):
                value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            table.add_row(key, str(value))

        self.console.print(table)
        self.console.print()

    def print_markdown(self, content: str) -> None:
        """Print markdown content.

        Args:
            content: Markdown content
        """
        md = Markdown(content)
        self.console.print(md)

    def print_code(self, code: str, language: str = "python") -> None:
        """Print syntax-highlighted code.

        Args:
            code: Code content
            language: Programming language
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def print_streaming(self, text: str, end: str = "") -> None:
        """Print streaming text without newline.

        Args:
            text: Text to print
            end: End character
        """
        # Handle special thinking markers
        if text.startswith("[thinking]") and text.endswith("[/thinking]\n"):
            # Extract message and show as status
            message = text[10:-13]  # Remove markers
            self.console.print(f"[cyan]{message}[/cyan]")
            return

        self.console.print(text, end=end)

    def create_progress(self, description: str = "Working...") -> Progress:
        """Create a progress indicator.

        Args:
            description: Progress description

        Returns:
            Progress instance
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )

    def clear(self) -> None:
        """Clear the screen."""
        self.console.clear()

    @contextmanager
    def status(self, message: str = "Thinking...") -> Generator[None, None, None]:
        """Show a spinner with status message.

        Args:
            message: Status message to display

        Yields:
            Nothing, just provides context
        """
        with self.console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
            yield

    def print_status(self, message: str) -> None:
        """Print a status message with spinner icon.

        Args:
            message: Status message
        """
        self.console.print(f"[cyan]> {message}[/cyan]")

    def print_directory_tree(self, path: str, files: list[str]) -> None:
        """Print a directory tree.

        Args:
            path: Root path
            files: List of file paths
        """
        self.console.print(f"[bold]{path}/[/bold]")

        # Sort and organize files
        for file in sorted(files):
            # Determine indentation based on depth
            depth = file.count("/")
            indent = "  " * depth

            # File or directory icon
            if file.endswith("/"):
                icon = ""
                style = "bold blue"
            else:
                icon = ""
                style = ""

            self.console.print(f"{indent}{icon} {file.split('/')[-1]}", style=style)
