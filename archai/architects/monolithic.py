"""Monolithic architecture generator."""

import re
from pathlib import Path
from typing import AsyncIterator

from archai.ai.router import AIRouter
from archai.architects.base import Architect, ArchitectureType
from archai.utils.file_ops import FileOperations
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class MonolithicArchitect(Architect):
    """Generator for monolithic architecture."""

    def __init__(self, router: AIRouter) -> None:
        super().__init__(router)

    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.MONOLITHIC

    @property
    def description(self) -> str:
        return "Single deployable unit with layered architecture (controllers/services/repositories)"

    def get_template_structure(self, app_name: str) -> dict[str, str]:
        """Get monolithic template structure (for reference only, AI decides actual structure).

        Args:
            app_name: Application name

        Returns:
            Dict mapping paths to descriptions
        """
        # AI generates the actual structure, this is just documentation
        return {
            "src/": "Source code",
            "src/controllers/": "HTTP handlers",
            "src/services/": "Business logic",
            "src/repositories/": "Data access",
            "src/models/": "Data models",
        }

    async def generate(
        self,
        description: str,
        output_path: Path,
        language: str = "python",
    ) -> AsyncIterator[str]:
        """Generate a monolithic application.

        Args:
            description: Natural language description
            output_path: Where to create the project
            language: Target language

        Yields:
            Progress messages
        """
        yield f"Generating monolithic {description} at {output_path}...\n\n"
        yield "[thinking]Asking AI to generate code...[/thinking]\n"

        # Ask AI to generate the code - let AI decide the structure
        prompt = f"""Create a complete {language} monolithic application for: {description}

APPLICATION REQUIREMENT: {description}
(Build EXACTLY what is described above, not something else!)

MONOLITHIC means: single deployable unit. Keep it SIMPLE - use minimal files.
For simple apps, 1-3 files is enough. Don't over-engineer.

Output format - use EXACTLY this format for each file:

===FILE: main.py===
# code here
===END FILE===

Guidelines:
- Simple apps: 1-2 files, CLI interface
- Medium apps: 3-5 files with basic structure
- Complex apps: layered architecture if truly needed

START OUTPUT NOW with ===FILE: markers. Output complete, runnable {language} code for "{description}":"""

        full_response = ""
        chunk_count = 0
        async for chunk in self._ask_ai(prompt):
            yield chunk
            full_response += chunk
            chunk_count += 1

        # Debug: show if we got any response
        if not full_response.strip():
            yield "\n\n⚠️ WARNING: AI returned empty response!\n"
            yield "Check your AI provider connection.\n"
        else:
            yield f"\n\n[Received {len(full_response)} chars in {chunk_count} chunks]\n"

        yield "\nWriting files...\n"

        logger.debug(f"Full response length: {len(full_response)}")
        logger.debug(f"Response contains ===FILE: {full_response.count('===FILE')}")

        # Parse and write files
        files_written = await self._parse_and_write_files(full_response, output_path)

        yield f"\nCreated {len(files_written)} files:\n"
        for file_path in files_written:
            relative = file_path.relative_to(output_path)
            yield f"  {relative}\n"

        yield f"\n✅ Monolithic application created at {output_path}\n"

        # Add run instructions
        yield "\n📋 To run:\n"
        yield f"  cd {output_path}\n"

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
            # Find any .py file
            py_files = list(output_path.rglob("main.py")) or list(output_path.rglob("*.py"))
            if py_files:
                rel_path = py_files[0].relative_to(output_path)
                yield f"  python {rel_path}\n"

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

        # Pattern to match ===FILE: path=== format (handle optional spaces)
        pattern = r"===\s*FILE:\s*(.+?)\s*===\s*\n(.*?)===\s*END\s*FILE\s*==="
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)

        logger.info(f"Pattern 1 (===FILE:===): found {len(matches)} matches")

        # Fallback: try markdown code blocks with filename comments
        # e.g., ```python\n# filename: src/main.py\n or ```python:src/main.py
        if not matches:
            logger.debug("No ===FILE=== markers found, trying markdown format")
            # Pattern: ```lang:filepath or ```lang\n# filepath
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
            header_pattern = r"(?:\*\*|###?\s*)([^\*\n]+\.(?:py|txt|md|yaml|json))\*?\*?\s*\n+```\w*\n(.*?)```"
            matches = re.findall(header_pattern, response, re.DOTALL)
            logger.info(f"Pattern 3 (header+code): found {len(matches)} matches")

        # Pattern 4: **1. `package.json`** followed by ```lang ... ```
        if not matches:
            logger.debug("Trying **N. `filename`** format")
            bold_num_pattern = r"\*\*\d+\.\s*`([^`]+)`\*\*\s*\n```[a-z]*\n(.*?)```"
            matches = re.findall(bold_num_pattern, response, re.DOTALL)
            logger.info(f"Pattern 4 (bold numbered): found {len(matches)} matches")

        # Pattern 5: **`src/index.js`** or similar
        if not matches:
            logger.debug("Trying **`filename`** format")
            bold_backtick_pattern = r"\*\*`([^`]+)`\*\*\s*\n```[a-z]*\n(.*?)```"
            matches = re.findall(bold_backtick_pattern, response, re.DOTALL)
            logger.info(f"Pattern 5 (bold backtick): found {len(matches)} matches")

        # Pattern 6: Find ALL code blocks and extract filename from surrounding text
        if not matches:
            logger.debug("Trying to extract code blocks with nearby filenames")
            blocks = re.split(r'(```[a-z]*\n.*?```)', response, flags=re.DOTALL)
            for i in range(0, len(blocks) - 1, 2):
                context = blocks[i] if i < len(blocks) else ""
                code_block = blocks[i + 1] if i + 1 < len(blocks) else ""

                # Look for filepath in context before the code block
                filepath_match = re.search(r'[`\*]*([a-zA-Z0-9_/\.\-]+\.(?:py|js|ts|json|yaml|yml|md|env|txt))[`\*]*', context[-300:])
                if filepath_match and code_block:
                    filepath = filepath_match.group(1)
                    # Extract code content from the block
                    code_content = re.sub(r'^```[a-z]*\n', '', code_block)
                    code_content = re.sub(r'\n```$', '', code_content)
                    if code_content.strip():
                        matches.append((filepath, code_content))
            logger.info(f"Pattern 6 (context extraction): found {len(matches)} matches")

        # Last resort: just find any code block and save as main.py
        if not matches:
            logger.warning("No file patterns matched, looking for any code block")
            code_pattern = r"```(?:python)?\n(.*?)```"
            code_matches = re.findall(code_pattern, response, re.DOTALL)
            if code_matches:
                # Take the largest code block
                largest = max(code_matches, key=len)
                matches.append(("main.py", largest))
                logger.info("Fallback: using largest code block as main.py")

        logger.info(f"Total files to write: {len(matches)}")

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        for filepath, content in matches:
            filepath = filepath.strip()
            # Remove any leading/trailing quotes
            filepath = filepath.strip("'\"")
            content = content.strip()

            # Sanitize filepath for Windows (remove invalid characters)
            filepath = filepath.replace("\\", "/")  # Normalize to forward slashes

            # Place files directly in output path (AI decides the structure)
            full_path = output_path / filepath

            try:
                # Ensure parent directory exists
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file synchronously as fallback if async fails
                try:
                    await FileOperations.write_file(full_path, content)
                except Exception as async_err:
                    logger.warning(f"Async write failed, trying sync: {async_err}")
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)

                files_written.append(full_path)
                logger.info(f"Successfully wrote file: {full_path}")
            except Exception as e:
                logger.error(f"Error writing {full_path}: {e}")
                # Print to console for visibility
                print(f"ERROR writing file {full_path}: {e}")

        if not files_written:
            logger.error("No files were written! AI response may not have correct format.")
            logger.debug(f"Response preview: {response[:500]}...")

        return files_written
