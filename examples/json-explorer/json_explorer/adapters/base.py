"""
Base adapter interface for LLM backends.

All adapters implement this interface for consistent behavior.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Iterator, Any
from enum import Enum


class AdapterType(Enum):
    """Supported adapter types."""
    ANTHROPIC = "anthropic"
    ZAI = "zai"
    OPENAI = "openai"
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    MCP = "mcp"


@dataclass
class AdapterConfig:
    """
    Configuration for LLM adapters.
    
    Attributes:
        adapter_type: Type of adapter
        model: Model identifier
        api_key: API key (uses env var if not specified)
        base_url: Custom API base URL
        timeout: Request timeout in seconds
        max_tokens: Max response tokens
        temperature: Sampling temperature (0-1)
        extra: Additional adapter-specific options
    """
    adapter_type: AdapterType = AdapterType.ANTHROPIC
    model: str = "claude-3-haiku-20240307"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 120
    max_tokens: int = 4096
    temperature: float = 0.0
    extra: dict = field(default_factory=dict)
    
    # Z.AI specific
    zai_mode: str = "ZAI"
    
    # CLI specific
    cli_path: Optional[str] = None
    working_dir: Optional[str] = None
    sandbox_mode: str = "read-only"
    
    # MCP specific
    mcp_server_url: Optional[str] = None
    mcp_headers: dict = field(default_factory=dict)


@dataclass
class CompletionResult:
    """Result from an LLM completion."""
    content: str
    tokens_used: int
    model: str
    stop_reason: Optional[str] = None
    raw_response: Optional[Any] = None


class LLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.
    
    All adapters must implement:
    - complete(): Synchronous completion
    - complete_async(): Async completion (optional)
    - stream(): Streaming completion (optional)
    """
    
    def __init__(self, config: AdapterConfig):
        self.config = config
    
    @abstractmethod
    def complete(self, prompt: str, system: Optional[str] = None) -> CompletionResult:
        """
        Generate a completion.
        
        Args:
            prompt: User prompt
            system: Optional system prompt
            
        Returns:
            CompletionResult with content and metadata
        """
        pass
    
    async def complete_async(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> CompletionResult:
        """
        Async completion (default implementation calls sync).
        
        Override for true async support.
        """
        import asyncio
        return await asyncio.to_thread(self.complete, prompt, system)
    
    def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream completion tokens.
        
        Default implementation returns full response at once.
        Override for true streaming.
        """
        result = self.complete(prompt, system)
        yield result.content
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.config.model
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.config.model})"


def create_adapter(config: AdapterConfig) -> LLMAdapter:
    """
    Factory function to create an adapter from config.
    
    Args:
        config: Adapter configuration
        
    Returns:
        Configured LLMAdapter instance
    """
    from .anthropic_adapter import AnthropicAdapter
    from .zai_adapter import ZAIAdapter
    from .claude_code_adapter import ClaudeCodeAdapter
    from .codex_adapter import CodexAdapter
    from .mcp_adapter import MCPAdapter
    
    adapters = {
        AdapterType.ANTHROPIC: AnthropicAdapter,
        AdapterType.ZAI: ZAIAdapter,
        AdapterType.OPENAI: AnthropicAdapter,  # Similar interface
        AdapterType.CLAUDE_CODE: ClaudeCodeAdapter,
        AdapterType.CODEX: CodexAdapter,
        AdapterType.MCP: MCPAdapter,
    }
    
    adapter_class = adapters.get(config.adapter_type)
    if not adapter_class:
        raise ValueError(f"Unknown adapter type: {config.adapter_type}")
    
    return adapter_class(config)

