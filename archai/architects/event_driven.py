"""Event-driven architecture generator."""

import re
from pathlib import Path
from typing import AsyncIterator

from archai.ai.router import AIRouter
from archai.architects.base import Architect, ArchitectureType
from archai.utils.file_ops import FileOperations
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class EventDrivenArchitect(Architect):
    """Generator for event-driven architecture."""

    def __init__(self, router: AIRouter) -> None:
        super().__init__(router)

    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.EVENT_DRIVEN

    @property
    def description(self) -> str:
        return "Message queues, pub/sub patterns, async processing with event sourcing"

    def get_template_structure(self, app_name: str) -> dict[str, str]:
        """Get event-driven template structure.

        Args:
            app_name: Application name

        Returns:
            Dict mapping paths to descriptions
        """
        return {
            f"{app_name}/": "Project root",
            f"{app_name}/src/": "Source code",
            f"{app_name}/src/events/": "Event definitions",
            f"{app_name}/src/handlers/": "Event handlers",
            f"{app_name}/src/publishers/": "Event publishers",
            f"{app_name}/src/subscribers/": "Event subscribers",
            f"{app_name}/src/domain/": "Domain models",
            f"{app_name}/src/infrastructure/": "Message broker integration",
            f"{app_name}/docker-compose.yml": "Container setup with broker",
            f"{app_name}/README.md": "Documentation",
        }

    async def generate(
        self,
        description: str,
        output_path: Path,
        language: str = "python",
    ) -> AsyncIterator[str]:
        """Generate an event-driven application.

        Args:
            description: Natural language description
            output_path: Where to create the project
            language: Target language

        Yields:
            Progress messages
        """
        yield f"Creating event-driven application at {output_path}...\n\n"

        yield "Identifying events and handlers...\n\n"

        # Ask AI to generate the code
        prompt = f"""Generate a complete {language} event-driven application based on this description:

{description}

Create an event-driven architecture with:
1. Event definitions (schemas/contracts)
2. Event publishers
3. Event handlers/subscribers
4. Message broker integration (e.g., RabbitMQ, Redis)
5. Domain models

For each file, output in this exact format:
===FILE: <filepath>===
<file contents>
===END FILE===

Generate these components:
1. Events:
   - src/events/base.py (base event class)
   - src/events/<domain>_events.py (domain-specific events)

2. Publishers:
   - src/publishers/base.py (base publisher)
   - src/publishers/<domain>_publisher.py

3. Handlers/Subscribers:
   - src/handlers/base.py (base handler)
   - src/handlers/<domain>_handler.py

4. Infrastructure:
   - src/infrastructure/message_broker.py (broker connection)
   - src/infrastructure/event_bus.py (event routing)

5. Domain:
   - src/domain/models.py
   - src/domain/services.py

6. Entry point:
   - src/main.py (starts consumers)
   - src/api.py (optional HTTP API for publishing events)

7. Configuration:
   - src/config.py
   - requirements.txt
   - docker-compose.yml (with message broker)
   - README.md

Make sure:
- Events are immutable and serializable
- Handlers are idempotent
- Include retry logic and dead letter queues
- Use async/await for non-blocking operations"""

        full_response = ""
        async for chunk in self._ask_ai(prompt):
            yield chunk
            full_response += chunk

        yield "\n\nWriting files...\n"

        # Parse and write files
        files_written = await self._parse_and_write_files(full_response, output_path)

        yield f"\nCreated {len(files_written)} files:\n"
        for file_path in sorted(files_written):
            relative = file_path.relative_to(output_path)
            yield f"  {relative}\n"

        yield f"\nEvent-driven application created at {output_path}\n"
        yield "\nTo run: docker-compose up -d && python src/main.py\n"

    async def _parse_and_write_files(
        self,
        response: str,
        output_path: Path,
    ) -> list[Path]:
        """Parse AI response and write files.

        Args:
            response: AI response with file contents
            output_path: Base output path

        Returns:
            List of written file paths
        """
        files_written = []

        # Pattern to match file blocks
        pattern = r"===FILE:\s*(.+?)\s*===\n(.*?)===END FILE==="
        matches = re.findall(pattern, response, re.DOTALL)

        for filepath, content in matches:
            filepath = filepath.strip()
            content = content.strip()

            full_path = output_path / filepath

            try:
                await FileOperations.write_file(full_path, content)
                files_written.append(full_path)
                logger.debug(f"Wrote file: {full_path}")
            except Exception as e:
                logger.error(f"Error writing {full_path}: {e}")

        # Create __init__.py files for all subdirectories
        src_dir = output_path / "src"
        if src_dir.exists():
            for subdir in ["events", "handlers", "publishers", "subscribers", "domain", "infrastructure"]:
                dir_path = src_dir / subdir
                if dir_path.exists():
                    init_path = dir_path / "__init__.py"
                    if not init_path.exists():
                        await FileOperations.write_file(init_path, '"""Package initialization."""\n')
                        files_written.append(init_path)

            # Root src __init__.py
            init_path = src_dir / "__init__.py"
            if not init_path.exists():
                await FileOperations.write_file(init_path, '"""Package initialization."""\n')
                files_written.append(init_path)

        return files_written
