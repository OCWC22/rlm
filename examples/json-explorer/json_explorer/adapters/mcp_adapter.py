"""
Generic MCP server adapter.

Connects to any MCP server that exposes LLM-like tools.
Supports both HTTP and stdio MCP servers.

Docs: https://modelcontextprotocol.io
"""

import os
import json
import asyncio
from typing import Optional, Any

from .base import LLMAdapter, AdapterConfig, CompletionResult


class MCPAdapter(LLMAdapter):
    """
    Generic MCP server adapter.
    
    Connects to MCP servers that expose LLM completion tools.
    
    Supports:
    - HTTP/Streamable HTTP servers
    - SSE servers
    - stdio servers (via subprocess)
    
    Example:
        >>> config = AdapterConfig(
        ...     adapter_type=AdapterType.MCP,
        ...     mcp_server_url="https://api.z.ai/api/mcp/web_reader/mcp",
        ...     mcp_headers={"Authorization": "Bearer your_key"},
        ... )
        >>> adapter = MCPAdapter(config)
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        
        self.server_url = config.mcp_server_url
        self.headers = config.mcp_headers or {}
        
        # Lazy-load MCP client
        self._client = None
    
    def _get_client(self):
        """Get or create MCP client."""
        if self._client is None:
            try:
                from mcp import Client
                from mcp.client.http import http_client
            except ImportError:
                raise ImportError(
                    "MCP SDK not installed. Run: pip install mcp"
                )
            
            # Create HTTP client if URL is provided
            if self.server_url:
                self._client = Client(
                    http_client(
                        self.server_url,
                        headers=self.headers,
                    )
                )
        
        return self._client
    
    def complete(self, prompt: str, system: Optional[str] = None) -> CompletionResult:
        """
        Call the MCP server's completion tool.
        
        The server must expose a tool like "complete" or "ask".
        """
        # Run async in sync context
        return asyncio.run(self._complete_async(prompt, system))
    
    async def _complete_async(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> CompletionResult:
        """Async implementation of complete."""
        client = self._get_client()
        
        # Combine prompts
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        
        # Try common tool names
        tool_names = ["complete", "ask", "query", "generate"]
        
        async with client:
            tools = await client.list_tools()
            available = {t.name for t in tools}
            
            # Find a completion-like tool
            tool_name = None
            for name in tool_names:
                if name in available:
                    tool_name = name
                    break
            
            if not tool_name:
                raise RuntimeError(
                    f"No completion tool found. Available: {available}"
                )
            
            # Call the tool
            result = await client.call_tool(
                tool_name,
                {"prompt": full_prompt}
            )
            
            # Extract content from result
            content = ""
            if result.content:
                for item in result.content:
                    if hasattr(item, "text"):
                        content += item.text
            
            return CompletionResult(
                content=content,
                tokens_used=0,  # MCP doesn't report tokens
                model=f"mcp:{tool_name}",
            )
    
    async def complete_async(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> CompletionResult:
        """Async completion using MCP."""
        return await self._complete_async(prompt, system)
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> Any:
        """
        Call any MCP tool directly.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        client = self._get_client()
        
        async with client:
            result = await client.call_tool(tool_name, arguments)
            return result
    
    async def list_tools(self) -> list[dict]:
        """List available MCP tools."""
        client = self._get_client()
        
        async with client:
            tools = await client.list_tools()
            return [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in tools
            ]


class ZAIMCPAdapter(MCPAdapter):
    """
    Z.AI MCP server adapter.
    
    Provides access to Z.AI's MCP tools:
    - Vision MCP Server (image analysis)
    - Web Search MCP Server
    - Web Reader MCP Server
    
    Example:
        >>> config = AdapterConfig(
        ...     adapter_type=AdapterType.MCP,
        ...     api_key="your_zai_key",
        ... )
        >>> adapter = ZAIMCPAdapter(config, server="web-search")
    """
    
    SERVERS = {
        "vision": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@z_ai/mcp-server"],
        },
        "web-search": {
            "type": "http",
            "url": "https://api.z.ai/api/mcp/web_search/mcp",
        },
        "web-reader": {
            "type": "http", 
            "url": "https://api.z.ai/api/mcp/web_reader/mcp",
        },
    }
    
    def __init__(self, config: AdapterConfig, server: str = "web-search"):
        # Get server config
        server_config = self.SERVERS.get(server)
        if not server_config:
            raise ValueError(
                f"Unknown Z.AI MCP server: {server}. "
                f"Available: {list(self.SERVERS.keys())}"
            )
        
        # Set up URL and headers
        if server_config["type"] == "http":
            config.mcp_server_url = server_config["url"]
            api_key = config.api_key or os.environ.get("Z_AI_API_KEY", "")
            config.mcp_headers = {
                "Authorization": f"Bearer {api_key}"
            }
        
        super().__init__(config)
        self.server_name = server

