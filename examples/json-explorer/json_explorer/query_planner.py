"""
Query Planner: Decompose natural language queries into execution plans.

Design Philosophy:
- Analyze query intent before processing
- Create deterministic execution plans
- Support filtering to minimize chunks processed
- Plans are serializable for tracing
"""

import re
from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from enum import Enum

from .schema import JsonSchema, JsonFormat


class QueryIntent(Enum):
    """Types of query intents we can detect."""
    SEARCH = "search"                    # Find specific content
    SUMMARIZE = "summarize"              # Summarize topics/themes
    COUNT = "count"                      # Count occurrences
    ANALYZE = "analyze"                  # Deep analysis
    EXTRACT = "extract"                  # Extract specific data
    COMPARE = "compare"                  # Compare different parts
    TIMELINE = "timeline"                # Temporal analysis
    EXHAUSTIVE_EXTRACT = "exhaustive"    # Find EVERY single mention with full context and citations


@dataclass
class FilterCriteria:
    """Criteria for filtering records before LLM processing."""
    keywords: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    field_filters: dict[str, Any] = field(default_factory=dict)  # field_name: value
    date_range: Optional[tuple[str, str]] = None  # (start, end)
    author_filter: Optional[str] = None
    channel_filter: Optional[str] = None
    
    def matches(self, record: dict, content_field: Optional[str] = None) -> bool:
        """Check if a record matches the filter criteria."""
        # Keyword matching
        if self.keywords:
            content = ""
            if content_field and content_field in record:
                content = str(record[content_field]).lower()
            else:
                content = str(record).lower()
            
            if not any(kw.lower() in content for kw in self.keywords):
                return False
        
        # Exclude keywords
        if self.exclude_keywords:
            content = str(record).lower()
            if any(kw.lower() in content for kw in self.exclude_keywords):
                return False
        
        # Field filters
        for field_name, expected in self.field_filters.items():
            if field_name in record:
                if record[field_name] != expected:
                    return False
        
        return True
    
    def to_dict(self) -> dict:
        """Serialize for tracing."""
        return {
            "keywords": self.keywords,
            "exclude_keywords": self.exclude_keywords,
            "field_filters": self.field_filters,
            "date_range": self.date_range,
            "author_filter": self.author_filter,
            "channel_filter": self.channel_filter,
        }


@dataclass
class QueryPlan:
    """
    Execution plan for a query.
    
    Created by QueryPlanner based on query analysis.
    """
    query: str
    intent: QueryIntent
    
    # What to search for
    filter_criteria: FilterCriteria = field(default_factory=FilterCriteria)
    
    # How to process
    require_full_scan: bool = False  # Must process all chunks
    chunk_limit: Optional[int] = None  # Max chunks to process
    parallel_ok: bool = True  # Safe to parallelize
    
    # LLM prompts
    chunk_prompt: str = ""  # Prompt for each chunk
    aggregate_prompt: str = ""  # Prompt for aggregation
    
    # Estimated cost
    estimated_chunks: Optional[int] = None
    estimated_tokens: Optional[int] = None
    
    # Metadata for tracing
    reasoning: str = ""  # Why we chose this plan
    
    def to_dict(self) -> dict:
        """Serialize for tracing."""
        return {
            "query": self.query,
            "intent": self.intent.value,
            "filter_criteria": self.filter_criteria.to_dict(),
            "require_full_scan": self.require_full_scan,
            "chunk_limit": self.chunk_limit,
            "parallel_ok": self.parallel_ok,
            "estimated_chunks": self.estimated_chunks,
            "estimated_tokens": self.estimated_tokens,
            "reasoning": self.reasoning,
        }


class QueryPlanner:
    """
    Plan query execution based on query intent and schema.
    
    Responsibilities:
    - Detect query intent (search, summarize, count, etc.)
    - Extract keywords and filters
    - Generate appropriate prompts
    - Estimate resource usage
    """
    
    def __init__(self, schema: JsonSchema):
        self.schema = schema
    
    def plan(self, query: str) -> QueryPlan:
        """
        Create an execution plan for a query.
        
        Args:
            query: Natural language query
            
        Returns:
            QueryPlan with execution details
        """
        # Detect intent
        intent = self._detect_intent(query)
        
        # Extract filter criteria
        filter_criteria = self._extract_filters(query)
        
        # Determine if full scan is required
        require_full_scan = self._requires_full_scan(intent, filter_criteria)
        
        # Generate prompts
        chunk_prompt = self._generate_chunk_prompt(query, intent)
        aggregate_prompt = self._generate_aggregate_prompt(query, intent)
        
        # Estimate costs
        estimated_chunks = self._estimate_chunks(filter_criteria)
        estimated_tokens = estimated_chunks * 5000 if estimated_chunks else None
        
        # Build reasoning
        reasoning = self._build_reasoning(intent, filter_criteria, require_full_scan)
        
        return QueryPlan(
            query=query,
            intent=intent,
            filter_criteria=filter_criteria,
            require_full_scan=require_full_scan,
            chunk_limit=100 if not require_full_scan else None,
            parallel_ok=intent != QueryIntent.TIMELINE,
            chunk_prompt=chunk_prompt,
            aggregate_prompt=aggregate_prompt,
            estimated_chunks=estimated_chunks,
            estimated_tokens=estimated_tokens,
            reasoning=reasoning,
        )
    
    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the primary intent of the query."""
        query_lower = query.lower()
        
        # EXHAUSTIVE extraction indicators - for getting EVERY mention with citations
        # Triggers: "what are people saying about X", "everything about X", "all mentions of X"
        exhaustive_indicators = [
            "what are people saying",
            "everything about",
            "all mentions",
            "every mention",
            "everything said about",
            "all the discussions",
            "comprehensive",
            "exhaustive",
            "each instance",
            "every single",
            "all instances",
            "cite all",
            "full context",
        ]
        if any(ind in query_lower for ind in exhaustive_indicators):
            return QueryIntent.EXHAUSTIVE_EXTRACT
        
        # Also trigger exhaustive for patterns like "what do they say about X"
        opinion_patterns = [
            r"what (?:do|are|did) (?:people|they|users?|members?) (?:say|think|mention)",
            r"opinions? (?:on|about|regarding)",
            r"thoughts? (?:on|about|regarding)",
            r"feedback (?:on|about|regarding)",
            r"discussion (?:on|about|regarding)",
        ]
        for pattern in opinion_patterns:
            if re.search(pattern, query_lower):
                return QueryIntent.EXHAUSTIVE_EXTRACT
        
        # Search indicators
        search_indicators = ["find", "search", "look for", "where", "who said", "mentions"]
        if any(ind in query_lower for ind in search_indicators):
            return QueryIntent.SEARCH
        
        # Count indicators
        count_indicators = ["how many", "count", "number of", "total"]
        if any(ind in query_lower for ind in count_indicators):
            return QueryIntent.COUNT
        
        # Timeline indicators
        timeline_indicators = ["when", "timeline", "over time", "history", "chronological"]
        if any(ind in query_lower for ind in timeline_indicators):
            return QueryIntent.TIMELINE
        
        # Compare indicators
        compare_indicators = ["compare", "difference", "versus", "vs", "between"]
        if any(ind in query_lower for ind in compare_indicators):
            return QueryIntent.COMPARE
        
        # Extract indicators
        extract_indicators = ["extract", "list", "get all", "show me all"]
        if any(ind in query_lower for ind in extract_indicators):
            return QueryIntent.EXTRACT
        
        # Summarize is default for open-ended questions
        summarize_indicators = ["summarize", "summary", "main topics", "what about", "discuss"]
        if any(ind in query_lower for ind in summarize_indicators):
            return QueryIntent.SUMMARIZE
        
        # Default to analysis for complex questions
        if "?" in query or query_lower.startswith(("what", "why", "how")):
            return QueryIntent.ANALYZE
        
        return QueryIntent.SUMMARIZE
    
    def _extract_filters(self, query: str) -> FilterCriteria:
        """Extract filter criteria from query."""
        criteria = FilterCriteria()
        query_lower = query.lower()
        
        # Extract quoted phrases as exact keywords
        quoted = re.findall(r'"([^"]+)"', query)
        criteria.keywords.extend(quoted)
        
        # Extract keywords after "about", "regarding", "mentioning"
        about_match = re.search(r'(?:about|regarding|mentioning|related to)\s+(\w+(?:\s+\w+)?)', query_lower)
        if about_match:
            criteria.keywords.append(about_match.group(1))
        
        # Extract channel filter for Discord
        if self.schema.format == JsonFormat.DISCORD:
            channel_match = re.search(r'(?:in|from|channel)\s+#?(\w+)', query_lower)
            if channel_match:
                criteria.channel_filter = channel_match.group(1)
        
        # Extract author filter
        author_match = re.search(r'(?:by|from user|user)\s+@?(\w+)', query_lower)
        if author_match:
            criteria.author_filter = author_match.group(1)
        
        # Extract time-related filters
        time_keywords = ["today", "yesterday", "last week", "last month", "this week"]
        for kw in time_keywords:
            if kw in query_lower:
                # Would need date calculation - simplified for now
                break
        
        # Extract any obvious keywords (nouns that aren't stop words)
        if not criteria.keywords:
            words = query_lower.split()
            stop_words = {
                "the", "a", "an", "is", "are", "was", "were", "be", "been",
                "what", "where", "when", "who", "how", "why", "which",
                "about", "in", "on", "at", "to", "for", "of", "with",
                "and", "or", "but", "not", "all", "any", "some",
                "do", "does", "did", "can", "could", "would", "should",
                "this", "that", "these", "those", "it", "its",
            }
            potential_keywords = [w for w in words if w not in stop_words and len(w) > 3]
            criteria.keywords.extend(potential_keywords[:3])  # Take top 3
        
        return criteria
    
    def _requires_full_scan(self, intent: QueryIntent, criteria: FilterCriteria) -> bool:
        """Determine if query requires scanning all chunks."""
        # Count always needs full scan
        if intent == QueryIntent.COUNT:
            return True
        
        # Exhaustive extraction MUST scan all chunks to find every mention
        if intent == QueryIntent.EXHAUSTIVE_EXTRACT:
            return True
        
        # Compare typically needs full scan
        if intent == QueryIntent.COMPARE:
            return True
        
        # If no filters, we need full scan for comprehensive answer
        if not criteria.keywords and not criteria.channel_filter and not criteria.author_filter:
            return True
        
        return False
    
    def _generate_chunk_prompt(self, query: str, intent: QueryIntent) -> str:
        """Generate the prompt template for chunk processing."""
        base_context = f"""You are analyzing a portion of a JSON data export.
Format: {self.schema.format.value}
Content field: {self.schema.content_field or 'N/A'}

USER QUERY: {query}

"""
        
        if intent == QueryIntent.SEARCH:
            return base_context + """TASK: Search this chunk for content relevant to the query.

If you find relevant content:
- Quote the exact relevant parts
- Note who said it and when (if available)
- Explain why it's relevant

If nothing relevant is found, respond with "NO_RELEVANT_CONTENT"
"""
        
        elif intent == QueryIntent.COUNT:
            return base_context + """TASK: Count items matching the query criteria in this chunk.

Provide:
- Count of matching items
- Brief examples (up to 3)

Format: COUNT: [number]
"""
        
        elif intent == QueryIntent.SUMMARIZE:
            return base_context + """TASK: Summarize content in this chunk related to the query.

Provide:
- Key themes or topics discussed
- Notable quotes or statements
- Main conclusions or decisions

Keep summary concise but comprehensive.
"""
        
        elif intent == QueryIntent.TIMELINE:
            return base_context + """TASK: Extract timeline information related to the query.

For each relevant event:
- Date/time
- What happened
- Who was involved

Format chronologically.
"""
        
        elif intent == QueryIntent.EXTRACT:
            return base_context + """TASK: Extract all items matching the query criteria.

List each matching item with:
- The content itself
- Source/author
- Timestamp

Format as a list.
"""
        
        elif intent == QueryIntent.EXHAUSTIVE_EXTRACT:
            return base_context + """TASK: Find EVERY SINGLE mention related to the query in this chunk.
This is an exhaustive extraction - we need COMPLETE coverage.

For EACH relevant mention, you MUST provide:

1. **EXACT QUOTE**: The verbatim text (use > blockquote)
2. **CITATION**: 
   - Author/username (who said it)
   - Timestamp (when they said it)
   - Message ID or record index (if available)
   - Channel/thread name (if applicable)
3. **CONTEXT**: What was being discussed before/after
4. **SENTIMENT**: Positive/negative/neutral opinion
5. **IMPLICATIONS**: What this statement means or suggests

FORMAT each finding as:

### Finding N

> "[Exact quote from the source]"

**Source:** @username | timestamp | channel/thread
**Record Index:** chunk_index.record_index (for verification)
**Context:** [What was the surrounding discussion]
**Sentiment:** [Positive/Negative/Neutral/Mixed]
**Key Insight:** [What this tells us]

---

CRITICAL REQUIREMENTS:
- Do NOT summarize - extract EVERY instance
- Do NOT skip minor mentions - capture everything
- Include partial mentions and implications
- Provide enough context to verify the source

If nothing relevant is found, respond with "NO_RELEVANT_CONTENT"
"""
        
        else:  # ANALYZE or default
            return base_context + """TASK: Analyze this chunk for insights related to the query.

Provide:
- Key findings
- Relevant evidence or quotes
- Any patterns observed

Be thorough but focused on the query.
"""
    
    def _generate_aggregate_prompt(self, query: str, intent: QueryIntent) -> str:
        """Generate the prompt for aggregating chunk results."""
        base = f"""You are synthesizing findings from multiple chunks of data to answer:

QUERY: {query}

Below are the findings from each chunk. Synthesize them into a comprehensive answer.

"""
        
        if intent == QueryIntent.COUNT:
            return base + """Sum up all counts and provide the total.
List example items from across all chunks.
"""
        
        elif intent == QueryIntent.TIMELINE:
            return base + """Merge all timeline entries chronologically.
Remove duplicates and create a cohesive timeline.
"""
        
        elif intent == QueryIntent.COMPARE:
            return base + """Identify and highlight the key differences and similarities.
Organize by comparison dimension.
"""
        
        elif intent == QueryIntent.EXHAUSTIVE_EXTRACT:
            return base + """This is an EXHAUSTIVE extraction. Your job is to compile ALL findings.

DO NOT summarize or consolidate. PRESERVE every individual citation.

Structure your response as:

## 📊 Summary Statistics
- Total mentions found: [N]
- Unique contributors: [N]
- Sentiment breakdown: Positive [N], Negative [N], Neutral [N]

## 🔍 All Citations (Chronological)

[Include EVERY finding from the chunks, organized chronologically]

### Citation 1
> "[Exact quote]"
**Source:** @username | timestamp | location
**Record Ref:** [chunk.record for verification]
**Sentiment:** [sentiment]
**Key Point:** [what this means]

[Continue for ALL citations...]

## 📈 Analysis

### Common Themes
[Group the citations by theme]

### Notable Opinions
[Highlight particularly insightful or influential statements]

### Contradictions or Debates
[Note where people disagree]

## 🔗 Verification References
[List all record references for independent verification]

CRITICAL: Do NOT omit any citations. Include everything found.
"""
        
        else:
            return base + """Synthesize all findings into a coherent answer.
- Identify common themes across chunks
- Highlight key insights
- Note any contradictions
- Cite specific sources when relevant
"""
    
    def _estimate_chunks(self, criteria: FilterCriteria) -> Optional[int]:
        """Estimate number of chunks that will be processed."""
        if not self.schema.total_records:
            return None
        
        # Rough estimate based on filters
        if criteria.keywords:
            # Assume keywords filter out ~90% of content
            estimated_records = self.schema.total_records * 0.1
        elif criteria.channel_filter or criteria.author_filter:
            # Assume field filters reduce by ~80%
            estimated_records = self.schema.total_records * 0.2
        else:
            estimated_records = self.schema.total_records
        
        # Assume ~50 records per chunk (configurable)
        estimated_chunks = max(1, int(estimated_records / 50))
        
        return estimated_chunks
    
    def _build_reasoning(
        self,
        intent: QueryIntent,
        criteria: FilterCriteria,
        require_full_scan: bool,
    ) -> str:
        """Build explanation of planning decisions."""
        parts = [
            f"Detected intent: {intent.value}",
        ]
        
        if criteria.keywords:
            parts.append(f"Keywords to search: {', '.join(criteria.keywords)}")
        
        if criteria.channel_filter:
            parts.append(f"Filtering to channel: {criteria.channel_filter}")
        
        if criteria.author_filter:
            parts.append(f"Filtering to author: {criteria.author_filter}")
        
        if require_full_scan:
            parts.append("Full scan required for comprehensive answer")
        else:
            parts.append("Can use keyword filtering to reduce chunks")
        
        return "; ".join(parts)

