"""
Generic JSON Handler: Handle arbitrary JSON structures.

Provides basic handling for any JSON that doesn't match
a known format (Discord, Slack, etc.)
"""

import json
from dataclasses import dataclass
from typing import Any, Iterator, Optional


@dataclass
class GenericRecord:
    """A generic JSON record with flattened access."""
    data: dict
    index: int
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a value by dot-notation path.
        
        Example: record.get("user.name") for {"user": {"name": "Alice"}}
        """
        parts = path.split(".")
        value = self.data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(value):
                    value = value[idx]
                else:
                    return default
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def to_text(self, max_length: int = 1000) -> str:
        """Convert to compact text representation."""
        text = json.dumps(self.data, ensure_ascii=False, indent=None)
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    def to_pretty_text(self, indent: int = 2) -> str:
        """Convert to pretty-printed text."""
        return json.dumps(self.data, ensure_ascii=False, indent=indent)


class GenericHandler:
    """
    Handler for generic JSON data.
    
    Provides basic parsing and formatting for any JSON structure.
    """
    
    def __init__(self):
        self.record_count = 0
    
    def detect_structure(self, data: Any) -> dict:
        """
        Analyze the structure of JSON data.
        
        Returns dict with:
        - root_type: "array", "object", "primitive"
        - record_count: Number of top-level records (for arrays)
        - sample_fields: Fields found in samples
        - nested_arrays: Paths to nested arrays
        """
        result = {
            "root_type": "unknown",
            "record_count": None,
            "sample_fields": [],
            "nested_arrays": [],
        }
        
        if isinstance(data, list):
            result["root_type"] = "array"
            result["record_count"] = len(data)
            
            if data and isinstance(data[0], dict):
                result["sample_fields"] = list(data[0].keys())
                
                # Find nested arrays
                for key, value in data[0].items():
                    if isinstance(value, list):
                        result["nested_arrays"].append(key)
        
        elif isinstance(data, dict):
            result["root_type"] = "object"
            result["sample_fields"] = list(data.keys())
            
            # Check for array fields that might be the main data
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    result["nested_arrays"].append(key)
                    if isinstance(value[0], dict):
                        result[f"{key}_fields"] = list(value[0].keys())
        
        else:
            result["root_type"] = "primitive"
        
        return result
    
    def extract_records(
        self,
        data: Any,
        path: Optional[str] = None,
    ) -> Iterator[GenericRecord]:
        """
        Extract records from JSON data.
        
        Args:
            data: The JSON data
            path: Optional dot-path to array of records
            
        Yields:
            GenericRecord objects
        """
        # Navigate to path if specified
        if path:
            parts = path.split(".")
            target = data
            for part in parts:
                if isinstance(target, dict):
                    target = target.get(part)
                else:
                    target = None
                    break
            data = target
        
        # Yield records
        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    yield GenericRecord(data=item, index=i)
                else:
                    yield GenericRecord(data={"value": item}, index=i)
        
        elif isinstance(data, dict):
            yield GenericRecord(data=data, index=0)
    
    def flatten_record(
        self,
        record: dict,
        prefix: str = "",
        max_depth: int = 5,
    ) -> dict:
        """
        Flatten a nested record to single-level dict.
        
        Example:
            {"user": {"name": "Alice"}} -> {"user.name": "Alice"}
        """
        if max_depth <= 0:
            return {prefix.rstrip("."): record}
        
        result = {}
        
        for key, value in record.items():
            full_key = f"{prefix}{key}"
            
            if isinstance(value, dict):
                nested = self.flatten_record(value, f"{full_key}.", max_depth - 1)
                result.update(nested)
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    result[full_key] = f"[{len(value)} objects]"
                else:
                    result[full_key] = value
            else:
                result[full_key] = value
        
        return result
    
    def format_for_llm(
        self,
        records: list[GenericRecord],
        max_chars: int = 50000,
        format_style: str = "compact",
    ) -> str:
        """
        Format records for LLM consumption.
        
        Args:
            records: List of records
            max_chars: Maximum characters
            format_style: "compact", "pretty", or "summary"
            
        Returns:
            Formatted string
        """
        parts = []
        current_length = 0
        
        for record in records:
            if format_style == "compact":
                text = record.to_text()
            elif format_style == "pretty":
                text = record.to_pretty_text()
            else:  # summary
                flat = self.flatten_record(record.data)
                text = "; ".join(f"{k}={v}" for k, v in list(flat.items())[:10])
            
            # Add record marker
            formatted = f"[Record {record.index + 1}]\n{text}"
            
            if current_length + len(formatted) > max_chars:
                parts.append(f"... truncated {len(records) - len(parts)} more records ...")
                break
            
            parts.append(formatted)
            current_length += len(formatted) + 2
        
        return "\n\n".join(parts)
    
    def find_searchable_fields(self, sample: dict) -> list[str]:
        """
        Identify fields that are likely searchable (contain text).
        """
        searchable = []
        
        for key, value in sample.items():
            if isinstance(value, str) and len(value) > 10:
                searchable.append(key)
            elif isinstance(value, dict):
                nested = self.find_searchable_fields(value)
                searchable.extend(f"{key}.{n}" for n in nested)
        
        return searchable
    
    def find_timestamp_fields(self, sample: dict) -> list[str]:
        """
        Identify fields that look like timestamps.
        """
        timestamp_indicators = [
            "time", "date", "created", "updated", "timestamp", 
            "at", "_at", "when", "on"
        ]
        
        candidates = []
        
        for key, value in sample.items():
            key_lower = key.lower()
            if any(ind in key_lower for ind in timestamp_indicators):
                candidates.append(key)
            elif isinstance(value, str):
                # Check if value looks like a timestamp
                if "T" in value and ":" in value:  # ISO format
                    candidates.append(key)
        
        return candidates

