"""
Chunk Executor: Process chunks through LLM with filtering and caching.

Design Philosophy:
- Apply filters before LLM calls to reduce costs
- Cache results for repeated queries
- Track tokens and costs precisely
- Support parallel execution
"""

import os
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .chunker import Chunk
from .query_planner import QueryPlan, FilterCriteria
from .schema import JsonSchema
from .trace import ExecutionTrace, TraceEventType


@dataclass
class ChunkResult:
    """Result from processing a single chunk."""
    chunk_index: int
    success: bool
    content: str
    
    # Metadata
    tokens_used: int = 0
    duration_ms: float = 0
    was_cached: bool = False
    was_filtered: bool = False  # True if chunk was skipped due to filter
    
    # Original chunk reference
    chunk_metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serialize for tracing."""
        return {
            "chunk_index": self.chunk_index,
            "success": self.success,
            "content_preview": self.content[:200] if self.content else "",
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
            "was_cached": self.was_cached,
            "was_filtered": self.was_filtered,
        }


@dataclass
class ExecutionResult:
    """Complete result from executing a query plan."""
    query: str
    success: bool
    
    # Results from chunks
    chunk_results: list[ChunkResult] = field(default_factory=list)
    
    # Aggregated content
    aggregated_content: str = ""
    
    # Summary stats
    total_chunks: int = 0
    chunks_processed: int = 0
    chunks_filtered: int = 0
    chunks_cached: int = 0
    total_tokens: int = 0
    total_duration_ms: float = 0
    
    # Error info
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Serialize for tracing."""
        return {
            "query": self.query,
            "success": self.success,
            "total_chunks": self.total_chunks,
            "chunks_processed": self.chunks_processed,
            "chunks_filtered": self.chunks_filtered,
            "chunks_cached": self.chunks_cached,
            "total_tokens": self.total_tokens,
            "total_duration_ms": self.total_duration_ms,
            "error": self.error,
        }


class LLMClient:
    """
    Simple LLM client abstraction.
    
    Wraps Anthropic/OpenAI/Z.AI APIs with consistent interface.
    """
    
    # Z.AI model mappings
    ZAI_MODEL_MAPPING = {
        "glm-4.7": "glm-4.7",
        "glm-4.5-air": "glm-4.5-air",
        "glm-4": "glm-4.7",
        "glm-fast": "glm-4.5-air",
    }
    
    def __init__(
        self,
        model: str,
        provider: str = "anthropic",
        api_key: Optional[str] = None,
        timeout: int = 120,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.provider = provider
        self.timeout = timeout
        self.base_url = base_url
        
        if provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY required")
            
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package required: pip install anthropic")
        
        elif provider == "zai":
            # Z.AI uses Anthropic-compatible API
            self.api_key = api_key or os.getenv("Z_AI_API_KEY")
            if not self.api_key:
                raise ValueError("Z_AI_API_KEY required")
            
            try:
                import anthropic
                self.client = anthropic.Anthropic(
                    api_key=self.api_key,
                    base_url=base_url or "https://api.z.ai/api/anthropic",
                    timeout=timeout,
                )
                # Map model name if needed
                self.model = self.ZAI_MODEL_MAPPING.get(model, model)
            except ImportError:
                raise ImportError("anthropic package required: pip install anthropic")
        
        elif provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY required")
            
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> tuple[str, int]:
        """
        Call LLM and return (response, tokens_used).
        """
        if self.provider in ["anthropic", "zai"]:
            # Both Anthropic and Z.AI use the same API format
            return self._call_anthropic(prompt, system_prompt, max_tokens)
        else:
            return self._call_openai(prompt, system_prompt, max_tokens)
    
    def _call_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
    ) -> tuple[str, int]:
        """Call Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "You are a helpful data analyst.",
            messages=[{"role": "user", "content": prompt}],
        )
        
        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        
        return content, tokens
    
    def _call_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
    ) -> tuple[str, int]:
        """Call OpenAI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )
        
        content = response.choices[0].message.content
        tokens = response.usage.prompt_tokens + response.usage.completion_tokens
        
        return content, tokens


class ChunkExecutor:
    """
    Execute query plan against chunks.
    
    Responsibilities:
    - Filter chunks based on criteria
    - Process chunks through LLM
    - Cache results
    - Aggregate final result
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        schema: JsonSchema,
        max_parallel: int = 4,
        cache_enabled: bool = True,
        max_tokens_budget: Optional[int] = None,
    ):
        self.llm = llm_client
        self.schema = schema
        self.max_parallel = max_parallel
        self.cache_enabled = cache_enabled
        self.max_tokens_budget = max_tokens_budget
        
        self._cache: dict[str, ChunkResult] = {}
        self._tokens_used = 0
    
    def execute(
        self,
        chunks: list[Chunk],
        plan: QueryPlan,
        trace: Optional[ExecutionTrace] = None,
    ) -> ExecutionResult:
        """
        Execute the query plan against all chunks.
        
        Args:
            chunks: List of chunks to process
            plan: Query execution plan
            trace: Optional trace for logging
            
        Returns:
            ExecutionResult with all chunk results and aggregation
        """
        start_time = time.time()
        self._tokens_used = 0
        
        result = ExecutionResult(
            query=plan.query,
            success=True,
            total_chunks=len(chunks),
        )
        
        try:
            # Phase 1: Filter chunks
            filtered_chunks = self._filter_chunks(chunks, plan.filter_criteria, trace)
            result.chunks_filtered = len(chunks) - len(filtered_chunks)
            
            if trace:
                trace.add_entry(
                    TraceEventType.INFO,
                    f"Filtered {result.chunks_filtered} chunks, {len(filtered_chunks)} remaining",
                )
            
            # Check chunk limit
            if plan.chunk_limit and len(filtered_chunks) > plan.chunk_limit:
                filtered_chunks = filtered_chunks[:plan.chunk_limit]
                if trace:
                    trace.add_entry(
                        TraceEventType.WARNING,
                        f"Limiting to {plan.chunk_limit} chunks",
                    )
            
            # Phase 2: Process chunks
            if plan.parallel_ok and self.max_parallel > 1:
                chunk_results = self._process_parallel(
                    filtered_chunks, plan, trace
                )
            else:
                chunk_results = self._process_sequential(
                    filtered_chunks, plan, trace
                )
            
            result.chunk_results = chunk_results
            result.chunks_processed = len([r for r in chunk_results if r.success and not r.was_filtered])
            result.chunks_cached = len([r for r in chunk_results if r.was_cached])
            result.total_tokens = self._tokens_used
            
            # Check for budget exceeded
            if self.max_tokens_budget and self._tokens_used >= self.max_tokens_budget:
                if trace:
                    trace.add_entry(
                        TraceEventType.WARNING,
                        f"Token budget exceeded: {self._tokens_used}/{self.max_tokens_budget}",
                    )
            
            # Phase 3: Aggregate results
            relevant_results = [r for r in chunk_results if r.success and r.content and "NO_RELEVANT_CONTENT" not in r.content]
            
            if relevant_results:
                result.aggregated_content = self._aggregate_results(
                    relevant_results, plan, trace
                )
            else:
                result.aggregated_content = "No relevant content found matching the query."
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            if trace:
                trace.log_error(str(e))
        
        result.total_duration_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _filter_chunks(
        self,
        chunks: list[Chunk],
        criteria: FilterCriteria,
        trace: Optional[ExecutionTrace],
    ) -> list[Chunk]:
        """Filter chunks based on criteria without LLM calls."""
        if not criteria.keywords and not criteria.channel_filter and not criteria.author_filter:
            return chunks
        
        filtered = []
        
        for chunk in chunks:
            # Quick text-based filtering
            text_lower = chunk.text_content.lower()
            
            # Keyword filter
            if criteria.keywords:
                if not any(kw.lower() in text_lower for kw in criteria.keywords):
                    continue
            
            # Channel filter
            if criteria.channel_filter:
                if criteria.channel_filter.lower() not in text_lower:
                    continue
            
            # Author filter
            if criteria.author_filter:
                if criteria.author_filter.lower() not in text_lower:
                    continue
            
            filtered.append(chunk)
        
        return filtered
    
    def _process_parallel(
        self,
        chunks: list[Chunk],
        plan: QueryPlan,
        trace: Optional[ExecutionTrace],
    ) -> list[ChunkResult]:
        """Process chunks in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            futures = {
                executor.submit(self._process_chunk, chunk, plan, trace): chunk
                for chunk in chunks
            }
            
            for future in as_completed(futures):
                chunk = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(ChunkResult(
                        chunk_index=chunk.index,
                        success=False,
                        content=f"Error: {e}",
                    ))
        
        # Sort by chunk index
        results.sort(key=lambda r: r.chunk_index)
        return results
    
    def _process_sequential(
        self,
        chunks: list[Chunk],
        plan: QueryPlan,
        trace: Optional[ExecutionTrace],
    ) -> list[ChunkResult]:
        """Process chunks sequentially."""
        results = []
        
        for chunk in chunks:
            # Check budget
            if self.max_tokens_budget and self._tokens_used >= self.max_tokens_budget:
                results.append(ChunkResult(
                    chunk_index=chunk.index,
                    success=False,
                    content="Budget exceeded",
                    was_filtered=True,
                ))
                continue
            
            result = self._process_chunk(chunk, plan, trace)
            results.append(result)
        
        return results
    
    def _process_chunk(
        self,
        chunk: Chunk,
        plan: QueryPlan,
        trace: Optional[ExecutionTrace],
    ) -> ChunkResult:
        """Process a single chunk through LLM."""
        start_time = time.time()
        
        # Check cache
        cache_key = self._cache_key(chunk, plan.query)
        if self.cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            if trace:
                trace.add_entry(
                    TraceEventType.CHUNK_SKIP,
                    f"Chunk {chunk.index} served from cache",
                )
            return ChunkResult(
                chunk_index=chunk.index,
                success=True,
                content=cached.content,
                was_cached=True,
                chunk_metadata=chunk.to_dict(),
            )
        
        # Build prompt
        prompt = plan.chunk_prompt + "\n\n---\n\n" + chunk.to_llm_context()
        
        if trace:
            trace.add_entry(
                TraceEventType.CHUNK_START,
                f"Processing chunk {chunk.index} ({chunk.record_count} records)",
                data={"chunk": chunk.to_dict()},
            )
        
        try:
            # Call LLM
            content, tokens = self.llm.complete(prompt)
            self._tokens_used += tokens
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = ChunkResult(
                chunk_index=chunk.index,
                success=True,
                content=content,
                tokens_used=tokens,
                duration_ms=duration_ms,
                chunk_metadata=chunk.to_dict(),
            )
            
            # Cache result
            if self.cache_enabled:
                self._cache[cache_key] = result
            
            if trace:
                trace.add_entry(
                    TraceEventType.CHUNK_END,
                    f"Chunk {chunk.index} processed",
                    data={"response_preview": content[:200]},
                    duration_ms=duration_ms,
                    tokens_used=tokens,
                )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            if trace:
                trace.add_entry(
                    TraceEventType.LLM_CALL_ERROR,
                    f"Chunk {chunk.index} failed: {e}",
                    duration_ms=duration_ms,
                )
            
            return ChunkResult(
                chunk_index=chunk.index,
                success=False,
                content=f"Error: {e}",
                duration_ms=duration_ms,
            )
    
    def _aggregate_results(
        self,
        results: list[ChunkResult],
        plan: QueryPlan,
        trace: Optional[ExecutionTrace],
    ) -> str:
        """Aggregate chunk results into final answer."""
        if trace:
            trace.add_entry(
                TraceEventType.AGGREGATE_START,
                f"Aggregating {len(results)} chunk results",
            )
        
        start_time = time.time()
        
        # Build aggregation input
        findings = []
        for result in results:
            findings.append(f"[Chunk {result.chunk_index + 1}]\n{result.content}")
        
        findings_text = "\n\n---\n\n".join(findings)
        
        # Aggregation prompt
        prompt = plan.aggregate_prompt + "\n\n---\n\n" + findings_text
        
        try:
            content, tokens = self.llm.complete(prompt)
            self._tokens_used += tokens
            
            duration_ms = (time.time() - start_time) * 1000
            
            if trace:
                trace.add_entry(
                    TraceEventType.AGGREGATE_END,
                    f"Aggregation complete",
                    data={"answer_preview": content[:200]},
                    duration_ms=duration_ms,
                    tokens_used=tokens,
                )
            
            return content
            
        except Exception as e:
            if trace:
                trace.log_error(f"Aggregation failed: {e}")
            
            # Fallback: return concatenated findings
            return f"Aggregation failed. Raw findings:\n\n{findings_text}"
    
    def _cache_key(self, chunk: Chunk, query: str) -> str:
        """Generate cache key for chunk + query."""
        content = f"{chunk.index}:{chunk.text_content[:1000]}:{query}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the result cache."""
        self._cache.clear()

