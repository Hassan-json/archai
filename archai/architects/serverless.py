"""Serverless architecture generator."""

import re
from pathlib import Path
from typing import AsyncIterator

from archai.ai.router import AIRouter
from archai.architects.base import Architect, ArchitectureType
from archai.utils.file_ops import FileOperations
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class ServerlessArchitect(Architect):
    """Generator for serverless architecture."""

    def __init__(self, router: AIRouter) -> None:
        super().__init__(router)

    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.SERVERLESS

    @property
    def description(self) -> str:
        return "Function-based architecture with event triggers, cloud-native (AWS Lambda style)"

    def get_template_structure(self, app_name: str) -> dict[str, str]:
        """Get serverless template structure.

        Args:
            app_name: Application name

        Returns:
            Dict mapping paths to descriptions
        """
        return {
            f"{app_name}/": "Project root",
            f"{app_name}/functions/": "Lambda functions",
            f"{app_name}/shared/": "Shared utilities",
            f"{app_name}/events/": "Event definitions",
            f"{app_name}/serverless.yml": "Serverless Framework config",
            f"{app_name}/requirements.txt": "Dependencies",
            f"{app_name}/README.md": "Documentation",
        }

    async def generate(
        self,
        description: str,
        output_path: Path,
        language: str = "python",
    ) -> AsyncIterator[str]:
        """Generate a serverless application.

        Args:
            description: Natural language description
            output_path: Where to create the project
            language: Target language

        Yields:
            Progress messages
        """
        yield f"Creating serverless application at {output_path}...\n\n"

        yield "Identifying functions and event triggers...\n\n"

        # Ask AI to generate the code
        prompt = f"""Generate a complete {language} serverless application based on this description:

{description}

Create a serverless architecture with:
1. Individual Lambda functions for each capability
2. API Gateway integration for HTTP endpoints
3. Event triggers (HTTP, schedule, queue)
4. Shared utilities

For each file, output in this exact format:
===FILE: <filepath>===
<file contents>
===END FILE===

Generate these components:
1. Lambda functions (one per capability):
   - functions/<function_name>/handler.py
   - functions/<function_name>/requirements.txt

2. Shared code:
   - shared/utils.py
   - shared/models.py
   - shared/validators.py

3. Configuration:
   - serverless.yml (Serverless Framework configuration)
   - requirements.txt (root dependencies)

4. Documentation:
   - README.md

Make sure:
- Each function is stateless and independent
- Functions handle their own error cases
- Use environment variables for configuration
- Include proper IAM permissions in serverless.yml"""

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

        yield f"\nServerless application created at {output_path}\n"
        yield "\nTo deploy: serverless deploy\n"

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

        # Create __init__.py files
        for subdir in ["functions", "shared"]:
            dir_path = output_path / subdir
            if dir_path.exists():
                init_path = dir_path / "__init__.py"
                if not init_path.exists():
                    await FileOperations.write_file(init_path, '"""Package initialization."""\n')
                    files_written.append(init_path)

                # Also for function subdirectories
                if subdir == "functions":
                    for func_dir in dir_path.iterdir():
                        if func_dir.is_dir():
                            init_path = func_dir / "__init__.py"
                            if not init_path.exists():
                                await FileOperations.write_file(init_path, '"""Package initialization."""\n')
                                files_written.append(init_path)

        return files_written
