"""
JSON Explorer Core: Main orchestration class.

This is the primary entry point for the JSON Explorer.
Combines schema analysis, query planning, chunk execution, and aggregation.

Design Philosophy:
- Every answer should be verifiable with citations
- Exhaustive queries find EVERY mention (like textbook-qa finds every page)
- Full trace for auditability
"""

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterator
from datetime import datetime

from .config import ExplorerConfig, TraceLevel
from .schema import SchemaAnalyzer, JsonSchema
from .chunker import JsonChunker, Chunk
from .query_planner import QueryPlanner, QueryPlan, QueryIntent
from .executor import ChunkExecutor, ExecutionResult, LLMClient
from .aggregator import ResultAggregator
from .trace import ExecutionTrace, TraceContext, TraceEventType
from .citation import Citation, CitationReport, CitationExtractor, Sentiment


@dataclass
class VerificationResult:
    """
    Verification info for an answer, similar to textbook-qa.
    
    Tracks what citations were found, what was verified, and any issues.
    """
    has_citations: bool = False
    citations_found: int = 0
    citations_verified: int = 0
    unique_authors: int = 0
    
    # Sentiment breakdown
    positive_mentions: int = 0
    negative_mentions: int = 0
    neutral_mentions: int = 0
    
    # Issues
    issues: list[str] = field(default_factory=list)
    
    # Reference IDs for lookup
    reference_ids: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "has_citations": self.has_citations,
            "citations_found": self.citations_found,
            "citations_verified": self.citations_verified,
            "unique_authors": self.unique_authors,
            "positive_mentions": self.positive_mentions,
            "negative_mentions": self.negative_mentions,
            "neutral_mentions": self.neutral_mentions,
            "issues": self.issues,
            "reference_ids": self.reference_ids,
        }


@dataclass
class QueryResult:
    """
    Complete result from a query.
    
    Contains the answer, execution trace, citations, and verification metadata.
    """
    answer: str
    success: bool
    
    # Execution details
    query: str
    file_path: Optional[str] = None
    
    # Stats
    chunks_processed: int = 0
    chunks_filtered: int = 0
    total_tokens: int = 0
    duration_ms: float = 0
    
    # Full trace
    trace: Optional[ExecutionTrace] = None
    
    # Citations (for exhaustive queries)
    citation_report: Optional[CitationReport] = None
    verification: Optional[VerificationResult] = None
    
    # Error info
    error: Optional[str] = None
    
    def __str__(self) -> str:
        """Return just the answer for easy printing."""
        return self.answer
    
    def summary(self) -> str:
        """Return a summary with stats."""
        lines = [
            f"Answer: {self.answer[:200]}{'...' if len(self.answer) > 200 else ''}",
            "",
            f"Stats:",
            f"  - Chunks processed: {self.chunks_processed}",
            f"  - Chunks filtered: {self.chunks_filtered}",
            f"  - Tokens used: {self.total_tokens:,}",
            f"  - Duration: {self.duration_ms:.0f}ms",
        ]
        
        if self.verification:
            lines.extend([
                "",
                f"Citations:",
                f"  - Found: {self.verification.citations_found}",
                f"  - Unique authors: {self.verification.unique_authors}",
                f"  - Positive: {self.verification.positive_mentions}",
                f"  - Negative: {self.verification.negative_mentions}",
            ])
        
        return "\n".join(lines)
    
    def get_citations_markdown(self) -> str:
        """Get all citations formatted as markdown."""
        if self.citation_report:
            return self.citation_report.to_markdown()
        return "No citations available."
    
    def get_reference_ids(self) -> list[str]:
        """Get list of reference IDs for verification."""
        if self.citation_report:
            return self.citation_report.get_all_references()
        return []


class JsonExplorer:
    """
    Query large JSON files using RLM-style recursive exploration.
    
    This class orchestrates the full pipeline:
    1. Load and analyze JSON schema
    2. Plan query execution based on intent
    3. Chunk and filter data
    4. Process chunks through LLM
    5. Aggregate results into final answer
    
    Example:
        >>> explorer = JsonExplorer(model="claude-3-haiku-20240307")
        >>> explorer.load("/path/to/discord_export.json")
        >>> result = explorer.query("What were the main topics discussed?")
        >>> print(result.answer)
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[ExplorerConfig] = None,
    ):
        """
        Initialize JSON Explorer.
        
        Args:
            model: LLM model name (e.g., "claude-3-haiku-20240307")
            provider: LLM provider ("anthropic" or "openai")
            api_key: API key (optional, uses env var if not provided)
            config: Full configuration object (overrides other args)
        """
        # Use provided config or create from args
        if config:
            self.config = config
        else:
            self.config = ExplorerConfig(
                model=model or "claude-3-haiku-20240307",
                provider=provider or "anthropic",
                api_key=api_key,
            )
        
        # Initialize LLM client
        self.llm = LLMClient(
            model=self.config.model,
            provider=self.config.provider,
            api_key=self.config.api_key,
            timeout=self.config.timeout_seconds,
            base_url=self.config.base_url,
        )
        
        # State
        self._file_path: Optional[str] = None
        self._schema: Optional[JsonSchema] = None
        self._data: Optional[list] = None  # Cached data if small enough
        
        # Components (initialized lazily)
        self._chunker: Optional[JsonChunker] = None
        self._planner: Optional[QueryPlanner] = None
        self._executor: Optional[ChunkExecutor] = None
        self._aggregator: Optional[ResultAggregator] = None
    
    @property
    def schema(self) -> Optional[JsonSchema]:
        """Get the analyzed schema (None if no file loaded)."""
        return self._schema
    
    @property
    def file_path(self) -> Optional[str]:
        """Get the loaded file path (None if no file loaded)."""
        return self._file_path
    
    def load(self, file_path: str) -> JsonSchema:
        """
        Load and analyze a JSON file.
        
        This analyzes the schema without loading all data into memory.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            JsonSchema with structure information
        """
        file_path = str(Path(file_path).resolve())
        self._file_path = file_path
        
        # Analyze schema
        analyzer = SchemaAnalyzer(
            sample_size=self.config.schema_sample_size,
            max_depth=self.config.schema_max_depth,
        )
        self._schema = analyzer.analyze(file_path)
        
        # Initialize components
        self._chunker = JsonChunker(
            schema=self._schema,
            max_chunk_size=self.config.max_chunk_size,
            strategy=self.config.chunking_strategy,
        )
        
        self._planner = QueryPlanner(schema=self._schema)
        
        self._executor = ChunkExecutor(
            llm_client=self.llm,
            schema=self._schema,
            max_parallel=self.config.parallel_chunks,
            cache_enabled=self.config.enable_caching,
            max_tokens_budget=self.config.max_tokens_budget,
        )
        
        self._aggregator = ResultAggregator(
            llm_client=self.llm,
        )
        
        return self._schema
    
    def load_data(self, data: list[dict], name: str = "inline_data") -> JsonSchema:
        """
        Load JSON data directly (not from file).
        
        Args:
            data: List of dictionaries
            name: Name for tracing
            
        Returns:
            JsonSchema with structure information
        """
        import json
        import tempfile
        
        # Write to temp file for schema analysis
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump(data, f)
            temp_path = f.name
        
        schema = self.load(temp_path)
        
        # Cache the data since it's already in memory
        self._data = data
        self._file_path = name  # Override for display
        
        return schema
    
    def analyze_schema(self) -> str:
        """
        Get a human-readable schema analysis.
        
        Returns:
            Formatted schema summary
        """
        if not self._schema:
            raise ValueError("No file loaded. Call load() first.")
        
        return self._schema.summary()
    
    def query(
        self,
        query: str,
        save_trace: bool = False,
        trace_dir: Optional[str] = None,
    ) -> QueryResult:
        """
        Query the loaded JSON data.
        
        Args:
            query: Natural language question
            save_trace: Whether to save execution trace to file
            trace_dir: Directory for trace files (uses config if not specified)
            
        Returns:
            QueryResult with answer, citations, and verification metadata
        """
        if not self._schema:
            raise ValueError("No file loaded. Call load() first.")
        
        start_time = time.time()
        
        # Create trace context
        with TraceContext(
            query=query,
            file_path=self._file_path,
            level=self.config.trace_level,
        ) as trace:
            try:
                # Phase 1: Plan query
                trace.add_entry(
                    TraceEventType.PLAN_START,
                    "Planning query execution",
                )
                
                plan = self._planner.plan(query)
                
                trace.add_entry(
                    TraceEventType.PLAN_END,
                    f"Plan created: {plan.intent.value}, {plan.estimated_chunks or '?'} chunks",
                    data=plan.to_dict(),
                )
                
                # Phase 2: Get chunks
                if self._data:
                    chunks = list(self._chunker.chunk_from_data(self._data))
                else:
                    chunks = list(self._chunker.chunk_from_file(self._file_path))
                
                trace.add_entry(
                    TraceEventType.INFO,
                    f"Created {len(chunks)} chunks from data",
                )
                
                # Phase 3: Execute
                exec_result = self._executor.execute(chunks, plan, trace)
                
                # Phase 4: Final aggregation (if not done in executor)
                if exec_result.aggregated_content:
                    answer = exec_result.aggregated_content
                else:
                    # Use aggregator for complex cases
                    agg_result = self._aggregator.aggregate(
                        exec_result.chunk_results,
                        plan,
                        trace,
                    )
                    answer = agg_result.content
                    exec_result.total_tokens += agg_result.tokens_used
                
                # Phase 5: Extract citations and verify (especially for exhaustive queries)
                citation_report = None
                verification = None
                
                if plan.intent == QueryIntent.EXHAUSTIVE_EXTRACT:
                    citation_report, verification = self._extract_and_verify_citations(
                        query=query,
                        answer=answer,
                        chunk_results=exec_result.chunk_results,
                        trace=trace,
                    )
                else:
                    # Basic verification for all queries
                    verification = self._basic_verification(answer, query)
                
                # Phase 6: Post-process answer (inject reference links, clean up)
                answer = self._post_process_answer(answer, query, verification)
                
                # Store answer in trace
                trace.answer = answer
                
                duration_ms = (time.time() - start_time) * 1000
                
                result = QueryResult(
                    answer=answer,
                    success=exec_result.success,
                    query=query,
                    file_path=self._file_path,
                    chunks_processed=exec_result.chunks_processed,
                    chunks_filtered=exec_result.chunks_filtered,
                    total_tokens=exec_result.total_tokens,
                    duration_ms=duration_ms,
                    trace=trace,
                    citation_report=citation_report,
                    verification=verification,
                )
                
            except Exception as e:
                trace.log_error(str(e))
                
                result = QueryResult(
                    answer=f"Query failed: {e}",
                    success=False,
                    query=query,
                    file_path=self._file_path,
                    error=str(e),
                    trace=trace,
                )
        
        # Save trace if requested
        if save_trace:
            trace_output = trace_dir or self.config.trace_output_dir or "./traces"
            result.trace.save(trace_output)
            
            # Also save citation report for exhaustive queries
            if result.citation_report:
                self._save_citation_report(result.citation_report, trace_output)
        
        return result
    
    def _extract_and_verify_citations(
        self,
        query: str,
        answer: str,
        chunk_results: list,
        trace: ExecutionTrace,
    ) -> tuple[CitationReport, VerificationResult]:
        """
        Extract citations from chunk results and verify them.
        
        This is the key function for exhaustive extraction queries.
        Like textbook-qa's page reference extraction, but for JSON records.
        """
        trace.add_entry(
            TraceEventType.INFO,
            "Extracting citations from chunk results",
        )
        
        # Extract citations from each chunk's response
        all_chunk_citations = []
        
        for result in chunk_results:
            if result.success and result.content and "NO_RELEVANT_CONTENT" not in result.content:
                chunk_citations = CitationExtractor.extract_from_response(
                    response=result.content,
                    chunk_index=result.chunk_index,
                    file_path=self._file_path,
                )
                all_chunk_citations.append(chunk_citations)
        
        # Merge and deduplicate
        merged_citations = CitationExtractor.merge_citations(
            all_chunk_citations,
            deduplicate=True,
        )
        
        # Build citation report
        citation_report = CitationReport(
            query=query,
            file_path=self._file_path,
        )
        
        for citation in merged_citations:
            citation_report.add_citation(citation)
        
        # Verify against original data if available
        if self._data:
            content_field = self._schema.content_field or "content"
            citation_report.verify(self._data, content_field)
        
        # Build verification result
        verification = VerificationResult(
            has_citations=len(merged_citations) > 0,
            citations_found=len(merged_citations),
            unique_authors=citation_report.unique_authors,
            positive_mentions=citation_report.sentiment_breakdown.get("positive", 0),
            negative_mentions=citation_report.sentiment_breakdown.get("negative", 0),
            neutral_mentions=citation_report.sentiment_breakdown.get("neutral", 0),
            reference_ids=citation_report.get_all_references(),
            issues=citation_report.verification_issues,
        )
        
        trace.add_entry(
            TraceEventType.INFO,
            f"Extracted {verification.citations_found} citations from {len(all_chunk_citations)} chunks",
            data=verification.to_dict(),
        )
        
        return citation_report, verification
    
    def _basic_verification(self, answer: str, query: str) -> VerificationResult:
        """
        Basic verification for non-exhaustive queries.
        
        Checks for quotes, references, and potential issues.
        """
        verification = VerificationResult()
        
        # Check for blockquotes (citations)
        quotes = re.findall(r'>\s*"?(.+?)"?\s*\n', answer)
        verification.citations_found = len(quotes)
        verification.has_citations = verification.citations_found > 0
        
        # Check for reference patterns
        ref_pattern = r'\[\d+\.\d+\]|\[ref:\s*\d+\]|\[chunk\s*\d+\]'
        refs = re.findall(ref_pattern, answer, re.IGNORECASE)
        verification.reference_ids = refs
        
        # Check for issues based on query
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["all", "every", "exhaustive", "complete"]):
            if verification.citations_found < 3:
                verification.issues.append("Query asked for exhaustive results but few citations found")
        
        if "who" in query_lower and not re.search(r'@\w+|\w+\s+said', answer):
            verification.issues.append("Query asked 'who' but no usernames found in answer")
        
        return verification
    
    def _post_process_answer(
        self,
        answer: str,
        query: str,
        verification: Optional[VerificationResult],
    ) -> str:
        """
        Post-process the answer to enhance it.
        
        Similar to textbook-qa's post-processing:
        - Clean up formatting
        - Inject reference links where missing
        - Add verification summary
        """
        # Clean up common LLM artifacts
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        
        # Add verification summary at the end if we have verification data
        if verification and verification.has_citations:
            summary = f"""

---

## 🔍 Verification Summary

| Metric | Value |
|--------|-------|
| Citations found | {verification.citations_found} |
| Unique contributors | {verification.unique_authors} |
| Positive mentions | {verification.positive_mentions} |
| Negative mentions | {verification.negative_mentions} |
| Neutral mentions | {verification.neutral_mentions} |
"""
            
            if verification.issues:
                summary += "\n**Issues:**\n"
                for issue in verification.issues:
                    summary += f"- ⚠️ {issue}\n"
            
            if verification.reference_ids:
                summary += f"\n**Reference IDs:** `{', '.join(verification.reference_ids[:10])}`"
                if len(verification.reference_ids) > 10:
                    summary += f" ... and {len(verification.reference_ids) - 10} more"
            
            answer += summary
        
        return answer
    
    def _save_citation_report(self, report: CitationReport, output_dir: str):
        """Save citation report to file."""
        from pathlib import Path
        import json
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save markdown version
        md_path = output_path / f"citations_{timestamp}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report.to_markdown())
        
        # Save JSON version for programmatic access
        json_path = output_path / f"citations_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2)
    
    def stream_query(
        self,
        query: str,
    ) -> Iterator[str]:
        """
        Stream query results as they're generated.
        
        Yields partial results during processing.
        Useful for UIs that want to show progress.
        
        Args:
            query: Natural language question
            
        Yields:
            Progress updates and partial results
        """
        if not self._schema:
            raise ValueError("No file loaded. Call load() first.")
        
        yield f"🔍 Analyzing query: {query}\n"
        
        # Plan
        plan = self._planner.plan(query)
        yield f"📋 Plan: {plan.intent.value} ({plan.reasoning})\n"
        
        # Get chunks
        if self._data:
            chunks = list(self._chunker.chunk_from_data(self._data))
        else:
            chunks = list(self._chunker.chunk_from_file(self._file_path))
        
        yield f"📦 Processing {len(chunks)} chunks...\n"
        
        # Process chunks
        results = []
        for i, chunk in enumerate(chunks):
            # Apply filter
            if plan.filter_criteria.keywords:
                text_lower = chunk.text_content.lower()
                if not any(kw.lower() in text_lower for kw in plan.filter_criteria.keywords):
                    continue
            
            yield f"  Processing chunk {i+1}/{len(chunks)}...\n"
            
            prompt = plan.chunk_prompt + "\n\n---\n\n" + chunk.to_llm_context()
            
            try:
                content, tokens = self.llm.complete(prompt)
                if "NO_RELEVANT_CONTENT" not in content:
                    results.append(content)
                    yield f"  ✓ Found relevant content\n"
            except Exception as e:
                yield f"  ✗ Error: {e}\n"
            
            # Check limit
            if plan.chunk_limit and len(results) >= plan.chunk_limit:
                break
        
        yield f"\n🔗 Aggregating {len(results)} results...\n"
        
        if not results:
            yield "\n❌ No relevant content found.\n"
            return
        
        # Aggregate
        findings = "\n\n---\n\n".join(results)
        prompt = plan.aggregate_prompt + "\n\n---\n\n" + findings
        
        try:
            answer, tokens = self.llm.complete(prompt)
            yield f"\n✅ Answer:\n\n{answer}\n"
        except Exception as e:
            yield f"\n❌ Aggregation failed: {e}\n"
    
    def get_sample(self, n: int = 5) -> list[dict]:
        """
        Get a sample of records from the data.
        
        Args:
            n: Number of records to return
            
        Returns:
            List of sample records
        """
        if self._data:
            return self._data[:n]
        
        if not self._file_path:
            raise ValueError("No file loaded.")
        
        import json
        with open(self._file_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data[:n]
        elif isinstance(data, dict) and "messages" in data:
            return data["messages"][:n]
        else:
            return [data]
    
    def clear_cache(self):
        """Clear the chunk result cache."""
        if self._executor:
            self._executor.clear_cache()
    
    def reset(self):
        """Reset all state."""
        self._file_path = None
        self._schema = None
        self._data = None
        self._chunker = None
        self._planner = None
        if self._executor:
            self._executor.clear_cache()
        self._executor = None
        self._aggregator = None

