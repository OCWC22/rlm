"""
CLI and LLM adapters for JSON Explorer.

Supports multiple backends:
- Anthropic API (direct)
- Z.AI endpoint (Claude Code compatible)
- OpenAI API
- Claude Code CLI
- Codex CLI
- MCP servers
"""

from .base import LLMAdapter, AdapterConfig
from .anthropic_adapter import AnthropicAdapter
from .zai_adapter import ZAIAdapter
from .claude_code_adapter import ClaudeCodeAdapter
from .codex_adapter import CodexAdapter
from .mcp_adapter import MCPAdapter

__all__ = [
    "LLMAdapter",
    "AdapterConfig",
    "AnthropicAdapter",
    "ZAIAdapter",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "MCPAdapter",
]

