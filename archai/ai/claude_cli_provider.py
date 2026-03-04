"""Claude CLI provider - uses Claude Code subscription via subprocess."""

import asyncio
import os
import shutil
from typing import AsyncIterator

from archai.ai.base import AIProvider, Message, Role
from archai.config.settings import ProviderConfig
from archai.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeCLIProvider(AIProvider):
    """Claude CLI provider using Claude Code subscription.

    This provider calls the `claude` CLI via subprocess, allowing you to use
    your Claude subscription (Max, Pro, etc.) instead of API credits.

    Requirements:
        - Claude CLI installed (`npm install -g @anthropic-ai/claude-code`)
        - Logged in (`claude login`)

    Configuration:
        providers:
          claude-cli:
            model: claude-sonnet-4-20250514  # optional, uses CLI default
            timeout: 300  # longer timeout for CLI
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize Claude CLI provider.

        Args:
            config: Provider configuration
        """
        self._config = config
        self._model = config.model or self.DEFAULT_MODEL
        self._timeout = config.timeout or 300
        self._claude_path = shutil.which("claude")

        if not self._claude_path:
            logger.warning("Claude CLI not found in PATH")

    def _build_prompt(self, messages: list[Message]) -> str:
        """Build a single prompt from message history.

        Args:
            messages: List of messages

        Returns:
            Combined prompt string
        """
        parts = []
        system_prompt = None

        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_prompt = msg.content
            elif msg.role == Role.USER:
                parts.append(msg.content)
            elif msg.role == Role.ASSISTANT:
                parts.append(f"Assistant: {msg.content}")

        prompt = "\n\n".join(parts)

        # Add instruction to just output text (no tool usage)
        preamble = """IMPORTANT: You are being used as a text generation backend.
Do NOT use any tools or try to write files. Just output the requested text/code directly.
Do NOT say things like "I don't have access to tools" - just generate the content.

"""
        if system_prompt:
            prompt = f"{preamble}{system_prompt}\n\n{prompt}"
        else:
            prompt = f"{preamble}{prompt}"

        return prompt

    @property
    def name(self) -> str:
        return "claude-cli"

    @property
    def model(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Send a chat request via Claude CLI.

        Args:
            messages: List of messages
            stream: Whether to stream (always streams with CLI)

        Yields:
            Response chunks
        """
        if not self._claude_path:
            raise RuntimeError(
                "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

        # Build the prompt from messages
        prompt = self._build_prompt(messages)

        # Build command - use --print for non-interactive output
        cmd = [
            self._claude_path,
            "--print",  # Non-interactive, print response (also skips workspace trust dialog)
            "--output-format", "text",  # Plain text output (simpler, more reliable)
            "--dangerously-skip-permissions",  # Skip all permission prompts
            "--no-session-persistence",  # Don't save session to disk
        ]

        # Add model if specified
        if self._model:
            cmd.extend(["--model", self._model])

        # Add the prompt as positional argument
        cmd.append(prompt)

        logger.debug(f"Running Claude CLI: {' '.join(cmd[:4])}...")

        try:
            # Create clean environment - remove API keys to force subscription usage
            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)
            env.pop("CLAUDE_API_KEY", None)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=os.path.expanduser("~"),  # Run from home to avoid project configs
            )

            # Stream stdout - plain text format
            got_content = False
            error_lines = []

            while True:
                line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=self._timeout
                )

                if not line:
                    break

                # Plain text output - yield directly
                line_str = line.decode("utf-8")

                # Check for error patterns
                line_lower = line_str.lower()
                if "invalid" in line_lower and "api" in line_lower:
                    error_lines.append(line_str.strip())
                elif line_lower.startswith("error:"):
                    error_lines.append(line_str.strip())
                else:
                    # Normal output - yield with newline preserved
                    yield line_str
                    got_content = True

            await process.wait()

            # Check for errors from stdout first, then stderr
            if error_lines:
                error_msg = "\n".join(error_lines)
                logger.error(f"Claude CLI error: {error_msg}")
                raise RuntimeError(f"Claude CLI error: {error_msg}")

            if process.returncode != 0:
                stderr = await process.stderr.read()
                error_msg = stderr.decode("utf-8").strip()

                if not error_msg:
                    error_msg = f"Claude CLI exited with code {process.returncode}"

                logger.error(f"Claude CLI error: {error_msg}")

                if "not logged in" in error_msg.lower():
                    raise RuntimeError("Claude CLI not logged in. Run: claude login")
                elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    raise RuntimeError("Claude subscription quota exceeded")
                elif "api key" in error_msg.lower() or "api_key" in error_msg.lower():
                    raise RuntimeError(
                        "Claude CLI API key error. This usually means an invalid API key "
                        "is configured. To use your subscription, ensure no ANTHROPIC_API_KEY "
                        "is set, or run: claude logout && claude login"
                    )
                else:
                    raise RuntimeError(f"Claude CLI error: {error_msg}")

        except asyncio.TimeoutError:
            logger.error(f"Claude CLI timeout after {self._timeout}s")
            raise RuntimeError(f"Claude CLI timeout after {self._timeout} seconds")
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            raise

    async def chat_complete(
        self,
        messages: list[Message],
    ) -> str:
        """Send a chat request and get complete response.

        Args:
            messages: List of messages

        Returns:
            Complete response text
        """
        result = []
        async for chunk in self.chat(messages, stream=False):
            result.append(chunk)
        return "".join(result)

    async def get_models(self) -> list[str]:
        """Get available Claude models.

        Returns:
            List of model strings available via CLI
        """
        return [
            "claude-opus-4-5-20250514",
            "claude-sonnet-4-20250514",
            "claude-3-5-haiku-20241022",
        ]

    async def is_available(self) -> bool:
        """Check if Claude CLI is available and logged in.

        Returns:
            True if CLI is available and authenticated
        """
        if not self._claude_path:
            return False

        try:
            # Check if claude is logged in by running a simple command
            process = await asyncio.create_subprocess_exec(
                self._claude_path,
                "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()
            return process.returncode == 0
        except Exception as e:
            logger.debug(f"Claude CLI availability check failed: {e}")
            return False
