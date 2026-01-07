"""
Schema Analysis: Understand JSON structure without loading full file.

Design Philosophy:
- Sample first N records to infer schema
- Detect known formats (Discord, Slack) automatically
- Build a navigable schema map for query planning
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Any, Iterator
from pathlib import Path
from enum import Enum


class JsonFormat(Enum):
    """Known JSON export formats with specialized handling."""
    DISCORD = "discord"
    SLACK = "slack"
    TWITTER = "twitter"
    GENERIC_ARRAY = "generic_array"
    GENERIC_OBJECT = "generic_object"
    JSONL = "jsonl"
    UNKNOWN = "unknown"


@dataclass
class FieldInfo:
    """Information about a field in the schema."""
    name: str
    field_type: str  # "string", "number", "boolean", "array", "object", "null", "mixed"
    nullable: bool = False
    sample_values: list = field(default_factory=list)
    nested_schema: Optional["JsonSchema"] = None  # For nested objects
    array_item_type: Optional[str] = None  # For arrays
    occurrence_count: int = 0
    
    @property
    def is_timestamp(self) -> bool:
        """Heuristic: field looks like a timestamp."""
        timestamp_indicators = ["time", "date", "created", "updated", "timestamp", "at"]
        return any(ind in self.name.lower() for ind in timestamp_indicators)
    
    @property
    def is_identifier(self) -> bool:
        """Heuristic: field looks like an ID."""
        return self.name.lower() in ["id", "_id", "uid", "uuid", "key"]
    
    @property
    def is_content(self) -> bool:
        """Heuristic: field contains main content."""
        content_indicators = ["content", "text", "message", "body", "description"]
        return any(ind in self.name.lower() for ind in content_indicators)


@dataclass
class JsonSchema:
    """
    Analyzed schema of a JSON file.
    
    This is NOT the full data - just structure information
    derived from sampling.
    """
    format: JsonFormat
    root_type: str  # "array", "object"
    total_records: Optional[int] = None  # Count if array
    fields: dict[str, FieldInfo] = field(default_factory=dict)
    file_size_bytes: int = 0
    sample_size: int = 0
    
    # Format-specific metadata
    discord_channels: Optional[list[str]] = None
    discord_guilds: Optional[list[str]] = None
    timestamp_field: Optional[str] = None
    content_field: Optional[str] = None
    id_field: Optional[str] = None
    
    def get_searchable_fields(self) -> list[str]:
        """Return fields that are likely to contain searchable text."""
        return [
            name for name, info in self.fields.items()
            if info.field_type == "string" and not info.is_identifier
        ]
    
    def get_groupable_fields(self) -> list[str]:
        """Return fields that could be used for grouping/chunking."""
        return [
            name for name, info in self.fields.items()
            if info.is_timestamp or info.field_type in ["string", "number"]
        ]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "format": self.format.value,
            "root_type": self.root_type,
            "total_records": self.total_records,
            "file_size_bytes": self.file_size_bytes,
            "sample_size": self.sample_size,
            "fields": {
                name: {
                    "type": info.field_type,
                    "nullable": info.nullable,
                    "is_timestamp": info.is_timestamp,
                    "is_content": info.is_content,
                    "sample_values": info.sample_values[:3],
                }
                for name, info in self.fields.items()
            },
            "timestamp_field": self.timestamp_field,
            "content_field": self.content_field,
            "id_field": self.id_field,
        }
    
    def summary(self) -> str:
        """Human-readable summary of the schema."""
        lines = [
            f"Format: {self.format.value}",
            f"Root type: {self.root_type}",
            f"Total records: {self.total_records or 'unknown'}",
            f"File size: {self.file_size_bytes / 1024 / 1024:.2f} MB",
            f"Fields analyzed: {len(self.fields)}",
        ]
        
        if self.timestamp_field:
            lines.append(f"Timestamp field: {self.timestamp_field}")
        if self.content_field:
            lines.append(f"Content field: {self.content_field}")
        
        lines.append("\nKey fields:")
        for name, info in self.fields.items():
            markers = []
            if info.is_timestamp:
                markers.append("⏰")
            if info.is_content:
                markers.append("📝")
            if info.is_identifier:
                markers.append("🔑")
            marker_str = " ".join(markers) if markers else ""
            lines.append(f"  - {name}: {info.field_type} {marker_str}")
        
        return "\n".join(lines)


class SchemaAnalyzer:
    """
    Analyze JSON schema by sampling without loading full file.
    
    Uses streaming parsing (ijson) for memory efficiency.
    """
    
    def __init__(
        self,
        sample_size: int = 100,
        max_depth: int = 10,
    ):
        self.sample_size = sample_size
        self.max_depth = max_depth
    
    def analyze(self, file_path: str | Path) -> JsonSchema:
        """
        Analyze a JSON file and return its schema.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            JsonSchema with structure information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        
        # Try to detect format and parse accordingly
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first chunk to detect format
            first_chunk = f.read(10000)
            f.seek(0)
            
            # Detect root type
            stripped = first_chunk.strip()
            if stripped.startswith('['):
                return self._analyze_array(f, file_size)
            elif stripped.startswith('{'):
                return self._analyze_object(f, file_size)
            else:
                # Might be JSONL
                return self._analyze_jsonl(f, file_size)
    
    def _analyze_array(self, f, file_size: int) -> JsonSchema:
        """Analyze a JSON array (most common: array of records)."""
        # For simplicity, use json.load for now
        # In production, use ijson for streaming
        f.seek(0)
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        if not isinstance(data, list):
            raise ValueError("Expected JSON array")
        
        # Sample records
        sample = data[:self.sample_size]
        total_records = len(data)
        
        # Detect format
        json_format = self._detect_format(sample)
        
        # Analyze fields from sample
        fields = self._analyze_fields(sample)
        
        # Find special fields
        timestamp_field = None
        content_field = None
        id_field = None
        
        for name, info in fields.items():
            if info.is_timestamp and not timestamp_field:
                timestamp_field = name
            if info.is_content and not content_field:
                content_field = name
            if info.is_identifier and not id_field:
                id_field = name
        
        # Format-specific metadata
        discord_channels = None
        discord_guilds = None
        
        if json_format == JsonFormat.DISCORD:
            discord_channels = self._extract_discord_channels(sample)
            discord_guilds = self._extract_discord_guilds(sample)
        
        return JsonSchema(
            format=json_format,
            root_type="array",
            total_records=total_records,
            fields=fields,
            file_size_bytes=file_size,
            sample_size=len(sample),
            discord_channels=discord_channels,
            discord_guilds=discord_guilds,
            timestamp_field=timestamp_field,
            content_field=content_field,
            id_field=id_field,
        )
    
    def _analyze_object(self, f, file_size: int) -> JsonSchema:
        """Analyze a JSON object (might contain nested arrays)."""
        f.seek(0)
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")
        
        # Check for Discord package format
        if "messages" in data and isinstance(data.get("messages"), list):
            # Discord channel export format
            messages = data["messages"]
            sample = messages[:self.sample_size]
            fields = self._analyze_fields(sample)
            
            return JsonSchema(
                format=JsonFormat.DISCORD,
                root_type="object",
                total_records=len(messages),
                fields=fields,
                file_size_bytes=file_size,
                sample_size=len(sample),
                discord_channels=[data.get("channel", {}).get("name", "unknown")],
                timestamp_field="timestamp",
                content_field="content",
                id_field="id",
            )
        
        # Generic object
        fields = {}
        for key, value in data.items():
            fields[key] = self._analyze_value(key, value)
        
        return JsonSchema(
            format=JsonFormat.GENERIC_OBJECT,
            root_type="object",
            total_records=None,
            fields=fields,
            file_size_bytes=file_size,
            sample_size=1,
        )
    
    def _analyze_jsonl(self, f, file_size: int) -> JsonSchema:
        """Analyze JSONL (newline-delimited JSON)."""
        f.seek(0)
        records = []
        
        for i, line in enumerate(f):
            if i >= self.sample_size:
                break
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        if not records:
            raise ValueError("No valid JSON records found in JSONL file")
        
        fields = self._analyze_fields(records)
        json_format = self._detect_format(records)
        
        return JsonSchema(
            format=json_format if json_format != JsonFormat.UNKNOWN else JsonFormat.JSONL,
            root_type="array",
            total_records=None,  # Unknown without counting all lines
            fields=fields,
            file_size_bytes=file_size,
            sample_size=len(records),
        )
    
    def _detect_format(self, sample: list[dict]) -> JsonFormat:
        """Detect the format based on sample records."""
        if not sample:
            return JsonFormat.UNKNOWN
        
        first = sample[0]
        if not isinstance(first, dict):
            return JsonFormat.GENERIC_ARRAY
        
        keys = set(first.keys())
        
        # Discord detection
        discord_indicators = {"content", "author", "timestamp", "channel_id"}
        if discord_indicators.issubset(keys) or "author" in keys and "content" in keys:
            return JsonFormat.DISCORD
        
        # Slack detection
        slack_indicators = {"ts", "user", "text", "channel"}
        if slack_indicators.issubset(keys):
            return JsonFormat.SLACK
        
        # Twitter detection
        twitter_indicators = {"tweet", "user", "created_at"}
        if twitter_indicators.issubset(keys) or "tweet" in keys:
            return JsonFormat.TWITTER
        
        return JsonFormat.GENERIC_ARRAY
    
    def _analyze_fields(self, records: list[dict]) -> dict[str, FieldInfo]:
        """Analyze field types from sample records."""
        field_data: dict[str, list] = {}
        
        for record in records:
            if not isinstance(record, dict):
                continue
            for key, value in record.items():
                if key not in field_data:
                    field_data[key] = []
                field_data[key].append(value)
        
        fields = {}
        for name, values in field_data.items():
            fields[name] = self._analyze_value(name, values, is_list=True)
        
        return fields
    
    def _analyze_value(
        self, 
        name: str, 
        values: Any, 
        is_list: bool = False
    ) -> FieldInfo:
        """Analyze a field's type and properties."""
        if is_list:
            # Analyze list of values
            types = set()
            samples = []
            null_count = 0
            
            for v in values[:50]:  # Sample up to 50 values
                if v is None:
                    null_count += 1
                    types.add("null")
                elif isinstance(v, bool):
                    types.add("boolean")
                    samples.append(v)
                elif isinstance(v, int):
                    types.add("number")
                    samples.append(v)
                elif isinstance(v, float):
                    types.add("number")
                    samples.append(v)
                elif isinstance(v, str):
                    types.add("string")
                    if len(v) < 100:
                        samples.append(v)
                elif isinstance(v, list):
                    types.add("array")
                elif isinstance(v, dict):
                    types.add("object")
            
            # Determine primary type
            types.discard("null")
            if len(types) == 0:
                field_type = "null"
            elif len(types) == 1:
                field_type = types.pop()
            else:
                field_type = "mixed"
            
            return FieldInfo(
                name=name,
                field_type=field_type,
                nullable=null_count > 0,
                sample_values=samples[:5],
                occurrence_count=len(values),
            )
        else:
            # Analyze single value
            value = values
            if value is None:
                return FieldInfo(name=name, field_type="null", nullable=True)
            elif isinstance(value, bool):
                return FieldInfo(name=name, field_type="boolean", sample_values=[value])
            elif isinstance(value, (int, float)):
                return FieldInfo(name=name, field_type="number", sample_values=[value])
            elif isinstance(value, str):
                return FieldInfo(name=name, field_type="string", sample_values=[value[:100]])
            elif isinstance(value, list):
                return FieldInfo(name=name, field_type="array")
            elif isinstance(value, dict):
                return FieldInfo(name=name, field_type="object")
            else:
                return FieldInfo(name=name, field_type="unknown")
    
    def _extract_discord_channels(self, sample: list[dict]) -> list[str]:
        """Extract unique channel names from Discord messages."""
        channels = set()
        for record in sample:
            if "channel_id" in record:
                channels.add(str(record["channel_id"]))
            if "channel" in record and isinstance(record["channel"], dict):
                name = record["channel"].get("name")
                if name:
                    channels.add(name)
        return list(channels)
    
    def _extract_discord_guilds(self, sample: list[dict]) -> list[str]:
        """Extract unique guild/server names from Discord messages."""
        guilds = set()
        for record in sample:
            if "guild_id" in record:
                guilds.add(str(record["guild_id"]))
            if "guild" in record and isinstance(record["guild"], dict):
                name = record["guild"].get("name")
                if name:
                    guilds.add(name)
        return list(guilds)

