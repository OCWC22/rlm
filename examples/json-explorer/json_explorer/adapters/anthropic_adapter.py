"""
Anthropic API adapter.

Direct API access to Claude models.
"""

import os
from typing import Optional

from .base import LLMAdapter, AdapterConfig, CompletionResult


class AnthropicAdapter(LLMAdapter):
    """
    Anthropic API adapter.
    
    Uses the official anthropic SDK.
    
    Environment variables:
        ANTHROPIC_API_KEY: API key
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic SDK not installed. Run: pip install anthropic"
            )
        
        api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable required"
            )
        
        self._client = anthropic.Anthropic(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
    
    def complete(self, prompt: str, system: Optional[str] = None) -> CompletionResult:
        """Generate a completion using Anthropic API."""
        kwargs = {
            "model": self.config.model,
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
        """Stream completion tokens."""
        kwargs = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system:
            kwargs["system"] = system
        
        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

