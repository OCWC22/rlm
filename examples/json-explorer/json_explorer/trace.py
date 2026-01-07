"""
Execution Trace: Complete audit trail for deterministic debugging.

Design Philosophy:
- Every decision and action is logged
- Traces are serializable (JSON/Markdown)
- Same input → same trace (deterministic)
- Traces enable replay and debugging
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Literal
from pathlib import Path
from enum import Enum

from .config import TraceLevel


class TraceEventType(Enum):
    """Types of events in execution trace."""
    # Lifecycle
    QUERY_START = "query_start"
    QUERY_END = "query_end"
    
    # Schema analysis
    SCHEMA_ANALYSIS_START = "schema_analysis_start"
    SCHEMA_ANALYSIS_END = "schema_analysis_end"
    
    # Query planning
    PLAN_START = "plan_start"
    PLAN_END = "plan_end"
    PLAN_DECISION = "plan_decision"
    
    # Chunk processing
    CHUNK_START = "chunk_start"
    CHUNK_END = "chunk_end"
    CHUNK_SKIP = "chunk_skip"
    
    # LLM calls
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    LLM_CALL_ERROR = "llm_call_error"
    
    # Aggregation
    AGGREGATE_START = "aggregate_start"
    AGGREGATE_END = "aggregate_end"
    
    # Citations (for exhaustive extraction)
    CITATION_EXTRACT = "citation_extract"
    CITATION_VERIFY = "citation_verify"
    
    # Errors and warnings
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class TraceEntry:
    """A single entry in the execution trace."""
    timestamp: str
    event_type: TraceEventType
    message: str
    data: Optional[dict] = None
    duration_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Serialize for JSON output."""
        result = {
            "timestamp": self.timestamp,
            "event": self.event_type.value,
            "message": self.message,
        }
        if self.data:
            result["data"] = self.data
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.tokens_used is not None:
            result["tokens_used"] = self.tokens_used
        return result
    
    def to_markdown(self) -> str:
        """Format as markdown line."""
        icon = self._get_icon()
        time_str = self.timestamp[11:19] if len(self.timestamp) > 19 else self.timestamp
        
        line = f"{icon} `{time_str}` **{self.event_type.value}**: {self.message}"
        
        if self.duration_ms is not None:
            line += f" ({self.duration_ms:.0f}ms)"
        if self.tokens_used is not None:
            line += f" [{self.tokens_used} tokens]"
        
        return line
    
    def _get_icon(self) -> str:
        """Get emoji icon for event type."""
        icons = {
            TraceEventType.QUERY_START: "🚀",
            TraceEventType.QUERY_END: "✅",
            TraceEventType.SCHEMA_ANALYSIS_START: "🔍",
            TraceEventType.SCHEMA_ANALYSIS_END: "📋",
            TraceEventType.PLAN_START: "📝",
            TraceEventType.PLAN_END: "📊",
            TraceEventType.PLAN_DECISION: "🎯",
            TraceEventType.CHUNK_START: "📦",
            TraceEventType.CHUNK_END: "✓",
            TraceEventType.CHUNK_SKIP: "⏭️",
            TraceEventType.LLM_CALL_START: "🤖",
            TraceEventType.LLM_CALL_END: "💬",
            TraceEventType.LLM_CALL_ERROR: "❌",
            TraceEventType.AGGREGATE_START: "🔗",
            TraceEventType.AGGREGATE_END: "📊",
            TraceEventType.CITATION_EXTRACT: "📑",
            TraceEventType.CITATION_VERIFY: "✔️",
            TraceEventType.ERROR: "🚨",
            TraceEventType.WARNING: "⚠️",
            TraceEventType.INFO: "ℹ️",
        }
        return icons.get(self.event_type, "•")


@dataclass
class ExecutionTrace:
    """
    Complete execution trace for a query.
    
    Provides full audit trail of what happened during query processing.
    Like textbook-qa's trace files, includes all citations for verification.
    """
    query_id: str
    query: str
    started_at: str
    file_path: Optional[str] = None
    
    # Trace entries
    entries: list[TraceEntry] = field(default_factory=list)
    
    # Summary stats
    total_duration_ms: Optional[float] = None
    total_tokens: int = 0
    total_llm_calls: int = 0
    chunks_processed: int = 0
    chunks_skipped: int = 0
    
    # Citation stats (for exhaustive queries)
    citations_found: int = 0
    citations_verified: int = 0
    unique_authors: int = 0
    reference_ids: list[str] = field(default_factory=list)
    
    # Result
    answer: Optional[str] = None
    error: Optional[str] = None
    
    def add_entry(
        self,
        event_type: TraceEventType,
        message: str,
        data: Optional[dict] = None,
        duration_ms: Optional[float] = None,
        tokens_used: Optional[int] = None,
    ):
        """Add an entry to the trace."""
        entry = TraceEntry(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            message=message,
            data=data,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
        )
        self.entries.append(entry)
        
        # Update summary stats
        if tokens_used:
            self.total_tokens += tokens_used
        if event_type == TraceEventType.LLM_CALL_END:
            self.total_llm_calls += 1
        if event_type == TraceEventType.CHUNK_END:
            self.chunks_processed += 1
        if event_type == TraceEventType.CHUNK_SKIP:
            self.chunks_skipped += 1
    
    def log_query_start(self, query: str, file_path: Optional[str] = None):
        """Log query start."""
        self.add_entry(
            TraceEventType.QUERY_START,
            f"Starting query: {query[:100]}...",
            data={"query": query, "file": file_path},
        )
    
    def log_query_end(self, answer: str, duration_ms: float):
        """Log query completion."""
        self.answer = answer
        self.total_duration_ms = duration_ms
        self.add_entry(
            TraceEventType.QUERY_END,
            f"Query completed successfully",
            data={"answer_length": len(answer)},
            duration_ms=duration_ms,
        )
    
    def log_error(self, error: str, details: Optional[dict] = None):
        """Log an error."""
        self.error = error
        self.add_entry(
            TraceEventType.ERROR,
            error,
            data=details,
        )
    
    def log_llm_call(
        self,
        purpose: str,
        prompt_preview: str,
        response_preview: str,
        tokens: int,
        duration_ms: float,
    ):
        """Log an LLM call with details."""
        self.add_entry(
            TraceEventType.LLM_CALL_START,
            f"Calling LLM: {purpose}",
            data={"prompt_preview": prompt_preview[:200]},
        )
        self.add_entry(
            TraceEventType.LLM_CALL_END,
            f"LLM responded",
            data={"response_preview": response_preview[:200]},
            duration_ms=duration_ms,
            tokens_used=tokens,
        )
    
    def log_citations(
        self,
        citations_found: int,
        unique_authors: int,
        reference_ids: list[str],
        verification_issues: list[str],
    ):
        """
        Log citation extraction results.
        
        Similar to textbook-qa's page reference logging.
        """
        self.citations_found = citations_found
        self.unique_authors = unique_authors
        self.reference_ids = reference_ids
        
        self.add_entry(
            TraceEventType.CITATION_EXTRACT,
            f"Extracted {citations_found} citations from {unique_authors} contributors",
            data={
                "citations_found": citations_found,
                "unique_authors": unique_authors,
                "sample_refs": reference_ids[:10],
            },
        )
        
        if verification_issues:
            self.add_entry(
                TraceEventType.WARNING,
                f"Citation verification issues: {len(verification_issues)}",
                data={"issues": verification_issues[:5]},
            )
    
    def to_dict(self) -> dict:
        """Serialize full trace to dictionary."""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "started_at": self.started_at,
            "file_path": self.file_path,
            "summary": {
                "total_duration_ms": self.total_duration_ms,
                "total_tokens": self.total_tokens,
                "total_llm_calls": self.total_llm_calls,
                "chunks_processed": self.chunks_processed,
                "chunks_skipped": self.chunks_skipped,
                # Citation info (for exhaustive queries)
                "citations_found": self.citations_found,
                "citations_verified": self.citations_verified,
                "unique_authors": self.unique_authors,
            },
            "reference_ids": self.reference_ids,
            "answer": self.answer,
            "error": self.error,
            "entries": [e.to_dict() for e in self.entries],
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_markdown(self, level: TraceLevel = TraceLevel.FULL) -> str:
        """Format trace as markdown document."""
        lines = [
            f"# Execution Trace: {self.query_id}",
            "",
            f"> **Query:** {self.query}",
            f"> **Started:** {self.started_at}",
            f"> **File:** {self.file_path or 'N/A'}",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Duration | {self.total_duration_ms or 0:.0f}ms |",
            f"| LLM Calls | {self.total_llm_calls} |",
            f"| Tokens Used | {self.total_tokens:,} |",
            f"| Chunks Processed | {self.chunks_processed} |",
            f"| Chunks Skipped | {self.chunks_skipped} |",
        ]
        
        # Add citation info if present
        if self.citations_found > 0:
            lines.extend([
                f"| Citations Found | {self.citations_found} |",
                f"| Unique Authors | {self.unique_authors} |",
            ])
        
        lines.append("")
        
        if self.answer:
            lines.extend([
                "## Answer",
                "",
                self.answer,
                "",
            ])
        
        if self.error:
            lines.extend([
                "## ⚠️ Error",
                "",
                f"```\n{self.error}\n```",
                "",
            ])
        
        if level in [TraceLevel.SUMMARY, TraceLevel.FULL]:
            lines.extend([
                "## Execution Timeline",
                "",
            ])
            
            # Filter entries based on level
            entries_to_show = self.entries
            if level == TraceLevel.SUMMARY:
                # Only show high-level events
                high_level = {
                    TraceEventType.QUERY_START,
                    TraceEventType.QUERY_END,
                    TraceEventType.SCHEMA_ANALYSIS_END,
                    TraceEventType.PLAN_END,
                    TraceEventType.AGGREGATE_END,
                    TraceEventType.ERROR,
                }
                entries_to_show = [e for e in self.entries if e.event_type in high_level]
            
            for entry in entries_to_show:
                lines.append(entry.to_markdown())
            
            lines.append("")
        
        if level == TraceLevel.FULL:
            # Include raw data for key entries
            lines.extend([
                "## Detailed Data",
                "",
            ])
            
            for entry in self.entries:
                if entry.data and entry.event_type in {
                    TraceEventType.PLAN_END,
                    TraceEventType.LLM_CALL_END,
                }:
                    lines.append(f"### {entry.event_type.value}")
                    lines.append(f"```json")
                    lines.append(json.dumps(entry.data, indent=2, ensure_ascii=False)[:1000])
                    lines.append(f"```")
                    lines.append("")
        
        # Add reference IDs for verification (like textbook-qa page links)
        if self.reference_ids:
            lines.extend([
                "## 🔗 Source Verification References",
                "",
                "Use these reference IDs to look up original records:",
                "",
            ])
            
            for ref in self.reference_ids[:20]:  # Show first 20
                lines.append(f"- `{ref}`")
            
            if len(self.reference_ids) > 20:
                lines.append(f"- ... and {len(self.reference_ids) - 20} more")
            
            lines.append("")
        
        lines.append("---")
        lines.append(f"*Generated by JSON Explorer*")
        
        return "\n".join(lines)
    
    def save(self, output_dir: str | Path, format: Literal["json", "markdown", "both"] = "both"):
        """Save trace to file(s)."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = f"trace-{self.query_id}"
        
        if format in ["json", "both"]:
            json_path = output_dir / f"{base_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
        
        if format in ["markdown", "both"]:
            md_path = output_dir / f"{base_name}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(self.to_markdown())


class TraceContext:
    """
    Context manager for building execution traces.
    
    Usage:
        with TraceContext(query, file_path) as trace:
            trace.log_schema_analysis(schema)
            trace.log_chunk_processing(chunk, result)
            ...
    """
    
    def __init__(
        self,
        query: str,
        file_path: Optional[str] = None,
        level: TraceLevel = TraceLevel.FULL,
    ):
        self.query = query
        self.file_path = file_path
        self.level = level
        self._start_time: Optional[float] = None
        self.trace: Optional[ExecutionTrace] = None
    
    def __enter__(self) -> ExecutionTrace:
        import time
        import uuid
        
        self._start_time = time.time()
        
        self.trace = ExecutionTrace(
            query_id=str(uuid.uuid4())[:8],
            query=self.query,
            started_at=datetime.now().isoformat(),
            file_path=self.file_path,
        )
        
        self.trace.log_query_start(self.query, self.file_path)
        
        return self.trace
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        
        if self.trace and self._start_time:
            duration_ms = (time.time() - self._start_time) * 1000
            
            if exc_type:
                self.trace.log_error(str(exc_val))
            elif self.trace.answer:
                self.trace.log_query_end(self.trace.answer, duration_ms)
            else:
                self.trace.total_duration_ms = duration_ms
        
        return False  # Don't suppress exceptions

