"""Architecture converter for transforming between architectures."""

import re
from pathlib import Path
from typing import AsyncIterator, Optional

from archai.ai.base import Message, Role
from archai.ai.router import AIRouter
from archai.architects.base import ArchitectureType, get_architect
from archai.config.prompts import SYSTEM_PROMPT, get_transformation_prompt
from archai.utils.code_parser import CodeParser
from archai.utils.file_ops import FileOperations
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class ArchitectureConverter:
    """Converts projects between different architectures."""

    def __init__(self, router: AIRouter) -> None:
        """Initialize converter.

        Args:
            router: AI router for LLM interactions
        """
        self.router = router

    async def convert(
        self,
        source_path: Path,
        target_architecture: ArchitectureType | str,
        output_path: Optional[Path] = None,
    ) -> AsyncIterator[str]:
        """Convert a project to a different architecture.

        Args:
            source_path: Path to source project
            target_architecture: Target architecture
            output_path: Output path (defaults to source_path-<arch>)

        Yields:
            Progress messages and conversion output
        """
        if isinstance(target_architecture, str):
            target_architecture = ArchitectureType(target_architecture)

        if output_path is None:
            output_path = source_path.parent / f"{source_path.name}-{target_architecture.value}"

        yield f"Converting {source_path.name} to {target_architecture.value} architecture...\n\n"

        # Analyze source project structure (quick detection, no AI call)
        yield "Analyzing source project...\n"

        # Use quick structure parsing instead of full AI analysis
        parser = CodeParser()
        structure = parser.parse_project(source_path)

        # Quick architecture detection
        source_arch = self._quick_detect_architecture(structure)
        yield f"Detected architecture: {source_arch.value}\n"

        if source_arch == target_architecture:
            yield f"\nProject is already using {target_architecture.value} architecture.\n"
            return

        yield f"\nPlanning transformation: {source_arch.value} -> {target_architecture.value}\n\n"

        # Read source files
        yield "Reading source files...\n"
        source_files = await self._read_source_files(source_path)
        yield f"Found {len(source_files)} source files\n\n"

        # Build transformation prompt
        prompt = self._build_transformation_prompt(
            source_arch=source_arch,
            target_arch=target_architecture,
            source_files=source_files,
            analysis="",  # Skip AI analysis for faster transformation
        )

        yield "Generating transformed architecture...\n\n"
        yield "[thinking]Asking AI to transform codebase...[/thinking]\n"

        # Get AI transformation
        messages = [
            Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
            Message(role=Role.USER, content=prompt),
        ]

        full_response = ""
        chunk_count = 0
        async for chunk in self.router.chat(messages, stream=True):
            yield chunk
            full_response += chunk
            chunk_count += 1

        # Debug: show if we got any response
        if not full_response.strip():
            yield "\n\n⚠️ WARNING: AI returned empty response!\n"
            yield "Check your AI provider connection.\n"
        else:
            yield f"\n\n[Received {len(full_response)} chars in {chunk_count} chunks]\n"

        yield "\nWriting transformed files...\n"

        # Parse and write files
        files_written = await self._parse_and_write_files(full_response, output_path)

        yield f"\nCreated {len(files_written)} files:\n"
        for file_path in sorted(files_written):
            relative = file_path.relative_to(output_path)
            yield f"  {relative}\n"

        yield f"\n✅ Transformation complete: {output_path}\n"

        # Add run instructions
        yield "\n📋 To run:\n"
        yield f"  cd {output_path}\n"

        # Check for docker-compose (microservices)
        compose_file = output_path / "docker-compose.yml"
        compose_file2 = output_path / "docker-compose.yaml"
        if compose_file.exists() or compose_file2.exists():
            yield "  docker-compose up --build\n"
        else:
            # Check for requirements.txt
            req_file = output_path / "requirements.txt"
            if req_file.exists():
                yield "  pip install -r requirements.txt\n"

            # Find main entry point
            main_file = output_path / "main.py"
            src_main = output_path / "src" / "main.py"
            if main_file.exists():
                yield "  python main.py\n"
            elif src_main.exists():
                yield "  python src/main.py\n"
            else:
                # Check for services folder (microservices without docker)
                services_dir = output_path / "services"
                if services_dir.exists():
                    yield "\n  # Run each service:\n"
                    for svc in services_dir.iterdir():
                        if svc.is_dir() and (svc / "main.py").exists():
                            yield f"  cd services/{svc.name} && python main.py\n"

    def _quick_detect_architecture(self, structure) -> ArchitectureType:
        """Quickly detect architecture from structure without AI.

        Args:
            structure: Parsed project structure

        Returns:
            Detected architecture type
        """
        dir_names = set()
        for module in structure.modules:
            for parent in module.path.relative_to(structure.root).parents:
                dir_names.add(str(parent))

        # Check for microservices
        if "services" in dir_names:
            service_dirs = [d for d in dir_names if "service" in d.lower() and d != "services"]
            if len(service_dirs) > 1:
                return ArchitectureType.MICROSERVICES

        # Check for serverless
        if "functions" in dir_names or any("lambda" in str(m.path).lower() for m in structure.modules):
            return ArchitectureType.SERVERLESS

        # Check for hexagonal
        if "ports" in dir_names and "adapters" in dir_names:
            return ArchitectureType.HEXAGONAL

        # Check for event-driven
        if "events" in dir_names and ("handlers" in dir_names or "subscribers" in dir_names):
            return ArchitectureType.EVENT_DRIVEN

        # Default to monolithic
        return ArchitectureType.MONOLITHIC

    async def _read_source_files(self, source_path: Path) -> dict[str, str]:
        """Read all source files from a project.

        Args:
            source_path: Project root path

        Returns:
            Dict mapping relative paths to contents
        """
        files = {}
        project_files = await FileOperations.get_project_files(source_path)

        for file_path in project_files[:50]:  # Limit to 50 files
            try:
                content = await FileOperations.read_file(file_path)
                relative = str(file_path.relative_to(source_path))
                files[relative] = content
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

        return files

    def _build_transformation_prompt(
        self,
        source_arch: ArchitectureType,
        target_arch: ArchitectureType,
        source_files: dict[str, str],
        analysis: str,
    ) -> str:
        """Build the transformation prompt.

        Args:
            source_arch: Source architecture
            target_arch: Target architecture
            source_files: Source file contents
            analysis: Previous analysis

        Returns:
            Transformation prompt
        """
        base_prompt = get_transformation_prompt(
            source_arch.value, target_arch.value
        )

        # Build source files context
        files_context = []
        for path, content in source_files.items():
            # Truncate very long files
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            files_context.append(f"=== {path} ===\n{content}")

        files_str = "\n\n".join(files_context)

        return f"""{base_prompt}

## Source Files
{files_str}

## CRITICAL OUTPUT FORMAT INSTRUCTIONS
You MUST output each file using EXACTLY this format (no exceptions):

===FILE: path/to/file.py===
file contents here
===END FILE===

Example:
===FILE: main.py===
print("hello")
===END FILE===

===FILE: services/api.py===
from flask import Flask
app = Flask(__name__)
===END FILE===

## Task
Transform the above {source_arch.value} codebase to {target_arch.value} architecture.

Requirements:
1. Preserve all business logic
2. Update imports and references
3. Create appropriate structure for {target_arch.value}
4. Include configuration files (requirements.txt, docker-compose.yml if needed)

START OUTPUT NOW - Use ===FILE: path=== format for EVERY file:"""

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

        # Pattern 1: ===FILE: path=== format (handle optional spaces)
        pattern = r"===\s*FILE:\s*(.+?)\s*===\s*\n(.*?)===\s*END\s*FILE\s*==="
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        logger.info(f"Pattern 1 (===FILE:===): found {len(matches)} matches")

        # Pattern 2: markdown code blocks with filename
        if not matches:
            logger.debug("Trying markdown format")
            md_pattern = r"```(?:\w+)?(?::([^\n]+)|\n#\s*(?:filename:|file:)?\s*([^\n]+))\n(.*?)```"
            md_matches = re.findall(md_pattern, response, re.DOTALL)
            for path1, path2, content in md_matches:
                filepath = (path1 or path2).strip()
                if filepath:
                    matches.append((filepath, content))
            logger.info(f"Pattern 2 (markdown): found {len(matches)} matches")

        # Pattern 3: **filename** or ### filename followed by code block
        if not matches:
            logger.debug("Trying header + code block format")
            header_pattern = r"(?:\*\*|###?\s*)([^\*\n]+\.(?:py|txt|md|yaml|yml|json|dockerfile))\*?\*?\s*\n+```\w*\n(.*?)```"
            matches = re.findall(header_pattern, response, re.DOTALL | re.IGNORECASE)
            logger.info(f"Pattern 3 (header+code): found {len(matches)} matches")

        # Pattern 4: `filename` followed by code block
        if not matches:
            logger.debug("Trying backtick filename format")
            backtick_pattern = r"`([^`]+\.(?:py|txt|md|yaml|yml|json))`[:\s]*\n+```\w*\n(.*?)```"
            matches = re.findall(backtick_pattern, response, re.DOTALL)
            logger.info(f"Pattern 4 (backtick): found {len(matches)} matches")

        # Pattern 5: **N. `filepath`** followed by code block (numbered list format)
        if not matches:
            logger.debug("Trying numbered list format")
            numbered_pattern = r"\*\*\d+\.\s*`([^`]+)`\*\*\s*\n```\w*\n(.*?)```"
            matches = re.findall(numbered_pattern, response, re.DOTALL)
            logger.info(f"Pattern 5 (numbered): found {len(matches)} matches")

        # Pattern 6: **1. `package.json`** followed by ```lang ... ```
        # This matches: **1. `package.json`**\n```json\n{...}\n```
        if not matches:
            logger.debug("Trying **N. `filename`** format")
            bold_num_pattern = r"\*\*\d+\.\s*`([^`]+)`\*\*\s*\n```[a-z]*\n(.*?)```"
            matches = re.findall(bold_num_pattern, response, re.DOTALL)
            logger.info(f"Pattern 6 (bold numbered): found {len(matches)} matches")

        # Pattern 7: Flexible - find ALL code blocks and extract filename from context
        if not matches:
            logger.debug("Trying to extract all code blocks with filenames")
            # Match patterns like: **`src/index.js`**\n```js or **filename.py**\n```python
            all_blocks_pattern = r"\*\*`?([^`\*\n]+\.(?:py|js|ts|json|yaml|yml|md|env|txt))`?\*\*\s*\n```[a-z]*\n(.*?)```"
            matches = re.findall(all_blocks_pattern, response, re.DOTALL | re.IGNORECASE)
            logger.info(f"Pattern 7 (all blocks): found {len(matches)} matches")

        # Pattern 8: Last resort - find code blocks after any line containing a filepath
        if not matches:
            logger.debug("Last resort: extracting code blocks after filepath mentions")
            # Split by code blocks and look for filenames before each
            blocks = re.split(r'(```[a-z]*\n.*?```)', response, flags=re.DOTALL)
            for i in range(0, len(blocks) - 1, 2):
                context = blocks[i] if i < len(blocks) else ""
                code_block = blocks[i + 1] if i + 1 < len(blocks) else ""

                # Look for filepath in context before the code block
                filepath_match = re.search(r'[`\*]*([a-zA-Z0-9_/\-]+\.(?:py|js|ts|json|yaml|yml|md|env|txt))[`\*]*', context[-200:])
                if filepath_match and code_block:
                    filepath = filepath_match.group(1)
                    # Extract code content from the block
                    code_content = re.sub(r'^```[a-z]*\n', '', code_block)
                    code_content = re.sub(r'\n```$', '', code_content)
                    matches.append((filepath, code_content))
            logger.info(f"Pattern 8 (last resort): found {len(matches)} matches")

        if not matches:
            logger.error("No file patterns matched in AI response!")
            print("\n⚠️ AI response format not recognized.")
            print("Response preview:")
            print(response[:500])
            print("...")

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        for filepath, content in matches:
            filepath = filepath.strip().strip("'\"")
            content = content.strip()

            # Normalize path separators for Windows
            filepath = filepath.replace("\\", "/")

            full_path = output_path / filepath

            try:
                # Ensure parent directory exists
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Try async write, fallback to sync
                try:
                    await FileOperations.write_file(full_path, content)
                except Exception as async_err:
                    logger.warning(f"Async write failed, trying sync: {async_err}")
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)

                files_written.append(full_path)
                logger.info(f"Wrote file: {full_path}")
            except Exception as e:
                logger.error(f"Error writing {full_path}: {e}")
                print(f"ERROR writing file {full_path}: {e}")

        # Create __init__.py files for Python packages
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
        # Find all directories containing .py files
        py_dirs: set[Path] = set()
        for file_path in files_written:
            if file_path.suffix == ".py":
                py_dirs.add(file_path.parent)
                # Also add parent directories
                for parent in file_path.relative_to(output_path).parents:
                    if parent != Path("."):
                        py_dirs.add(output_path / parent)

        for dir_path in py_dirs:
            if dir_path.exists():
                init_path = dir_path / "__init__.py"
                if not init_path.exists():
                    await FileOperations.write_file(
                        init_path, '"""Package initialization."""\n'
                    )
                    files_written.append(init_path)
