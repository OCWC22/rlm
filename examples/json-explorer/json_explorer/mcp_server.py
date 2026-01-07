"""
MCP Server: Expose JSON Explorer as an MCP server for iOS/web integration.

This allows the JSON Explorer to be used by:
- iOS apps via MCP protocol
- Web apps via MCP protocol
- Other agents via tool calls

Design Philosophy:
- Stateful: Load a file once, query many times
- Safe: No arbitrary file access, just JSON exploration
- Observable: Full trace available for debugging
"""

import json
import asyncio
from typing import Optional, Any
from dataclasses import dataclass, asdict

# MCP SDK (if available)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    Server = None

from .core import JsonExplorer, QueryResult
from .config import ExplorerConfig, TraceLevel


@dataclass
class ServerState:
    """State for the MCP server."""
    explorer: Optional[JsonExplorer] = None
    loaded_file: Optional[str] = None
    last_result: Optional[QueryResult] = None


class JsonExplorerMCPServer:
    """
    MCP Server wrapper for JSON Explorer.
    
    Exposes tools:
    - load_json: Load a JSON file for exploration
    - analyze_schema: Get schema information
    - query: Ask a question about the data
    - get_sample: Get sample records
    - get_trace: Get the last execution trace
    """
    
    def __init__(
        self,
        config: Optional[ExplorerConfig] = None,
        allowed_paths: Optional[list[str]] = None,
    ):
        """
        Args:
            config: Explorer configuration
            allowed_paths: List of allowed path prefixes for security
        """
        self.config = config or ExplorerConfig()
        self.allowed_paths = allowed_paths or []  # Empty = allow all
        self.state = ServerState()
        
        if HAS_MCP:
            self.server = Server("json-explorer")
            self._register_tools()
        else:
            self.server = None
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="load_json",
                    description="Load a JSON file for exploration. Call this first before querying.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the JSON file to load"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="analyze_schema",
                    description="Get schema information about the loaded JSON file.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="query",
                    description="Ask a natural language question about the loaded JSON data.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question to ask"
                            },
                            "save_trace": {
                                "type": "boolean",
                                "description": "Whether to save execution trace",
                                "default": False
                            }
                        },
                        "required": ["question"]
                    }
                ),
                Tool(
                    name="get_sample",
                    description="Get sample records from the loaded JSON data.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "count": {
                                "type": "integer",
                                "description": "Number of records to return",
                                "default": 5
                            }
                        }
                    }
                ),
                Tool(
                    name="get_trace",
                    description="Get the execution trace from the last query.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "format": {
                                "type": "string",
                                "enum": ["json", "markdown", "summary"],
                                "default": "summary"
                            }
                        }
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            try:
                if name == "load_json":
                    result = await self._load_json(arguments["file_path"])
                elif name == "analyze_schema":
                    result = await self._analyze_schema()
                elif name == "query":
                    result = await self._query(
                        arguments["question"],
                        arguments.get("save_trace", False)
                    )
                elif name == "get_sample":
                    result = await self._get_sample(arguments.get("count", 5))
                elif name == "get_trace":
                    result = await self._get_trace(arguments.get("format", "summary"))
                else:
                    result = f"Unknown tool: {name}"
                
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {e}")]
    
    def _check_path_allowed(self, file_path: str) -> bool:
        """Check if file path is allowed."""
        if not self.allowed_paths:
            return True
        
        from pathlib import Path
        abs_path = str(Path(file_path).resolve())
        
        return any(abs_path.startswith(allowed) for allowed in self.allowed_paths)
    
    async def _load_json(self, file_path: str) -> str:
        """Load a JSON file."""
        if not self._check_path_allowed(file_path):
            return f"Access denied: {file_path} is not in allowed paths"
        
        # Create new explorer
        self.state.explorer = JsonExplorer(config=self.config)
        
        try:
            schema = self.state.explorer.load(file_path)
            self.state.loaded_file = file_path
            
            return f"""✅ Loaded: {file_path}

{schema.summary()}"""
        
        except Exception as e:
            self.state.explorer = None
            return f"❌ Failed to load: {e}"
    
    async def _analyze_schema(self) -> str:
        """Get schema analysis."""
        if not self.state.explorer:
            return "❌ No file loaded. Use load_json first."
        
        return self.state.explorer.analyze_schema()
    
    async def _query(self, question: str, save_trace: bool = False) -> str:
        """Query the loaded data."""
        if not self.state.explorer:
            return "❌ No file loaded. Use load_json first."
        
        result = self.state.explorer.query(question, save_trace=save_trace)
        self.state.last_result = result
        
        if result.success:
            return f"""{result.answer}

---
📊 Stats: {result.chunks_processed} chunks processed, {result.total_tokens:,} tokens, {result.duration_ms:.0f}ms"""
        else:
            return f"❌ Query failed: {result.error}"
    
    async def _get_sample(self, count: int = 5) -> str:
        """Get sample records."""
        if not self.state.explorer:
            return "❌ No file loaded. Use load_json first."
        
        samples = self.state.explorer.get_sample(count)
        return json.dumps(samples, indent=2, ensure_ascii=False)
    
    async def _get_trace(self, format: str = "summary") -> str:
        """Get the last execution trace."""
        if not self.state.last_result or not self.state.last_result.trace:
            return "❌ No query executed yet."
        
        trace = self.state.last_result.trace
        
        if format == "json":
            return trace.to_json()
        elif format == "markdown":
            return trace.to_markdown(TraceLevel.FULL)
        else:  # summary
            return trace.to_markdown(TraceLevel.SUMMARY)
    
    async def run(self):
        """Run the MCP server."""
        if not HAS_MCP:
            raise ImportError(
                "MCP SDK not installed. Run: pip install mcp"
            )
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# HTTP/REST wrapper for web integration
class JsonExplorerHTTPServer:
    """
    Simple HTTP server for JSON Explorer.
    
    Provides REST API for web integration when MCP is not available.
    """
    
    def __init__(
        self,
        config: Optional[ExplorerConfig] = None,
        host: str = "localhost",
        port: int = 8080,
    ):
        self.config = config or ExplorerConfig()
        self.host = host
        self.port = port
        self.state = ServerState()
    
    def create_app(self):
        """Create Flask/FastAPI app (if available)."""
        try:
            from flask import Flask, request, jsonify
            app = Flask(__name__)
            
            @app.route("/health")
            def health():
                return jsonify({"status": "ok"})
            
            @app.route("/load", methods=["POST"])
            def load():
                data = request.json
                file_path = data.get("file_path")
                
                if not file_path:
                    return jsonify({"error": "file_path required"}), 400
                
                try:
                    self.state.explorer = JsonExplorer(config=self.config)
                    schema = self.state.explorer.load(file_path)
                    self.state.loaded_file = file_path
                    
                    return jsonify({
                        "status": "loaded",
                        "schema": schema.to_dict()
                    })
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
            
            @app.route("/query", methods=["POST"])
            def query():
                if not self.state.explorer:
                    return jsonify({"error": "No file loaded"}), 400
                
                data = request.json
                question = data.get("question")
                
                if not question:
                    return jsonify({"error": "question required"}), 400
                
                result = self.state.explorer.query(question)
                
                return jsonify({
                    "answer": result.answer,
                    "success": result.success,
                    "chunks_processed": result.chunks_processed,
                    "total_tokens": result.total_tokens,
                    "duration_ms": result.duration_ms,
                })
            
            @app.route("/schema")
            def schema():
                if not self.state.explorer:
                    return jsonify({"error": "No file loaded"}), 400
                
                return jsonify(self.state.explorer.schema.to_dict())
            
            @app.route("/sample")
            def sample():
                if not self.state.explorer:
                    return jsonify({"error": "No file loaded"}), 400
                
                count = request.args.get("count", 5, type=int)
                samples = self.state.explorer.get_sample(count)
                return jsonify(samples)
            
            return app
            
        except ImportError:
            raise ImportError("Flask not installed. Run: pip install flask")
    
    def run(self):
        """Run the HTTP server."""
        app = self.create_app()
        app.run(host=self.host, port=self.port)


def main():
    """CLI entry point for the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="JSON Explorer MCP Server"
    )
    parser.add_argument(
        "--mode",
        choices=["mcp", "http"],
        default="mcp",
        help="Server mode: mcp (stdio) or http (REST)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="HTTP server host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP server port"
    )
    parser.add_argument(
        "--model",
        default="claude-3-haiku-20240307",
        help="LLM model to use"
    )
    parser.add_argument(
        "--allowed-paths",
        nargs="*",
        help="Allowed path prefixes for file access"
    )
    
    args = parser.parse_args()
    
    config = ExplorerConfig(model=args.model)
    
    if args.mode == "mcp":
        if not HAS_MCP:
            print("MCP SDK not installed. Run: pip install mcp")
            return 1
        
        server = JsonExplorerMCPServer(
            config=config,
            allowed_paths=args.allowed_paths,
        )
        asyncio.run(server.run())
    
    else:  # http
        server = JsonExplorerHTTPServer(
            config=config,
            host=args.host,
            port=args.port,
        )
        print(f"Starting HTTP server at http://{args.host}:{args.port}")
        server.run()


if __name__ == "__main__":
    main()

