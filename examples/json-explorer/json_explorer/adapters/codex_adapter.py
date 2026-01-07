"""
OpenAI Codex CLI adapter.

Runs queries through the Codex CLI tool.
Supports GPT-5, o3, o3-mini models.

Docs: https://developers.openai.com/codex
"""

import os
import subprocess
import json
from typing import Optional

from .base import LLMAdapter, AdapterConfig, CompletionResult


# Codex model options
CODEX_MODELS = ["gpt-5", "o3", "o3-mini"]

# Sandbox modes
SANDBOX_MODES = ["read-only", "workspace-write", "danger-full-access"]


class CodexAdapter(LLMAdapter):
    """
    OpenAI Codex CLI adapter.
    
    Runs prompts through the `codex` CLI tool.
    
    Prerequisites:
        npm install -g @openai/codex
        codex login --api-key "your-openai-api-key"
        
    Environment variables:
        OPENAI_API_KEY: OpenAI API key
        
    Example:
        >>> config = AdapterConfig(
        ...     adapter_type=AdapterType.CODEX,
        ...     model="gpt-5",
        ...     sandbox_mode="read-only",
        ... )
        >>> adapter = CodexAdapter(config)
        >>> result = adapter.complete("Explain this function")
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        
        self.cli_path = config.cli_path or "codex"
        self.working_dir = config.working_dir or os.getcwd()
        self.sandbox_mode = config.sandbox_mode or "read-only"
        
        # Map model names
        model = config.model.lower()
        if model in CODEX_MODELS:
            self.model = model
        else:
            self.model = "gpt-5"  # Default
        
        # Verify CLI is available
        self._verify_cli()
    
    def _verify_cli(self):
        """Verify Codex CLI is installed."""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError("Codex CLI not working")
        except FileNotFoundError:
            raise ImportError(
                "Codex CLI not found. Install with: "
                "npm install -g @openai/codex"
            )
    
    def complete(self, prompt: str, system: Optional[str] = None) -> CompletionResult:
        """
        Run a prompt through Codex CLI.
        
        Uses non-interactive mode with JSON output.
        """
        # Combine system prompt if provided
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n---\n\n{prompt}"
        
        # Build command for non-interactive execution
        cmd = [
            self.cli_path,
            "exec",  # Non-interactive mode
            "--model", self.model,
            "--sandbox", self.sandbox_mode,
            "--approval", "never",  # Don't ask for approval
            full_prompt,
        ]
        
        # Run in the specified directory
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.working_dir,
            timeout=self.config.timeout,
            env={
                **os.environ,
                "OPENAI_API_KEY": self.config.api_key or os.environ.get("OPENAI_API_KEY", ""),
            },
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Codex error: {result.stderr}")
        
        content = result.stdout.strip()
        
        # Codex doesn't report token usage in CLI
        # Estimate based on content length
        estimated_tokens = len(content.split()) * 1.3
        
        return CompletionResult(
            content=content,
            tokens_used=int(estimated_tokens),
            model=f"codex-{self.model}",
            stop_reason="end_turn",
        )
    
    def ask(
        self,
        prompt: str,
        files: Optional[list[str]] = None,
        image: Optional[str] = None,
    ) -> CompletionResult:
        """
        Ask Codex with additional context.
        
        Args:
            prompt: The question or instruction
            files: Optional file paths to reference (use @file syntax)
            image: Optional image path to analyze
        """
        # Build file references
        full_prompt = prompt
        if files:
            refs = " ".join(f"@{f}" for f in files)
            full_prompt = f"{refs} {prompt}"
        
        # Build command
        cmd = [
            self.cli_path,
            "exec",
            "--model", self.model,
            "--sandbox", self.sandbox_mode,
        ]
        
        if image:
            cmd.extend(["--image", image])
        
        cmd.append(full_prompt)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.working_dir,
            timeout=self.config.timeout,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Codex error: {result.stderr}")
        
        content = result.stdout.strip()
        
        return CompletionResult(
            content=content,
            tokens_used=int(len(content.split()) * 1.3),
            model=f"codex-{self.model}",
        )
    
    def stream(self, prompt: str, system: Optional[str] = None):
        """
        Stream is not supported in CLI mode.
        Falls back to regular completion.
        """
        result = self.complete(prompt, system)
        yield result.content


class CodexMCPAdapter(LLMAdapter):
    """
    Codex via MCP server (codex-mcp-server).
    
    Uses the codex-mcp-server package for structured interaction.
    
    Prerequisites:
        npm install -g codex-cli-mcp-tool
    
    MCP Config:
        {
            "mcpServers": {
                "codex": {
                    "command": "codex-cli-mcp-tool",
                    "args": []
                }
            }
        }
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        # MCP client would be configured here
        self._mcp_client = None
    
    def complete(self, prompt: str, system: Optional[str] = None) -> CompletionResult:
        """Delegate to Codex via MCP."""
        # Fall back to CLI for now
        cli_adapter = CodexAdapter(self.config)
        return cli_adapter.complete(prompt, system)

