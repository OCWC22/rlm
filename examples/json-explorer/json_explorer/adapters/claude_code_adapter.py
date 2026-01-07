"""
Claude Code CLI adapter.

Runs queries through the Claude Code CLI tool.
Useful for leveraging Claude Code's file access and context.

Docs: https://docs.anthropic.com/en/docs/claude-code/overview
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .base import LLMAdapter, AdapterConfig, CompletionResult


class ClaudeCodeAdapter(LLMAdapter):
    """
    Claude Code CLI adapter.
    
    Runs prompts through the `claude` CLI tool in non-interactive mode.
    
    Prerequisites:
        npm install -g @anthropic-ai/claude-code
        
    Environment variables:
        ANTHROPIC_API_KEY: Claude API key
        
    Example:
        >>> config = AdapterConfig(
        ...     adapter_type=AdapterType.CLAUDE_CODE,
        ...     working_dir="/path/to/project",
        ... )
        >>> adapter = ClaudeCodeAdapter(config)
        >>> result = adapter.complete("Explain this codebase")
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        
        self.cli_path = config.cli_path or "claude"
        self.working_dir = config.working_dir or os.getcwd()
        
        # Verify CLI is available
        self._verify_cli()
    
    def _verify_cli(self):
        """Verify Claude Code CLI is installed."""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError("Claude Code CLI not working")
        except FileNotFoundError:
            raise ImportError(
                "Claude Code CLI not found. Install with: "
                "npm install -g @anthropic-ai/claude-code"
            )
    
    def complete(self, prompt: str, system: Optional[str] = None) -> CompletionResult:
        """
        Run a prompt through Claude Code CLI.
        
        Uses --print mode for non-interactive execution.
        """
        # Combine system prompt if provided
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n---\n\n{prompt}"
        
        # Build command
        cmd = [
            self.cli_path,
            "--print",  # Non-interactive, print result
            "--output-format", "text",  # Plain text output
        ]
        
        # Run in the specified directory
        result = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            cwd=self.working_dir,
            timeout=self.config.timeout,
            env={
                **os.environ,
                # Ensure API key is available
                "ANTHROPIC_API_KEY": self.config.api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
            },
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Claude Code error: {result.stderr}")
        
        content = result.stdout.strip()
        
        # Claude Code doesn't report token usage in CLI
        # Estimate based on content length
        estimated_tokens = len(content.split()) * 1.3
        
        return CompletionResult(
            content=content,
            tokens_used=int(estimated_tokens),
            model="claude-code-cli",
            stop_reason="end_turn",
        )
    
    def complete_with_files(
        self,
        prompt: str,
        files: list[str],
        system: Optional[str] = None,
    ) -> CompletionResult:
        """
        Run a prompt with specific file context.
        
        Args:
            prompt: User prompt
            files: List of file paths to include as context
            system: Optional system prompt
        """
        # Build file references
        file_refs = "\n".join(f"@{f}" for f in files)
        full_prompt = f"{file_refs}\n\n{prompt}"
        
        return self.complete(full_prompt, system)
    
    def stream(self, prompt: str, system: Optional[str] = None):
        """
        Stream is not supported in CLI mode.
        Falls back to regular completion.
        """
        result = self.complete(prompt, system)
        yield result.content


class ClaudeCodeMCPAdapter(LLMAdapter):
    """
    Claude Code via MCP server.
    
    Uses Claude Code as an MCP tool for more structured interaction.
    
    This is useful when running as an MCP server that wants to
    delegate to Claude Code for certain operations.
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        # MCP server connection would be configured here
        self._mcp_client = None
    
    def complete(self, prompt: str, system: Optional[str] = None) -> CompletionResult:
        """Delegate to Claude Code via MCP."""
        # This would use the MCP protocol to communicate
        # For now, fall back to CLI
        cli_adapter = ClaudeCodeAdapter(self.config)
        return cli_adapter.complete(prompt, system)

