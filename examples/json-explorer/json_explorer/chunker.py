"""
JSON Chunker: Split large JSON into processable chunks.

Design Philosophy:
- Stream through files, never load all into memory
- Respect semantic boundaries (don't split messages)
- Provide metadata for each chunk (index, offset, context)
"""

import json
from dataclasses import dataclass, field
from typing import Iterator, Optional, Any, Callable
from pathlib import Path

from .schema import JsonSchema, JsonFormat
from .config import ChunkingStrategy


@dataclass
class Chunk:
    """
    A chunk of JSON data ready for LLM processing.
    
    Contains the actual data plus metadata for tracing.
    """
    index: int
    total_chunks: Optional[int] = None  # May be unknown for streaming
    
    # The actual content
    records: list[dict] = field(default_factory=list)
    text_content: str = ""  # Pre-formatted for LLM
    
    # Metadata for tracing
    record_count: int = 0
    start_record_index: int = 0
    end_record_index: int = 0
    char_count: int = 0
    
    # Optional grouping info
    group_key: Optional[str] = None  # e.g., channel name, date
    group_value: Optional[str] = None
    
    # Time range if applicable
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    
    def to_llm_context(self, include_metadata: bool = True) -> str:
        """Format chunk for LLM consumption."""
        parts = []
        
        if include_metadata:
            parts.append(f"[Chunk {self.index + 1}")
            if self.total_chunks:
                parts[-1] += f" of {self.total_chunks}"
            parts[-1] += f" | Records {self.start_record_index + 1}-{self.end_record_index + 1}]"
            
            if self.group_key and self.group_value:
                parts.append(f"[{self.group_key}: {self.group_value}]")
            
            if self.start_timestamp and self.end_timestamp:
                parts.append(f"[Time: {self.start_timestamp} to {self.end_timestamp}]")
            
            parts.append("")
        
        parts.append(self.text_content)
        
        return "\n".join(parts)
    
    def to_dict(self) -> dict:
        """Serialize for tracing."""
        return {
            "index": self.index,
            "total_chunks": self.total_chunks,
            "record_count": self.record_count,
            "start_record_index": self.start_record_index,
            "end_record_index": self.end_record_index,
            "char_count": self.char_count,
            "group_key": self.group_key,
            "group_value": self.group_value,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            # Don't include full content in trace metadata
            "preview": self.text_content[:200] + "..." if len(self.text_content) > 200 else self.text_content,
        }


class JsonChunker:
    """
    Chunk JSON data based on schema and strategy.
    
    Supports:
    - Record-based chunking (N records per chunk)
    - Size-based chunking (max chars per chunk)
    - Field-based grouping (group by channel, date, etc.)
    """
    
    def __init__(
        self,
        schema: JsonSchema,
        max_chunk_size: int = 50_000,
        strategy: ChunkingStrategy = ChunkingStrategy.AUTO,
        group_field: Optional[str] = None,
        records_per_chunk: int = 100,
        overlap: int = 0,  # Number of records to overlap
    ):
        self.schema = schema
        self.max_chunk_size = max_chunk_size
        self.strategy = strategy
        self.group_field = group_field
        self.records_per_chunk = records_per_chunk
        self.overlap = overlap
        
        # Determine actual strategy
        if strategy == ChunkingStrategy.AUTO:
            self._auto_strategy = self._detect_strategy()
        else:
            self._auto_strategy = strategy
    
    def _detect_strategy(self) -> ChunkingStrategy:
        """Auto-detect best chunking strategy based on schema."""
        if self.schema.format == JsonFormat.DISCORD:
            # For Discord, prefer time-based if we have timestamps
            if self.schema.timestamp_field:
                return ChunkingStrategy.TIME_BASED
            return ChunkingStrategy.RECORDS
        
        if self.schema.format == JsonFormat.SLACK:
            return ChunkingStrategy.TIME_BASED
        
        if self.schema.timestamp_field:
            return ChunkingStrategy.TIME_BASED
        
        return ChunkingStrategy.SIZE_BASED
    
    def chunk_from_file(self, file_path: str | Path) -> Iterator[Chunk]:
        """
        Stream chunks from a JSON file.
        
        Yields Chunk objects as they are created.
        Memory efficient - doesn't load full file.
        """
        file_path = Path(file_path)
        
        # For now, load file (in production, use ijson for streaming)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different root types
        if isinstance(data, list):
            yield from self._chunk_array(data)
        elif isinstance(data, dict):
            # Check for known wrapper formats
            if "messages" in data and isinstance(data["messages"], list):
                yield from self._chunk_array(data["messages"])
            else:
                # Yield single chunk for object
                yield self._create_chunk(
                    records=[data],
                    index=0,
                    total=1,
                    start_idx=0,
                )
        else:
            raise ValueError(f"Unexpected root type: {type(data)}")
    
    def chunk_from_data(self, data: list[dict]) -> Iterator[Chunk]:
        """Chunk in-memory data."""
        yield from self._chunk_array(data)
    
    def _chunk_array(self, records: list[dict]) -> Iterator[Chunk]:
        """Chunk an array of records based on strategy."""
        if self._auto_strategy == ChunkingStrategy.FIELD_BASED and self.group_field:
            yield from self._chunk_by_field(records)
        elif self._auto_strategy == ChunkingStrategy.TIME_BASED and self.schema.timestamp_field:
            yield from self._chunk_by_time(records)
        elif self._auto_strategy == ChunkingStrategy.SIZE_BASED:
            yield from self._chunk_by_size(records)
        else:
            yield from self._chunk_by_records(records)
    
    def _chunk_by_records(self, records: list[dict]) -> Iterator[Chunk]:
        """Chunk by fixed number of records."""
        total_chunks = (len(records) + self.records_per_chunk - 1) // self.records_per_chunk
        
        start = 0
        chunk_index = 0
        
        while start < len(records):
            end = min(start + self.records_per_chunk, len(records))
            chunk_records = records[start:end]
            
            yield self._create_chunk(
                records=chunk_records,
                index=chunk_index,
                total=total_chunks,
                start_idx=start,
            )
            
            chunk_index += 1
            start = end - self.overlap if self.overlap > 0 else end
    
    def _chunk_by_size(self, records: list[dict]) -> Iterator[Chunk]:
        """Chunk by character size limit."""
        chunks = []
        current_records = []
        current_size = 0
        start_idx = 0
        
        for i, record in enumerate(records):
            record_str = self._format_record(record)
            record_size = len(record_str)
            
            if current_size + record_size > self.max_chunk_size and current_records:
                # Emit current chunk
                chunks.append((current_records, start_idx))
                current_records = []
                current_size = 0
                start_idx = i
            
            current_records.append(record)
            current_size += record_size
        
        if current_records:
            chunks.append((current_records, start_idx))
        
        total = len(chunks)
        for idx, (chunk_records, start) in enumerate(chunks):
            yield self._create_chunk(
                records=chunk_records,
                index=idx,
                total=total,
                start_idx=start,
            )
    
    def _chunk_by_time(self, records: list[dict]) -> Iterator[Chunk]:
        """Chunk by time periods (e.g., per day, per hour)."""
        timestamp_field = self.schema.timestamp_field
        if not timestamp_field:
            yield from self._chunk_by_records(records)
            return
        
        # Sort by timestamp
        sorted_records = sorted(
            records,
            key=lambda r: r.get(timestamp_field, "") or ""
        )
        
        # Group by day (extract YYYY-MM-DD from timestamp)
        groups: dict[str, list[dict]] = {}
        for record in sorted_records:
            ts = record.get(timestamp_field, "")
            if ts:
                # Try to extract date portion
                day = ts[:10] if len(ts) >= 10 else ts
            else:
                day = "unknown"
            
            if day not in groups:
                groups[day] = []
            groups[day].append(record)
        
        # Create chunks from groups (may need to split large days)
        chunk_index = 0
        total_chunks = len(groups)  # Approximate - may be more if days are split
        
        for day, day_records in sorted(groups.items()):
            # If day is too large, sub-chunk
            if len(day_records) > self.records_per_chunk * 2:
                for sub_chunk in self._chunk_by_records(day_records):
                    sub_chunk.index = chunk_index
                    sub_chunk.group_key = "date"
                    sub_chunk.group_value = day
                    yield sub_chunk
                    chunk_index += 1
            else:
                yield self._create_chunk(
                    records=day_records,
                    index=chunk_index,
                    total=total_chunks,
                    start_idx=0,
                    group_key="date",
                    group_value=day,
                )
                chunk_index += 1
    
    def _chunk_by_field(self, records: list[dict]) -> Iterator[Chunk]:
        """Chunk by grouping on a specific field value."""
        if not self.group_field:
            yield from self._chunk_by_records(records)
            return
        
        # Group by field value
        groups: dict[str, list[dict]] = {}
        for record in records:
            value = str(record.get(self.group_field, "unknown"))
            if value not in groups:
                groups[value] = []
            groups[value].append(record)
        
        chunk_index = 0
        for field_value, group_records in groups.items():
            # May need to split large groups
            for sub_chunk in self._chunk_by_size(group_records):
                sub_chunk.index = chunk_index
                sub_chunk.group_key = self.group_field
                sub_chunk.group_value = field_value
                yield sub_chunk
                chunk_index += 1
    
    def _create_chunk(
        self,
        records: list[dict],
        index: int,
        total: int,
        start_idx: int,
        group_key: Optional[str] = None,
        group_value: Optional[str] = None,
    ) -> Chunk:
        """Create a Chunk object from records."""
        # Format records for LLM
        text_parts = []
        for i, record in enumerate(records):
            formatted = self._format_record(record)
            text_parts.append(formatted)
        
        text_content = "\n\n".join(text_parts)
        
        # Extract time range if available
        start_ts = None
        end_ts = None
        if self.schema.timestamp_field:
            timestamps = [
                r.get(self.schema.timestamp_field)
                for r in records
                if r.get(self.schema.timestamp_field)
            ]
            if timestamps:
                start_ts = min(timestamps)
                end_ts = max(timestamps)
        
        return Chunk(
            index=index,
            total_chunks=total,
            records=records,
            text_content=text_content,
            record_count=len(records),
            start_record_index=start_idx,
            end_record_index=start_idx + len(records) - 1,
            char_count=len(text_content),
            group_key=group_key,
            group_value=group_value,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
        )
    
    def _format_record(self, record: dict) -> str:
        """Format a single record for LLM consumption."""
        if self.schema.format == JsonFormat.DISCORD:
            return self._format_discord_message(record)
        elif self.schema.format == JsonFormat.SLACK:
            return self._format_slack_message(record)
        else:
            return self._format_generic_record(record)
    
    def _format_discord_message(self, record: dict) -> str:
        """Format a Discord message for readability."""
        author = record.get("author", {})
        if isinstance(author, dict):
            author_name = author.get("name", author.get("username", "Unknown"))
        else:
            author_name = str(author)
        
        timestamp = record.get("timestamp", "")
        content = record.get("content", "")
        
        # Include attachments info
        attachments = record.get("attachments", [])
        attachment_str = ""
        if attachments:
            attachment_str = f" [+{len(attachments)} attachment(s)]"
        
        # Include embeds info
        embeds = record.get("embeds", [])
        embed_str = ""
        if embeds:
            embed_str = f" [+{len(embeds)} embed(s)]"
        
        return f"[{timestamp}] {author_name}: {content}{attachment_str}{embed_str}"
    
    def _format_slack_message(self, record: dict) -> str:
        """Format a Slack message for readability."""
        user = record.get("user", "Unknown")
        ts = record.get("ts", "")
        text = record.get("text", "")
        
        return f"[{ts}] {user}: {text}"
    
    def _format_generic_record(self, record: dict) -> str:
        """Format a generic record as compact JSON."""
        # For generic records, use compact JSON
        # Focus on content fields if available
        if self.schema.content_field and self.schema.content_field in record:
            content = record[self.schema.content_field]
            other_fields = {k: v for k, v in record.items() if k != self.schema.content_field}
            if other_fields:
                meta = json.dumps(other_fields, ensure_ascii=False)
                return f"{meta}\n{content}"
            return str(content)
        
        return json.dumps(record, ensure_ascii=False, indent=None)

