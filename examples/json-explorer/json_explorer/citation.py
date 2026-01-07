"""
Citation tracking and verification for JSON data sources.

Provides a citation system similar to textbook-qa's page references,
but adapted for JSON records (Discord messages, chat logs, etc.).

Design Philosophy:
- Every finding should be traceable to its source
- Citations must be verifiable independently
- Full context preserved for audit
"""

import re
import json
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class Sentiment(Enum):
    """Sentiment classification for a citation."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class Citation:
    """
    A single citable reference from the JSON data.
    
    Contains all information needed to verify the source.
    """
    # Core content
    quote: str                          # Exact text quoted
    
    # Source identification
    author: Optional[str] = None        # Who said it (username, etc.)
    timestamp: Optional[str] = None     # When it was said
    channel: Optional[str] = None       # Channel/thread name
    message_id: Optional[str] = None    # Unique message ID if available
    
    # Location in data
    chunk_index: int = 0                # Which chunk this came from
    record_index: int = 0               # Which record within the chunk
    file_path: Optional[str] = None     # Source file
    
    # Context
    context_before: Optional[str] = None  # What was said before
    context_after: Optional[str] = None   # What was said after
    
    # Analysis
    sentiment: Sentiment = Sentiment.NEUTRAL
    key_insight: Optional[str] = None    # What this means
    relevance_score: float = 0.0         # How relevant (0-1)
    
    def __post_init__(self):
        """Validate and clean citation."""
        # Clean up quote
        self.quote = self.quote.strip()
        if self.quote.startswith('"') and self.quote.endswith('"'):
            self.quote = self.quote[1:-1]
    
    @property
    def reference_id(self) -> str:
        """
        Generate a unique reference ID for this citation.
        
        Format: chunk_index.record_index (e.g., "3.15")
        This can be used to look up the original record.
        """
        return f"{self.chunk_index}.{self.record_index}"
    
    @property 
    def source_line(self) -> str:
        """Format source info as a single line for display."""
        parts = []
        if self.author:
            parts.append(f"@{self.author}")
        if self.timestamp:
            parts.append(self.timestamp)
        if self.channel:
            parts.append(f"#{self.channel}")
        return " | ".join(parts) if parts else "Unknown source"
    
    def to_markdown(self) -> str:
        """Format citation as markdown for display."""
        lines = [
            f"> \"{self.quote}\"",
            "",
            f"**Source:** {self.source_line}",
            f"**Ref:** `{self.reference_id}`",
        ]
        
        if self.sentiment != Sentiment.NEUTRAL:
            lines.append(f"**Sentiment:** {self.sentiment.value.capitalize()}")
        
        if self.key_insight:
            lines.append(f"**Insight:** {self.key_insight}")
        
        if self.context_before or self.context_after:
            context_parts = []
            if self.context_before:
                context_parts.append(f"Before: {self.context_before[:100]}...")
            if self.context_after:
                context_parts.append(f"After: {self.context_after[:100]}...")
            lines.append(f"**Context:** {'; '.join(context_parts)}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Serialize for storage/tracing."""
        return {
            "quote": self.quote,
            "author": self.author,
            "timestamp": self.timestamp,
            "channel": self.channel,
            "message_id": self.message_id,
            "chunk_index": self.chunk_index,
            "record_index": self.record_index,
            "file_path": self.file_path,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "sentiment": self.sentiment.value,
            "key_insight": self.key_insight,
            "relevance_score": self.relevance_score,
            "reference_id": self.reference_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Citation":
        """Deserialize from storage."""
        return cls(
            quote=data["quote"],
            author=data.get("author"),
            timestamp=data.get("timestamp"),
            channel=data.get("channel"),
            message_id=data.get("message_id"),
            chunk_index=data.get("chunk_index", 0),
            record_index=data.get("record_index", 0),
            file_path=data.get("file_path"),
            context_before=data.get("context_before"),
            context_after=data.get("context_after"),
            sentiment=Sentiment(data.get("sentiment", "neutral")),
            key_insight=data.get("key_insight"),
            relevance_score=data.get("relevance_score", 0.0),
        )


@dataclass
class CitationReport:
    """
    Complete citation report for a query.
    
    Contains all citations found, verification info, and summary.
    """
    query: str
    file_path: Optional[str] = None
    
    # All citations found
    citations: list[Citation] = field(default_factory=list)
    
    # Stats
    total_found: int = 0
    unique_authors: int = 0
    sentiment_breakdown: dict[str, int] = field(default_factory=dict)
    
    # Verification
    verified: bool = False
    verification_issues: list[str] = field(default_factory=list)
    
    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_citation(self, citation: Citation):
        """Add a citation to the report."""
        self.citations.append(citation)
        self.total_found = len(self.citations)
        self._update_stats()
    
    def _update_stats(self):
        """Update summary statistics."""
        authors = set(c.author for c in self.citations if c.author)
        self.unique_authors = len(authors)
        
        self.sentiment_breakdown = {
            "positive": len([c for c in self.citations if c.sentiment == Sentiment.POSITIVE]),
            "negative": len([c for c in self.citations if c.sentiment == Sentiment.NEGATIVE]),
            "neutral": len([c for c in self.citations if c.sentiment == Sentiment.NEUTRAL]),
            "mixed": len([c for c in self.citations if c.sentiment == Sentiment.MIXED]),
        }
    
    def get_all_references(self) -> list[str]:
        """Get list of all reference IDs for verification."""
        return [c.reference_id for c in self.citations]
    
    def verify(self, data: list[dict], content_field: str = "content") -> bool:
        """
        Verify citations against original data.
        
        Args:
            data: The original JSON data (list of records)
            content_field: Field name containing the text content
            
        Returns:
            True if all citations verified
        """
        self.verification_issues = []
        verified_count = 0
        
        for citation in self.citations:
            try:
                # Parse reference
                chunk_idx, record_idx = map(int, citation.reference_id.split("."))
                
                # For now we can only verify record_idx against flat data
                # Chunk index would need the chunker to verify
                if record_idx < len(data):
                    record = data[record_idx]
                    content = record.get(content_field, str(record))
                    
                    # Check if quote exists in content (fuzzy match)
                    quote_words = set(citation.quote.lower().split())
                    content_words = set(content.lower().split())
                    
                    overlap = len(quote_words & content_words) / len(quote_words) if quote_words else 0
                    
                    if overlap > 0.5:  # At least 50% word overlap
                        verified_count += 1
                    else:
                        self.verification_issues.append(
                            f"Ref {citation.reference_id}: Quote not found in record"
                        )
                else:
                    self.verification_issues.append(
                        f"Ref {citation.reference_id}: Record index out of range"
                    )
                    
            except (ValueError, IndexError) as e:
                self.verification_issues.append(
                    f"Ref {citation.reference_id}: Verification error - {e}"
                )
        
        self.verified = verified_count == len(self.citations)
        return self.verified
    
    def to_markdown(self) -> str:
        """Generate full markdown report."""
        lines = [
            f"# 📚 Citation Report",
            "",
            f"**Query:** {self.query}",
            f"**Source:** `{self.file_path or 'Unknown'}`",
            f"**Generated:** {self.generated_at}",
            "",
            "---",
            "",
            "## 📊 Summary Statistics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Citations | {self.total_found} |",
            f"| Unique Contributors | {self.unique_authors} |",
            f"| ✅ Positive | {self.sentiment_breakdown.get('positive', 0)} |",
            f"| ❌ Negative | {self.sentiment_breakdown.get('negative', 0)} |",
            f"| ➖ Neutral | {self.sentiment_breakdown.get('neutral', 0)} |",
            f"| 🔄 Mixed | {self.sentiment_breakdown.get('mixed', 0)} |",
            "",
            "---",
            "",
            "## 🔍 All Citations",
            "",
        ]
        
        for i, citation in enumerate(self.citations, 1):
            lines.append(f"### Citation {i}")
            lines.append("")
            lines.append(citation.to_markdown())
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Verification section
        lines.extend([
            "## ✅ Verification",
            "",
            f"**Status:** {'Verified ✓' if self.verified else 'Not Verified'}",
            "",
        ])
        
        if self.verification_issues:
            lines.append("**Issues:**")
            for issue in self.verification_issues:
                lines.append(f"- ⚠️ {issue}")
            lines.append("")
        
        # Reference list
        lines.extend([
            "## 🔗 Reference Index",
            "",
            "Use these references to look up original records:",
            "",
        ])
        
        for ref in self.get_all_references():
            lines.append(f"- `{ref}`")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Serialize for storage."""
        return {
            "query": self.query,
            "file_path": self.file_path,
            "citations": [c.to_dict() for c in self.citations],
            "total_found": self.total_found,
            "unique_authors": self.unique_authors,
            "sentiment_breakdown": self.sentiment_breakdown,
            "verified": self.verified,
            "verification_issues": self.verification_issues,
            "generated_at": self.generated_at,
        }


class CitationExtractor:
    """
    Extract citations from LLM responses.
    
    Parses the structured citation format from exhaustive extraction.
    """
    
    @staticmethod
    def extract_from_response(
        response: str,
        chunk_index: int = 0,
        file_path: Optional[str] = None,
    ) -> list[Citation]:
        """
        Extract citations from an LLM response.
        
        Parses the structured format returned by EXHAUSTIVE_EXTRACT prompts.
        
        Args:
            response: LLM response text
            chunk_index: Index of the chunk this came from
            file_path: Source file path
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        # Pattern to match citation blocks
        # Look for ### Finding N or ### Citation N followed by blockquote
        finding_pattern = r'###\s*(?:Finding|Citation)\s*\d+\s*\n+>\s*["\']?(.+?)["\']?\s*\n+\*\*Source:\*\*\s*(.+?)\n'
        
        matches = re.finditer(finding_pattern, response, re.DOTALL | re.IGNORECASE)
        
        record_idx = 0
        for match in matches:
            quote = match.group(1).strip().strip('"\'')
            source_line = match.group(2).strip()
            
            # Parse source line (format: @username | timestamp | channel)
            source_parts = [p.strip() for p in source_line.split("|")]
            
            author = None
            timestamp = None
            channel = None
            
            for part in source_parts:
                if part.startswith("@"):
                    author = part[1:]
                elif "#" in part:
                    channel = part.replace("#", "").strip()
                elif re.match(r'\d{4}[-/]', part) or re.match(r'\d{1,2}:\d{2}', part):
                    timestamp = part
            
            # Look for sentiment in surrounding text
            sentiment = Sentiment.NEUTRAL
            text_after = response[match.end():match.end() + 200].lower()
            if "positive" in text_after:
                sentiment = Sentiment.POSITIVE
            elif "negative" in text_after:
                sentiment = Sentiment.NEGATIVE
            elif "mixed" in text_after:
                sentiment = Sentiment.MIXED
            
            # Look for insight
            insight_match = re.search(r'\*\*(?:Key\s*)?Insight:\*\*\s*(.+?)(?:\n|$)', 
                                      response[match.end():match.end() + 500])
            key_insight = insight_match.group(1).strip() if insight_match else None
            
            citation = Citation(
                quote=quote,
                author=author,
                timestamp=timestamp,
                channel=channel,
                chunk_index=chunk_index,
                record_index=record_idx,
                file_path=file_path,
                sentiment=sentiment,
                key_insight=key_insight,
            )
            
            citations.append(citation)
            record_idx += 1
        
        # Fallback: try to extract simple blockquotes if structured format not found
        if not citations:
            blockquote_pattern = r'>\s*["\']?(.+?)["\']?\s*\n'
            for i, match in enumerate(re.finditer(blockquote_pattern, response)):
                quote = match.group(1).strip()
                if len(quote) > 10:  # Skip very short quotes
                    citations.append(Citation(
                        quote=quote,
                        chunk_index=chunk_index,
                        record_index=i,
                        file_path=file_path,
                    ))
        
        return citations
    
    @staticmethod
    def merge_citations(
        chunk_citations: list[list[Citation]],
        deduplicate: bool = True,
    ) -> list[Citation]:
        """
        Merge citations from multiple chunks.
        
        Args:
            chunk_citations: List of citation lists (one per chunk)
            deduplicate: Remove duplicate quotes
            
        Returns:
            Merged list of citations
        """
        all_citations = []
        seen_quotes = set()
        
        for citations in chunk_citations:
            for citation in citations:
                # Deduplicate by quote text (normalized)
                quote_key = citation.quote.lower().strip()[:100]
                
                if deduplicate and quote_key in seen_quotes:
                    continue
                
                seen_quotes.add(quote_key)
                all_citations.append(citation)
        
        # Sort by chunk/record index for consistent ordering
        all_citations.sort(key=lambda c: (c.chunk_index, c.record_index))
        
        return all_citations

