"""
Result Aggregator: Combine chunk results into final answers.

Design Philosophy:
- Handle hierarchical aggregation for very large result sets
- Support different aggregation strategies per intent
- Maintain citations and provenance
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum

from .executor import ChunkResult, ExecutionResult, LLMClient
from .query_planner import QueryIntent, QueryPlan
from .trace import ExecutionTrace, TraceEventType


class AggregationStrategy(Enum):
    """How to aggregate chunk results."""
    CONCATENATE = "concatenate"   # Simple concatenation
    SUMMARIZE = "summarize"       # LLM-based summarization
    HIERARCHICAL = "hierarchical"  # Multi-level aggregation
    MERGE = "merge"               # Merge structured data (counts, lists)


@dataclass
class AggregationResult:
    """Result of aggregating chunk results."""
    content: str
    strategy_used: AggregationStrategy
    levels_of_aggregation: int = 1
    tokens_used: int = 0
    source_chunks: list[int] = field(default_factory=list)


class ResultAggregator:
    """
    Aggregate chunk results into final answers.
    
    Handles:
    - Simple concatenation for small result sets
    - LLM-based summarization for complex queries
    - Hierarchical aggregation for very large result sets
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        max_direct_aggregate_chars: int = 50_000,
        max_results_per_level: int = 10,
    ):
        """
        Args:
            llm_client: LLM client for summarization (optional)
            max_direct_aggregate_chars: Max chars before hierarchical aggregation
            max_results_per_level: Max results to aggregate at once
        """
        self.llm = llm_client
        self.max_direct_aggregate_chars = max_direct_aggregate_chars
        self.max_results_per_level = max_results_per_level
    
    def aggregate(
        self,
        results: list[ChunkResult],
        plan: QueryPlan,
        trace: Optional[ExecutionTrace] = None,
    ) -> AggregationResult:
        """
        Aggregate chunk results based on query intent.
        
        Args:
            results: List of chunk results
            plan: The query plan
            trace: Optional execution trace
            
        Returns:
            AggregationResult with final content
        """
        # Filter to successful, non-empty results
        valid_results = [
            r for r in results
            if r.success and r.content and "NO_RELEVANT_CONTENT" not in r.content
        ]
        
        if not valid_results:
            return AggregationResult(
                content="No relevant content found matching the query.",
                strategy_used=AggregationStrategy.CONCATENATE,
                source_chunks=[],
            )
        
        # Determine strategy based on intent and result size
        strategy = self._choose_strategy(valid_results, plan.intent)
        
        if trace:
            trace.add_entry(
                TraceEventType.AGGREGATE_START,
                f"Aggregating {len(valid_results)} results using {strategy.value}",
            )
        
        if strategy == AggregationStrategy.CONCATENATE:
            result = self._concatenate(valid_results)
        elif strategy == AggregationStrategy.MERGE:
            result = self._merge_structured(valid_results, plan.intent)
        elif strategy == AggregationStrategy.SUMMARIZE:
            result = self._summarize(valid_results, plan, trace)
        else:  # HIERARCHICAL
            result = self._hierarchical_aggregate(valid_results, plan, trace)
        
        if trace:
            trace.add_entry(
                TraceEventType.AGGREGATE_END,
                f"Aggregation complete: {len(result.content)} chars",
                tokens_used=result.tokens_used,
            )
        
        return result
    
    def _choose_strategy(
        self,
        results: list[ChunkResult],
        intent: QueryIntent,
    ) -> AggregationStrategy:
        """Choose aggregation strategy based on results and intent."""
        total_chars = sum(len(r.content) for r in results)
        
        # Count queries can use merge
        if intent == QueryIntent.COUNT:
            return AggregationStrategy.MERGE
        
        # Small result sets can be concatenated
        if total_chars < 5000 and len(results) <= 3:
            return AggregationStrategy.CONCATENATE
        
        # Large result sets need hierarchical
        if total_chars > self.max_direct_aggregate_chars or len(results) > self.max_results_per_level:
            if self.llm:
                return AggregationStrategy.HIERARCHICAL
            return AggregationStrategy.CONCATENATE
        
        # Default: summarize if LLM available
        if self.llm:
            return AggregationStrategy.SUMMARIZE
        
        return AggregationStrategy.CONCATENATE
    
    def _concatenate(self, results: list[ChunkResult]) -> AggregationResult:
        """Simple concatenation of results."""
        parts = []
        source_chunks = []
        
        for result in results:
            parts.append(f"**[Chunk {result.chunk_index + 1}]**\n{result.content}")
            source_chunks.append(result.chunk_index)
        
        return AggregationResult(
            content="\n\n---\n\n".join(parts),
            strategy_used=AggregationStrategy.CONCATENATE,
            source_chunks=source_chunks,
        )
    
    def _merge_structured(
        self,
        results: list[ChunkResult],
        intent: QueryIntent,
    ) -> AggregationResult:
        """Merge structured data (counts, lists, etc.)."""
        if intent == QueryIntent.COUNT:
            return self._merge_counts(results)
        
        # Default: just concatenate
        return self._concatenate(results)
    
    def _merge_counts(self, results: list[ChunkResult]) -> AggregationResult:
        """Merge count results."""
        import re
        
        total_count = 0
        examples = []
        source_chunks = []
        
        for result in results:
            source_chunks.append(result.chunk_index)
            
            # Try to extract count from "COUNT: X" format
            match = re.search(r'COUNT:\s*(\d+)', result.content)
            if match:
                total_count += int(match.group(1))
            
            # Collect examples (first few lines after count)
            lines = result.content.split('\n')
            for line in lines:
                if line.strip() and 'COUNT:' not in line:
                    examples.append(line.strip())
                    if len(examples) >= 5:
                        break
        
        content = f"**Total Count: {total_count}**\n\n"
        if examples:
            content += "Examples:\n" + "\n".join(f"- {e}" for e in examples[:5])
        
        return AggregationResult(
            content=content,
            strategy_used=AggregationStrategy.MERGE,
            source_chunks=source_chunks,
        )
    
    def _summarize(
        self,
        results: list[ChunkResult],
        plan: QueryPlan,
        trace: Optional[ExecutionTrace],
    ) -> AggregationResult:
        """LLM-based summarization of results."""
        if not self.llm:
            return self._concatenate(results)
        
        # Build input for LLM
        findings = []
        source_chunks = []
        
        for result in results:
            findings.append(f"[Chunk {result.chunk_index + 1}]\n{result.content}")
            source_chunks.append(result.chunk_index)
        
        findings_text = "\n\n---\n\n".join(findings)
        
        prompt = f"""{plan.aggregate_prompt}

FINDINGS FROM {len(results)} CHUNKS:

{findings_text}

Provide a comprehensive, well-organized answer. Cite chunk numbers when referencing specific information."""
        
        try:
            content, tokens = self.llm.complete(prompt)
            
            return AggregationResult(
                content=content,
                strategy_used=AggregationStrategy.SUMMARIZE,
                tokens_used=tokens,
                source_chunks=source_chunks,
            )
        except Exception as e:
            if trace:
                trace.log_error(f"Summarization failed: {e}")
            return self._concatenate(results)
    
    def _hierarchical_aggregate(
        self,
        results: list[ChunkResult],
        plan: QueryPlan,
        trace: Optional[ExecutionTrace],
    ) -> AggregationResult:
        """
        Multi-level hierarchical aggregation for large result sets.
        
        Groups results, summarizes each group, then summarizes the summaries.
        """
        if not self.llm:
            return self._concatenate(results)
        
        total_tokens = 0
        source_chunks = [r.chunk_index for r in results]
        levels = 0
        
        # Group results
        groups = []
        for i in range(0, len(results), self.max_results_per_level):
            groups.append(results[i:i + self.max_results_per_level])
        
        if trace:
            trace.add_entry(
                TraceEventType.INFO,
                f"Hierarchical aggregation: {len(results)} results → {len(groups)} groups",
            )
        
        # Level 1: Summarize each group
        level1_summaries = []
        for i, group in enumerate(groups):
            findings = [f"[Chunk {r.chunk_index + 1}]\n{r.content}" for r in group]
            findings_text = "\n\n---\n\n".join(findings)
            
            prompt = f"""Summarize these findings for the query: {plan.query}

{findings_text}

Provide a concise summary preserving key information."""
            
            try:
                content, tokens = self.llm.complete(prompt)
                total_tokens += tokens
                level1_summaries.append(content)
            except Exception as e:
                level1_summaries.append(f"Group {i+1} summary failed: {e}")
        
        levels = 1
        
        # If still too many summaries, aggregate again
        while len(level1_summaries) > self.max_results_per_level:
            new_summaries = []
            for i in range(0, len(level1_summaries), self.max_results_per_level):
                batch = level1_summaries[i:i + self.max_results_per_level]
                combined = "\n\n---\n\n".join(batch)
                
                prompt = f"""Combine these summaries for the query: {plan.query}

{combined}

Provide a unified summary."""
                
                try:
                    content, tokens = self.llm.complete(prompt)
                    total_tokens += tokens
                    new_summaries.append(content)
                except Exception as e:
                    new_summaries.append(f"Summary aggregation failed: {e}")
            
            level1_summaries = new_summaries
            levels += 1
        
        # Final aggregation
        if len(level1_summaries) == 1:
            final_content = level1_summaries[0]
        else:
            combined = "\n\n---\n\n".join(level1_summaries)
            
            prompt = f"""{plan.aggregate_prompt}

AGGREGATED SUMMARIES:

{combined}

Provide the final, comprehensive answer to: {plan.query}"""
            
            try:
                final_content, tokens = self.llm.complete(prompt)
                total_tokens += tokens
            except Exception as e:
                final_content = f"Final aggregation failed: {e}\n\n{combined}"
            
            levels += 1
        
        return AggregationResult(
            content=final_content,
            strategy_used=AggregationStrategy.HIERARCHICAL,
            levels_of_aggregation=levels,
            tokens_used=total_tokens,
            source_chunks=source_chunks,
        )

