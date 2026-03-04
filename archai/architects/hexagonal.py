"""Hexagonal (ports & adapters) architecture generator."""

import re
from pathlib import Path
from typing import AsyncIterator

from archai.ai.router import AIRouter
from archai.architects.base import Architect, ArchitectureType
from archai.utils.file_ops import FileOperations
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class HexagonalArchitect(Architect):
    """Generator for hexagonal (ports & adapters) architecture."""

    def __init__(self, router: AIRouter) -> None:
        super().__init__(router)

    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.HEXAGONAL

    @property
    def description(self) -> str:
        return "Ports & adapters architecture with dependency inversion and clean domain isolation"

    def get_template_structure(self, app_name: str) -> dict[str, str]:
        """Get hexagonal template structure.

        Args:
            app_name: Application name

        Returns:
            Dict mapping paths to descriptions
        """
        return {
            f"{app_name}/": "Project root",
            f"{app_name}/src/": "Source code",
            f"{app_name}/src/domain/": "Core domain (entities, value objects)",
            f"{app_name}/src/application/": "Application services (use cases)",
            f"{app_name}/src/ports/": "Port interfaces (input/output)",
            f"{app_name}/src/ports/input/": "Input ports (driving)",
            f"{app_name}/src/ports/output/": "Output ports (driven)",
            f"{app_name}/src/adapters/": "Adapter implementations",
            f"{app_name}/src/adapters/input/": "Input adapters (API, CLI)",
            f"{app_name}/src/adapters/output/": "Output adapters (DB, external)",
            f"{app_name}/tests/": "Test files",
            f"{app_name}/README.md": "Documentation",
        }

    async def generate(
        self,
        description: str,
        output_path: Path,
        language: str = "python",
    ) -> AsyncIterator[str]:
        """Generate a hexagonal architecture application.

        Args:
            description: Natural language description
            output_path: Where to create the project
            language: Target language

        Yields:
            Progress messages
        """
        yield f"Creating hexagonal architecture application at {output_path}...\n\n"

        yield "Identifying domain, ports, and adapters...\n\n"

        # Ask AI to generate the code
        prompt = f"""Generate a complete {language} hexagonal (ports & adapters) application based on this description:

{description}

Create a hexagonal architecture with:
1. Domain Layer - Core business logic (entities, value objects, domain services)
2. Application Layer - Use cases that orchestrate domain objects
3. Ports - Interfaces that define how the application interacts with the outside
   - Input ports (driving): How external actors interact with the app
   - Output ports (driven): How the app interacts with external services
4. Adapters - Implementations of ports
   - Input adapters: REST API, CLI, GraphQL
   - Output adapters: Database, external APIs, message queues

For each file, output in this exact format:
===FILE: <filepath>===
<file contents>
===END FILE===

Generate these components:
1. Domain:
   - src/domain/entities/<entity>.py (domain entities)
   - src/domain/value_objects.py (value objects)
   - src/domain/services.py (domain services)
   - src/domain/exceptions.py (domain exceptions)

2. Application:
   - src/application/use_cases/<use_case>.py (use case implementations)
   - src/application/services.py (application services)
   - src/application/dtos.py (data transfer objects)

3. Ports:
   - src/ports/input/<port>_port.py (input port interfaces)
   - src/ports/output/<port>_port.py (output port interfaces)

4. Adapters:
   - src/adapters/input/api/routes.py (REST API adapter)
   - src/adapters/input/api/main.py (API entry point)
   - src/adapters/output/persistence/<repo>_repository.py (DB adapter)
   - src/adapters/output/external/<service>_adapter.py (external service adapters)

5. Configuration:
   - src/config.py
   - src/container.py (dependency injection)
   - requirements.txt
   - README.md

Make sure:
- Domain has NO external dependencies
- All dependencies point inward (toward domain)
- Ports are abstract interfaces
- Adapters depend on ports, not the other way around
- Use dependency injection for wiring"""

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

        yield f"\nHexagonal architecture application created at {output_path}\n"

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
        await self._create_init_files(output_path, files_written)

        return files_written

    async def _create_init_files(
        self,
        output_path: Path,
        files_written: list[Path],
    ) -> None:
        """Create __init__.py files for Python packages.

        Args:
            output_path: Base output path
            files_written: List to append created files to
        """
        src_dir = output_path / "src"
        if not src_dir.exists():
            return

        # All directories that should be packages
        package_dirs = [
            src_dir,
            src_dir / "domain",
            src_dir / "domain" / "entities",
            src_dir / "application",
            src_dir / "application" / "use_cases",
            src_dir / "ports",
            src_dir / "ports" / "input",
            src_dir / "ports" / "output",
            src_dir / "adapters",
            src_dir / "adapters" / "input",
            src_dir / "adapters" / "input" / "api",
            src_dir / "adapters" / "output",
            src_dir / "adapters" / "output" / "persistence",
            src_dir / "adapters" / "output" / "external",
        ]

        for dir_path in package_dirs:
            if dir_path.exists():
                init_path = dir_path / "__init__.py"
                if not init_path.exists():
                    await FileOperations.write_file(init_path, '"""Package initialization."""\n')
                    files_written.append(init_path)

        # Tests directory
        tests_dir = output_path / "tests"
        if tests_dir.exists():
            init_path = tests_dir / "__init__.py"
            if not init_path.exists():
                await FileOperations.write_file(init_path, '"""Package initialization."""\n')
                files_written.append(init_path)
