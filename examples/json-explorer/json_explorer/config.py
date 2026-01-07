"""
Configuration for JSON Explorer.

Design: Single source of truth for all configuration options.
All values have sensible defaults for production use.

Supports:
- Anthropic API (direct)
- Z.AI endpoint (Claude Code compatible)
- OpenAI API
- Claude Code CLI
- Codex CLI
- MCP servers
- Neon PostgreSQL for caching
- Cloudflare R2 for file storage
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Literal


class TraceLevel(Enum):
    """Level of execution tracing detail."""
    MINIMAL = "minimal"    # Just final answer
    SUMMARY = "summary"    # Answer + high-level steps
    FULL = "full"          # Complete execution trace with all LLM calls


class ChunkingStrategy(Enum):
    """How to chunk the JSON data."""
    AUTO = "auto"              # Auto-detect based on format
    RECORDS = "records"        # Split array of objects
    TIME_BASED = "time_based"  # Group by timestamp field
    SIZE_BASED = "size_based"  # Fixed size chunks
    FIELD_BASED = "field_based"  # Group by a specific field value


class AdapterType(Enum):
    """LLM adapter types."""
    ANTHROPIC = "anthropic"    # Direct Anthropic API
    ZAI = "zai"                # Z.AI endpoint (Claude Code compatible)
    OPENAI = "openai"          # OpenAI API
    CLAUDE_CODE = "claude_code"  # Claude Code CLI
    CODEX = "codex"            # OpenAI Codex CLI
    MCP = "mcp"                # Generic MCP server


@dataclass
class ExplorerConfig:
    """
    Configuration for JsonExplorer.
    
    All parameters have production-safe defaults.
    
    Attributes:
        model: LLM model identifier
        adapter_type: LLM adapter to use (anthropic, zai, openai, claude_code, codex, mcp)
        api_key: Optional API key (defaults to env var)
        base_url: Custom API base URL (for Z.AI: https://api.z.ai/api/anthropic)
        
        max_chunk_size: Maximum characters per chunk sent to LLM
        max_chunks_per_query: Limit on chunks processed per query
        max_tokens_budget: Total token budget for a query
        timeout_seconds: Timeout for LLM calls
        
        parallel_chunks: Number of chunks to process in parallel
        enable_caching: Cache chunk results for repeated queries
        cache_ttl_seconds: Cache time-to-live
        
        chunking_strategy: How to chunk the data
        chunk_overlap: Characters of overlap between chunks
        
        trace_level: Level of execution tracing
        trace_output_dir: Directory to save traces (None = don't save)
        
        auto_detect_format: Auto-detect Discord, Slack, etc.
        fallback_to_generic: Fall back to generic handler on detection failure
        
        max_retries: Retries for failed LLM calls
        retry_delay_seconds: Delay between retries
        
        # Storage
        use_neon: Use Neon PostgreSQL for caching (vs in-memory)
        neon_database_url: Neon connection string
        use_r2: Use Cloudflare R2 for file storage
        
        # CLI adapters
        cli_working_dir: Working directory for CLI adapters
        sandbox_mode: Sandbox mode for Codex (read-only, workspace-write, danger-full-access)
    """
    
    # Model configuration
    model: str = "claude-3-haiku-20240307"
    adapter_type: AdapterType = AdapterType.ANTHROPIC
    api_key: Optional[str] = None  # Falls back to env var based on adapter
    base_url: Optional[str] = None  # For Z.AI: https://api.z.ai/api/anthropic
    
    # Backwards compatibility alias
    @property
    def provider(self) -> str:
        """Alias for adapter_type (backwards compatibility)."""
        return self.adapter_type.value
    
    # Processing limits
    max_chunk_size: int = 50_000  # ~12K tokens for Haiku
    max_chunks_per_query: int = 100
    max_tokens_budget: int = 100_000  # Total tokens across all calls
    timeout_seconds: int = 120
    
    # Parallelism and caching
    parallel_chunks: int = 4
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Chunking configuration
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.AUTO
    chunk_overlap: int = 500  # Characters of overlap
    
    # Tracing and debugging
    trace_level: TraceLevel = TraceLevel.FULL
    trace_output_dir: Optional[str] = None
    
    # Format detection
    auto_detect_format: bool = True
    fallback_to_generic: bool = True
    
    # Reliability
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Advanced: Schema sampling
    schema_sample_size: int = 100  # Records to sample for schema detection
    schema_max_depth: int = 10  # Max nesting depth to analyze
    
    # Storage configuration
    use_neon: bool = False  # Use Neon PostgreSQL for caching
    neon_database_url: Optional[str] = None  # Defaults to NEON_DATABASE_URL env var
    use_r2: bool = False  # Use Cloudflare R2 for file storage
    r2_bucket: Optional[str] = None  # Defaults to CLOUDFLARE_R2_BUCKET_NAME env var
    
    # CLI adapter configuration
    cli_working_dir: Optional[str] = None  # Working directory for CLI adapters
    sandbox_mode: str = "read-only"  # Codex sandbox mode
    
    # MCP configuration
    mcp_server_url: Optional[str] = None  # URL for MCP server
    mcp_headers: dict = field(default_factory=dict)  # Headers for MCP requests
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_chunk_size < 1000:
            raise ValueError("max_chunk_size must be at least 1000 characters")
        if self.max_chunks_per_query < 1:
            raise ValueError("max_chunks_per_query must be at least 1")
        if self.parallel_chunks < 1:
            raise ValueError("parallel_chunks must be at least 1")


# Preset configurations for common use cases
PRESETS = {
    "fast": ExplorerConfig(
        model="claude-3-haiku-20240307",
        max_chunk_size=30_000,
        parallel_chunks=8,
        trace_level=TraceLevel.MINIMAL,
    ),
    "balanced": ExplorerConfig(
        model="claude-3-haiku-20240307",
        max_chunk_size=50_000,
        parallel_chunks=4,
        trace_level=TraceLevel.SUMMARY,
    ),
    "thorough": ExplorerConfig(
        model="claude-sonnet-4-20250514",
        max_chunk_size=100_000,
        parallel_chunks=2,
        trace_level=TraceLevel.FULL,
    ),
    "budget": ExplorerConfig(
        model="claude-3-haiku-20240307",
        max_tokens_budget=50_000,
        max_chunks_per_query=50,
        parallel_chunks=2,
    ),
    # Z.AI presets (uses GLM models via Claude API)
    "zai_fast": ExplorerConfig(
        model="glm-4.5-air",  # Maps to Claude Haiku
        adapter_type=AdapterType.ZAI,
        base_url="https://api.z.ai/api/anthropic",
        max_chunk_size=30_000,
        parallel_chunks=8,
        trace_level=TraceLevel.MINIMAL,
    ),
    "zai_thorough": ExplorerConfig(
        model="glm-4.7",  # Maps to Claude Sonnet/Opus
        adapter_type=AdapterType.ZAI,
        base_url="https://api.z.ai/api/anthropic",
        max_chunk_size=100_000,
        parallel_chunks=2,
        trace_level=TraceLevel.FULL,
    ),
    # Production preset with Neon + R2
    "production": ExplorerConfig(
        model="claude-3-haiku-20240307",
        use_neon=True,
        use_r2=True,
        enable_caching=True,
        cache_ttl_seconds=86400,  # 24 hours
        trace_level=TraceLevel.FULL,
    ),
    # Claude Code CLI preset
    "claude_code": ExplorerConfig(
        adapter_type=AdapterType.CLAUDE_CODE,
        model="claude-code-cli",
        timeout_seconds=300,  # 5 minutes for complex queries
    ),
    # Codex CLI preset
    "codex": ExplorerConfig(
        adapter_type=AdapterType.CODEX,
        model="gpt-5",
        sandbox_mode="read-only",
        timeout_seconds=300,
    ),
}


def get_preset(name: str) -> ExplorerConfig:
    """Get a preset configuration by name."""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
    return PRESETS[name]

