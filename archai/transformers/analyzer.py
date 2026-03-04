"""Code structure analyzer for understanding existing projects."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Optional

from archai.ai.base import Message, Role
from archai.ai.router import AIRouter
from archai.architects.base import ArchitectureType
from archai.config.prompts import ANALYSIS_PROMPT, SYSTEM_PROMPT
from archai.utils.code_parser import CodeParser, ProjectStructure
from archai.utils.file_ops import FileOperations
from archai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    """Result of code analysis."""

    project_path: Path
    detected_architecture: Optional[ArchitectureType] = None
    structure: Optional[ProjectStructure] = None
    summary: str = ""
    components: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    ai_analysis: str = ""


class CodeAnalyzer:
    """Analyzes existing codebases to understand their architecture."""

    def __init__(self, router: AIRouter) -> None:
        """Initialize analyzer.

        Args:
            router: AI router for LLM interactions
        """
        self.router = router
        self.parser = CodeParser()

    async def analyze(
        self,
        project_path: Path,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Analyze a project and yield progress/results.

        Args:
            project_path: Path to project root
            stream: Whether to stream AI response

        Yields:
            Progress messages and analysis
        """
        yield f"Analyzing project at {project_path}...\n\n"

        # Check if path exists
        if not await FileOperations.exists(project_path):
            yield f"Error: Path does not exist: {project_path}\n"
            return

        if not await FileOperations.is_dir(project_path):
            yield f"Error: Path is not a directory: {project_path}\n"
            return

        # Parse project structure
        yield "Parsing code structure...\n"
        structure = self.parser.parse_project(project_path)

        yield f"Found {len(structure.modules)} modules\n"
        yield f"Found {sum(len(m.classes) for m in structure.modules)} classes\n"
        yield f"Found {sum(len(m.functions) for m in structure.modules)} functions\n\n"

        # Build context for AI
        context = self._build_analysis_context(structure)

        yield "Analyzing architecture patterns...\n\n"
        yield "[thinking]Asking AI to analyze architecture...[/thinking]\n"

        # Get AI analysis
        messages = [
            Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
            Message(role=Role.USER, content=f"{ANALYSIS_PROMPT}\n\n{context}"),
        ]

        if stream:
            async for chunk in self.router.chat(messages, stream=True):
                yield chunk
        else:
            response = await self.router.chat_complete(messages)
            yield response

    async def get_analysis_result(self, project_path: Path) -> AnalysisResult:
        """Get structured analysis result.

        Args:
            project_path: Path to project root

        Returns:
            AnalysisResult instance
        """
        result = AnalysisResult(project_path=project_path)

        if not project_path.exists() or not project_path.is_dir():
            result.summary = f"Invalid path: {project_path}"
            return result

        # Parse structure
        structure = self.parser.parse_project(project_path)
        result.structure = structure
        result.dependencies = structure.dependencies

        # Build summary
        result.summary = self.parser.get_project_summary(structure)

        # Extract components
        for module in structure.modules:
            for cls in module.classes:
                result.components.append(f"{module.path.stem}.{cls.name}")

        # Detect architecture
        result.detected_architecture = self._detect_architecture(structure)

        # Get AI analysis
        context = self._build_analysis_context(structure)
        messages = [
            Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
            Message(role=Role.USER, content=f"{ANALYSIS_PROMPT}\n\n{context}"),
        ]

        result.ai_analysis = await self.router.chat_complete(messages)

        return result

    def _build_analysis_context(self, structure: ProjectStructure) -> str:
        """Build context string for AI analysis.

        Args:
            structure: Parsed project structure

        Returns:
            Context string
        """
        lines = [
            f"Project root: {structure.root}",
            f"Total modules: {len(structure.modules)}",
            "",
            "== Directory Structure ==",
        ]

        # Build tree view
        seen_dirs: set[Path] = set()
        for module in sorted(structure.modules, key=lambda m: str(m.path)):
            rel_path = module.path.relative_to(structure.root)
            # Add parent directories
            for parent in rel_path.parents:
                if parent != Path(".") and parent not in seen_dirs:
                    lines.append(f"  {parent}/")
                    seen_dirs.add(parent)
            lines.append(f"  {rel_path}")

        lines.append("")
        lines.append("== Classes ==")
        for module in structure.modules:
            for cls in module.classes:
                rel_path = module.path.relative_to(structure.root)
                bases_str = f" ({', '.join(cls.bases)})" if cls.bases else ""
                lines.append(f"  {rel_path}:{cls.line_number} - {cls.name}{bases_str}")
                if cls.methods:
                    methods_str = ", ".join(cls.methods[:5])
                    if len(cls.methods) > 5:
                        methods_str += f" ... (+{len(cls.methods) - 5} more)"
                    lines.append(f"    Methods: {methods_str}")

        lines.append("")
        lines.append("== Top-level Functions ==")
        for module in structure.modules:
            for func in module.functions:
                if not func.name.startswith("_"):
                    rel_path = module.path.relative_to(structure.root)
                    async_str = "async " if func.is_async else ""
                    lines.append(f"  {rel_path}:{func.line_number} - {async_str}{func.name}")

        if structure.dependencies:
            lines.append("")
            lines.append("== Dependencies ==")
            for dep in structure.dependencies[:20]:
                lines.append(f"  - {dep}")
            if len(structure.dependencies) > 20:
                lines.append(f"  ... and {len(structure.dependencies) - 20} more")

        if structure.entry_points:
            lines.append("")
            lines.append("== Entry Points ==")
            for ep in structure.entry_points:
                lines.append(f"  - {ep.relative_to(structure.root)}")

        return "\n".join(lines)

    def _detect_architecture(self, structure: ProjectStructure) -> Optional[ArchitectureType]:
        """Detect architecture type from structure.

        Args:
            structure: Parsed project structure

        Returns:
            Detected architecture type or None
        """
        dir_names = set()
        for module in structure.modules:
            for parent in module.path.relative_to(structure.root).parents:
                dir_names.add(str(parent))

        # Check for microservices
        if "services" in dir_names or any(
            "service" in str(m.path) for m in structure.modules
        ):
            # Multiple service directories suggest microservices
            service_dirs = [
                d for d in dir_names if "service" in d.lower() and d != "services"
            ]
            if len(service_dirs) > 1:
                return ArchitectureType.MICROSERVICES

        # Check for serverless
        if "functions" in dir_names or any(
            "lambda" in str(m.path).lower() for m in structure.modules
        ):
            return ArchitectureType.SERVERLESS

        # Check for hexagonal
        if "ports" in dir_names and "adapters" in dir_names:
            return ArchitectureType.HEXAGONAL

        # Check for event-driven
        if "events" in dir_names and (
            "handlers" in dir_names or "subscribers" in dir_names
        ):
            return ArchitectureType.EVENT_DRIVEN

        # Check for monolithic patterns
        if any(
            name in dir_names
            for name in ["controllers", "services", "repositories", "models"]
        ):
            return ArchitectureType.MONOLITHIC

        # Default to monolithic for simple structures
        if len(structure.modules) > 0:
            return ArchitectureType.MONOLITHIC

        return None
