"""
Z.AI adapter for Claude Code endpoint.

Z.AI provides an Anthropic-compatible API at https://api.z.ai/api/anthropic
This adapter enables using Z.AI's GLM models through Claude Code.

Docs: https://docs.z.ai/devpack/tool/claude

Environment variables:
    Z_AI_API_KEY: Your Z.AI API key

To use with Claude Code:
    export ANTHROPIC_AUTH_TOKEN="your_zai_api_key"
    export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
    export API_TIMEOUT_MS="3000000"  # 50 minutes
"""

import os
from typing import Optional

from .base import LLMAdapter, AdapterConfig, CompletionResult


# Z.AI configuration
ZAI_BASE_URL = "https://api.z.ai/api/anthropic"

# Default to GLM 4.7 (their best model)
ZAI_DEFAULT_MODEL = "glm-4.7"

# Model mappings (Claude models map to GLM)
ZAI_MODEL_MAPPING = {
    # Claude → GLM mapping (Z.AI translates these)
    "claude-3-opus-20240229": "glm-4.7",
    "claude-sonnet-4-20250514": "glm-4.7",
    "claude-3-5-sonnet-20240620": "glm-4.7",
    "claude-3-haiku-20240307": "glm-4.5-air",
    # Direct GLM models (preferred - use these directly)
    "glm-4.7": "glm-4.7",           # Best model - use this for thorough analysis
    "glm-4.5-air": "glm-4.5-air",   # Fast model - good for high-volume queries
    # Aliases for convenience
    "glm-4": "glm-4.7",
    "glm-fast": "glm-4.5-air",
}


class ZAIAdapter(LLMAdapter):
    """
    Z.AI Anthropic-compatible adapter.
    
    Provides access to GLM models through the Claude API interface.
    Works with Claude Code using the Z.AI endpoint.
    
    Example:
        >>> config = AdapterConfig(
        ...     adapter_type=AdapterType.ZAI,
        ...     model="claude-3-haiku-20240307",  # Maps to GLM-4.5-Air
        ... )
        >>> adapter = ZAIAdapter(config)
        >>> result = adapter.complete("Hello!")
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic SDK not installed. Run: pip install anthropic"
            )
        
        # Get Z.AI API key
        api_key = config.api_key or os.environ.get("Z_AI_API_KEY")
        if not api_key:
            raise ValueError(
                "Z_AI_API_KEY environment variable required. "
                "Get your key at https://z.ai/manage-apikey/apikey-list"
            )
        
        # Use Z.AI base URL
        base_url = config.base_url or ZAI_BASE_URL
        
        self._client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=config.timeout,
        )
        
        # Map model name if needed - default to GLM 4.7
        requested_model = config.model or ZAI_DEFAULT_MODEL
        self._effective_model = ZAI_MODEL_MAPPING.get(
            requested_model, requested_model
        )
    
    def complete(self, prompt: str, system: Optional[str] = None) -> CompletionResult:
        """Generate a completion using Z.AI API."""
        kwargs = {
            "model": self._effective_model,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system:
            kwargs["system"] = system
        
        if self.config.temperature > 0:
            kwargs["temperature"] = self.config.temperature
        
        response = self._client.messages.create(**kwargs)
        
        # Extract content
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        
        # Calculate tokens
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
        return CompletionResult(
            content=content,
            tokens_used=tokens_used,
            model=response.model,
            stop_reason=response.stop_reason,
            raw_response=response,
        )
    
    def stream(self, prompt: str, system: Optional[str] = None):
        """Stream completion tokens from Z.AI."""
        kwargs = {
            "model": self._effective_model,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system:
            kwargs["system"] = system
        
        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    
    @property
    def model_name(self) -> str:
        """Get the effective model name."""
        return self._effective_model


def setup_zai_for_claude_code() -> dict:
    """
    Get environment variables needed for Claude Code + Z.AI.
    
    Returns:
        Dict of environment variables to set
        
    Usage in shell:
        export ANTHROPIC_AUTH_TOKEN="your_zai_api_key"
        export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
        export API_TIMEOUT_MS="3000000"
        
    To enable Zread MCP (for citations from open-source repos):
        claude mcp add -s user -t http zread https://api.z.ai/api/mcp/zread/mcp --header "Authorization: Bearer your_zai_api_key"
    """
    api_key = os.environ.get("Z_AI_API_KEY", "")
    
    return {
        "ANTHROPIC_AUTH_TOKEN": api_key,
        "ANTHROPIC_BASE_URL": ZAI_BASE_URL,
        "API_TIMEOUT_MS": "3000000",  # 50 minutes
    }


def get_zai_mcp_command(api_key: Optional[str] = None) -> str:
    """
    Get the command to add Zread MCP server to Claude Code.
    
    The Zread MCP server enables Claude Code to access documentation
    and code from open-source repositories with citations.
    
    Args:
        api_key: Z.AI API key. If None, uses Z_AI_API_KEY env var.
        
    Returns:
        The claude mcp add command string
    """
    key = api_key or os.environ.get("Z_AI_API_KEY", "YOUR_ZAI_API_KEY")
    return f'claude mcp add -s user -t http zread https://api.z.ai/api/mcp/zread/mcp --header "Authorization: Bearer {key}"'

