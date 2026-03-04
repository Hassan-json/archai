"""Code parsing utilities for understanding project structure."""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from archai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    file_path: Path
    line_number: int
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class FunctionInfo:
    """Information about a function."""

    name: str
    file_path: Path
    line_number: int
    parameters: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_async: bool = False


@dataclass
class ImportInfo:
    """Information about an import."""

    module: str
    names: list[str] = field(default_factory=list)
    is_from_import: bool = False


@dataclass
class ModuleInfo:
    """Information about a module/file."""

    path: Path
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class ProjectStructure:
    """Overall project structure."""

    root: Path
    modules: list[ModuleInfo] = field(default_factory=list)
    entry_points: list[Path] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class PythonParser:
    """Parser for Python source files."""

    def parse_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """Parse a Python file and extract structure info.

        Args:
            file_path: Path to Python file

        Returns:
            ModuleInfo or None if parsing fails
        """
        try:
            with open(file_path, "r") as f:
                source = f.read()

            tree = ast.parse(source)
            return self._extract_module_info(tree, file_path)

        except SyntaxError as e:
            logger.warning(f"Syntax error parsing {file_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
            return None

    def _extract_module_info(self, tree: ast.Module, file_path: Path) -> ModuleInfo:
        """Extract module information from AST.

        Args:
            tree: AST module
            file_path: Path to the file

        Returns:
            ModuleInfo instance
        """
        module = ModuleInfo(path=file_path)
        module.docstring = ast.get_docstring(tree)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                module.classes.append(self._extract_class_info(node, file_path))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                module.functions.append(self._extract_function_info(node, file_path))
            elif isinstance(node, ast.Import):
                module.imports.append(self._extract_import(node))
            elif isinstance(node, ast.ImportFrom):
                module.imports.append(self._extract_import_from(node))

        return module

    def _extract_class_info(self, node: ast.ClassDef, file_path: Path) -> ClassInfo:
        """Extract class information from AST node.

        Args:
            node: Class definition node
            file_path: Path to the file

        Returns:
            ClassInfo instance
        """
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attr_name(base)}")

        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        return ClassInfo(
            name=node.name,
            file_path=file_path,
            line_number=node.lineno,
            bases=bases,
            methods=methods,
            docstring=ast.get_docstring(node),
        )

    def _extract_function_info(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: Path
    ) -> FunctionInfo:
        """Extract function information from AST node.

        Args:
            node: Function definition node
            file_path: Path to the file

        Returns:
            FunctionInfo instance
        """
        params = [arg.arg for arg in node.args.args]

        return FunctionInfo(
            name=node.name,
            file_path=file_path,
            line_number=node.lineno,
            parameters=params,
            docstring=ast.get_docstring(node),
            is_async=isinstance(node, ast.AsyncFunctionDef),
        )

    def _extract_import(self, node: ast.Import) -> ImportInfo:
        """Extract import information.

        Args:
            node: Import node

        Returns:
            ImportInfo instance
        """
        names = [alias.name for alias in node.names]
        return ImportInfo(module=names[0] if len(names) == 1 else "", names=names)

    def _extract_import_from(self, node: ast.ImportFrom) -> ImportInfo:
        """Extract from-import information.

        Args:
            node: ImportFrom node

        Returns:
            ImportInfo instance
        """
        return ImportInfo(
            module=node.module or "",
            names=[alias.name for alias in node.names],
            is_from_import=True,
        )

    def _get_attr_name(self, node: ast.Attribute) -> str:
        """Get full attribute name (e.g., 'module.Class').

        Args:
            node: Attribute node

        Returns:
            Full attribute name
        """
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))


class CodeParser:
    """Main code parser that handles multiple languages."""

    def __init__(self) -> None:
        self.python_parser = PythonParser()

    def parse_project(self, root: Path) -> ProjectStructure:
        """Parse a project directory.

        Args:
            root: Project root directory

        Returns:
            ProjectStructure instance
        """
        structure = ProjectStructure(root=root)

        # Find Python files
        python_files = list(root.rglob("*.py"))

        for file_path in python_files:
            # Skip common exclude directories
            if any(
                part in file_path.parts
                for part in ["__pycache__", ".venv", "venv", "node_modules", ".git"]
            ):
                continue

            module_info = self.python_parser.parse_file(file_path)
            if module_info:
                structure.modules.append(module_info)

            # Check for entry points
            if file_path.name in ["main.py", "__main__.py", "app.py", "cli.py"]:
                structure.entry_points.append(file_path)

        # Parse requirements
        requirements_file = root / "requirements.txt"
        if requirements_file.exists():
            structure.dependencies = self._parse_requirements(requirements_file)

        # Parse pyproject.toml dependencies
        pyproject_file = root / "pyproject.toml"
        if pyproject_file.exists():
            structure.dependencies.extend(self._parse_pyproject_deps(pyproject_file))

        return structure

    def _parse_requirements(self, path: Path) -> list[str]:
        """Parse requirements.txt file.

        Args:
            path: Path to requirements.txt

        Returns:
            List of package names
        """
        deps = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (before version specifier)
                    match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                    if match:
                        deps.append(match.group(1))
        return deps

    def _parse_pyproject_deps(self, path: Path) -> list[str]:
        """Parse dependencies from pyproject.toml.

        Args:
            path: Path to pyproject.toml

        Returns:
            List of package names
        """
        deps = []
        try:
            with open(path) as f:
                content = f.read()

            # Simple regex extraction (not full TOML parsing)
            deps_match = re.search(
                r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL
            )
            if deps_match:
                deps_str = deps_match.group(1)
                for match in re.finditer(r'"([a-zA-Z0-9_-]+)', deps_str):
                    deps.append(match.group(1))
        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {e}")

        return deps

    def get_project_summary(self, structure: ProjectStructure) -> str:
        """Generate a human-readable summary of the project structure.

        Args:
            structure: ProjectStructure instance

        Returns:
            Summary string
        """
        lines = [
            f"Project: {structure.root.name}",
            f"Modules: {len(structure.modules)}",
            "",
        ]

        total_classes = sum(len(m.classes) for m in structure.modules)
        total_functions = sum(len(m.functions) for m in structure.modules)

        lines.append(f"Total classes: {total_classes}")
        lines.append(f"Total functions: {total_functions}")
        lines.append("")

        if structure.entry_points:
            lines.append("Entry points:")
            for ep in structure.entry_points:
                lines.append(f"  - {ep.relative_to(structure.root)}")
            lines.append("")

        if structure.dependencies:
            lines.append(f"Dependencies: {len(structure.dependencies)}")
            for dep in structure.dependencies[:10]:
                lines.append(f"  - {dep}")
            if len(structure.dependencies) > 10:
                lines.append(f"  ... and {len(structure.dependencies) - 10} more")

        return "\n".join(lines)
