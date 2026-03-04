"""Microservices architecture generator."""

import re
from pathlib import Path
from typing import AsyncIterator

from archai.ai.router import AIRouter
from archai.architects.base import Architect, ArchitectureType
from archai.utils.file_ops import FileOperations
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class MicroservicesArchitect(Architect):
    """Generator for microservices architecture."""

    def __init__(self, router: AIRouter) -> None:
        super().__init__(router)

    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.MICROSERVICES

    @property
    def description(self) -> str:
        return "Independent services with API gateway, service discovery, and containerization"

    def get_template_structure(self, app_name: str) -> dict[str, str]:
        """Get microservices template structure.

        Args:
            app_name: Application name

        Returns:
            Dict mapping paths to descriptions
        """
        return {
            f"{app_name}/": "Project root",
            f"{app_name}/services/": "Microservices",
            f"{app_name}/services/api-gateway/": "API Gateway service",
            f"{app_name}/services/api-gateway/src/": "Gateway source",
            f"{app_name}/shared/": "Shared utilities and models",
            f"{app_name}/docker-compose.yml": "Container orchestration",
            f"{app_name}/README.md": "Project documentation",
        }

    async def generate(
        self,
        description: str,
        output_path: Path,
        language: str = "python",
    ) -> AsyncIterator[str]:
        """Generate a microservices application.

        Args:
            description: Natural language description
            output_path: Where to create the project
            language: Target language

        Yields:
            Progress messages
        """
        yield f"Generating microservices for: {description} at {output_path}...\n\n"
        yield "[thinking]Asking AI to design services...[/thinking]\n"

        # Ask AI to generate the code
        prompt = f"""Output a complete {language} microservices application: {description}

MICROSERVICES means: separate, independent services that communicate via HTTP/REST.

Output each file using EXACTLY this format:

===FILE: services/calculator-service/main.py===
# code here
===END FILE===

===FILE: docker-compose.yml===
# code here
===END FILE===

Create:
1. 2-3 independent services in services/<name>/ folders
2. Each service has: main.py, requirements.txt, Dockerfile
3. docker-compose.yml to run all services
4. README.md with run instructions

Keep it simple. Each service should be a small Flask/FastAPI app.

START OUTPUT NOW with ===FILE: markers:"""

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

        yield f"\n✅ Microservices application created at {output_path}\n"

        # Add run instructions
        yield "\n📋 To run:\n"
        yield f"  cd {output_path}\n"

        # Check for docker-compose
        compose_file = output_path / "docker-compose.yml"
        compose_file2 = output_path / "docker-compose.yaml"
        if compose_file.exists() or compose_file2.exists():
            yield "  docker-compose up --build\n"
        else:
            # Individual services
            services_dir = output_path / "services"
            if services_dir.exists():
                yield "\n  # Run each service:\n"
                for svc in services_dir.iterdir():
                    if svc.is_dir():
                        yield f"  cd services/{svc.name} && pip install -r requirements.txt && python src/main.py\n"

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

        # Create __init__.py files for Python packages
        for service_dir in (output_path / "services").iterdir() if (output_path / "services").exists() else []:
            if service_dir.is_dir():
                src_dir = service_dir / "src"
                if src_dir.exists():
                    init_path = src_dir / "__init__.py"
                    if not init_path.exists():
                        await FileOperations.write_file(init_path, '"""Package initialization."""\n')
                        files_written.append(init_path)

        return files_written
