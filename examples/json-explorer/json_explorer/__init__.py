"""
JSON Explorer: RLM-Style Large JSON Querying

Query massive JSON files (Discord exports, API dumps, logs) with small models
using recursive language model techniques.

Key Features:
- Exhaustive extraction: Find EVERY mention of a topic with citations
- Verification: All answers traceable to source records (like textbook-qa)
- Multiple LLM backends: Anthropic, Z.AI, OpenAI, Claude Code, Codex, MCP
- Storage: Neon PostgreSQL (caching), Cloudflare R2 (files)

Example:
    >>> from json_explorer import JsonExplorer
    >>> explorer = JsonExplorer(model="claude-3-haiku-20240307")
    >>> explorer.load("/path/to/discord_export.json")
    >>> result = explorer.query("What were the main topics discussed?")
    >>> print(result.answer)

With Z.AI (GLM 4.7):
    >>> from json_explorer.config import get_preset
    >>> explorer = JsonExplorer(config=get_preset("zai_thorough"))
    >>> explorer.load("/path/to/export.json")
    >>> result = explorer.query("Find mentions of product launch")

Exhaustive Query (find EVERY mention with citations):
    >>> # This finds ALL mentions, with full context and verification
    >>> result = explorer.query("What are people saying about Kling 2.6 for video generation?")
    >>> print(result.answer)  # Includes all citations
    >>> print(result.verification.citations_found)  # Number of mentions found
    >>> print(result.get_reference_ids())  # List of record IDs for verification
"""

from .core import JsonExplorer, QueryResult, VerificationResult
from .config import ExplorerConfig, TraceLevel, AdapterType, get_preset, PRESETS
from .schema import SchemaAnalyzer, JsonSchema
from .query_planner import QueryPlan, QueryPlanner, QueryIntent
from .executor import ChunkExecutor, ExecutionResult
from .aggregator import ResultAggregator
from .trace import ExecutionTrace, TraceEntry
from .chunker import JsonChunker, Chunk
from .citation import Citation, CitationReport, CitationExtractor, Sentiment

# Analysis framework (modular analyzers)
from .analysis import (
    BaseAnalyzer,
    AnalysisQuestion,
    AnalysisResult,
    AnalysisPipeline,
    AnalysisReport,
    MarketingAnalyzer,
    ResearchAnalyzer,
    ProductAnalyzer,
    SupportAnalyzer,
    SentimentAnalyzer,
    CustomAnalyzer,
)

__all__ = [
    # Main API
    "JsonExplorer",
    "QueryResult",
    "VerificationResult",
    "ExplorerConfig",
    "AdapterType",
    "get_preset",
    "PRESETS",
    
    # Schema analysis
    "SchemaAnalyzer",
    "JsonSchema",
    
    # Query planning
    "QueryPlan",
    "QueryPlanner",
    "QueryIntent",
    
    # Execution
    "ChunkExecutor",
    "ExecutionResult",
    "JsonChunker",
    "Chunk",
    
    # Citations
    "Citation",
    "CitationReport",
    "CitationExtractor",
    "Sentiment",
    
    # Aggregation
    "ResultAggregator",
    
    # Tracing
    "ExecutionTrace",
    "TraceEntry",
    "TraceLevel",
    
    # Analysis Framework (modular analyzers)
    "BaseAnalyzer",
    "AnalysisQuestion",
    "AnalysisResult",
    "AnalysisPipeline",
    "AnalysisReport",
    "MarketingAnalyzer",
    "ResearchAnalyzer",
    "ProductAnalyzer",
    "SupportAnalyzer",
    "SentimentAnalyzer",
    "CustomAnalyzer",
]

__version__ = "0.1.0"

