"""File system operations for Archai."""

import os
import shutil
from pathlib import Path
from typing import Optional

import aiofiles
import aiofiles.os

from archai.utils.logger import get_logger

logger = get_logger(__name__)


class FileOperations:
    """Utility class for file system operations."""

    @staticmethod
    async def write_file(path: Path, content: str) -> None:
        """Write content to a file asynchronously.

        Args:
            path: Path to the file
            content: Content to write
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        logger.debug(f"Wrote file: {path}")

    @staticmethod
    async def read_file(path: Path) -> str:
        """Read content from a file asynchronously.

        Args:
            path: Path to the file

        Returns:
            File content as string
        """
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
        return content

    @staticmethod
    async def exists(path: Path) -> bool:
        """Check if a path exists.

        Args:
            path: Path to check

        Returns:
            True if path exists
        """
        return await aiofiles.os.path.exists(path)

    @staticmethod
    async def is_dir(path: Path) -> bool:
        """Check if a path is a directory.

        Args:
            path: Path to check

        Returns:
            True if path is a directory
        """
        return await aiofiles.os.path.isdir(path)

    @staticmethod
    async def mkdir(path: Path, parents: bool = True) -> None:
        """Create a directory.

        Args:
            path: Path to create
            parents: Create parent directories if needed
        """
        if parents:
            path.mkdir(parents=True, exist_ok=True)
        else:
            await aiofiles.os.mkdir(path)
        logger.debug(f"Created directory: {path}")

    @staticmethod
    async def list_dir(path: Path) -> list[str]:
        """List contents of a directory.

        Args:
            path: Directory path

        Returns:
            List of file/directory names
        """
        return await aiofiles.os.listdir(path)

    @staticmethod
    def copy_tree(src: Path, dst: Path) -> None:
        """Copy a directory tree synchronously.

        Args:
            src: Source directory
            dst: Destination directory
        """
        shutil.copytree(src, dst, dirs_exist_ok=True)
        logger.debug(f"Copied {src} to {dst}")

    @staticmethod
    def remove_tree(path: Path) -> None:
        """Remove a directory tree synchronously.

        Args:
            path: Directory to remove
        """
        if path.exists():
            shutil.rmtree(path)
            logger.debug(f"Removed directory: {path}")

    @staticmethod
    async def get_project_files(
        path: Path,
        extensions: Optional[list[str]] = None,
        exclude_dirs: Optional[list[str]] = None,
    ) -> list[Path]:
        """Get all project files recursively.

        Args:
            path: Root directory
            extensions: File extensions to include (e.g., ['.py', '.js'])
            exclude_dirs: Directory names to exclude

        Returns:
            List of file paths
        """
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".java", ".go", ".rs"]
        if exclude_dirs is None:
            exclude_dirs = [
                "__pycache__",
                "node_modules",
                ".git",
                ".venv",
                "venv",
                "dist",
                "build",
            ]

        files: list[Path] = []

        def _scan_dir(dir_path: Path) -> None:
            try:
                for entry in os.scandir(dir_path):
                    if entry.is_dir():
                        if entry.name not in exclude_dirs:
                            _scan_dir(Path(entry.path))
                    elif entry.is_file():
                        file_path = Path(entry.path)
                        if file_path.suffix in extensions:
                            files.append(file_path)
            except PermissionError:
                logger.warning(f"Permission denied: {dir_path}")

        _scan_dir(path)
        return files
