"""
Discord Export Handler: Optimized handling for Discord data exports.

Discord exports come in two main formats:
1. Package export: Folder with multiple JSON files per channel
2. Single channel export: JSON file with messages array

This handler provides:
- Format detection
- Channel-aware chunking
- Message threading
- Attachment and embed handling
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Iterator, Any
from pathlib import Path
from datetime import datetime


@dataclass
class DiscordMessage:
    """Structured Discord message."""
    id: str
    content: str
    author_name: str
    author_id: str
    timestamp: str
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    attachments: list[dict] = field(default_factory=list)
    embeds: list[dict] = field(default_factory=list)
    reactions: list[dict] = field(default_factory=list)
    reply_to: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "DiscordMessage":
        """Parse a Discord message from JSON dict."""
        author = data.get("author", {})
        if isinstance(author, dict):
            author_name = author.get("name", author.get("username", "Unknown"))
            author_id = author.get("id", "")
        else:
            author_name = str(author)
            author_id = ""
        
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            author_name=author_name,
            author_id=author_id,
            timestamp=data.get("timestamp", ""),
            channel_id=data.get("channel_id"),
            attachments=data.get("attachments", []),
            embeds=data.get("embeds", []),
            reactions=data.get("reactions", []),
            reply_to=data.get("reference", {}).get("message_id") if data.get("reference") else None,
        )
    
    def to_text(self, include_metadata: bool = True) -> str:
        """Format message for LLM consumption."""
        parts = []
        
        if include_metadata:
            ts = self.timestamp[:19] if len(self.timestamp) >= 19 else self.timestamp
            parts.append(f"[{ts}] {self.author_name}:")
        
        if self.reply_to:
            parts.append(f"  ↳ (replying to {self.reply_to})")
        
        parts.append(f"  {self.content}" if include_metadata else self.content)
        
        if self.attachments:
            att_info = [a.get("filename", "file") for a in self.attachments]
            parts.append(f"  📎 Attachments: {', '.join(att_info)}")
        
        if self.embeds:
            embed_info = [e.get("title", "embed") for e in self.embeds if e.get("title")]
            if embed_info:
                parts.append(f"  🔗 Embeds: {', '.join(embed_info)}")
        
        return "\n".join(parts)


@dataclass
class DiscordChannel:
    """Metadata for a Discord channel."""
    id: str
    name: str
    type: str = "text"
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    message_count: int = 0


class DiscordHandler:
    """
    Handler for Discord export data.
    
    Provides optimized processing for Discord-specific structures.
    """
    
    def __init__(self):
        self.channels: dict[str, DiscordChannel] = {}
        self.message_count = 0
    
    def detect_format(self, data: Any) -> str:
        """
        Detect the Discord export format.
        
        Returns:
            "package" - Full account export with multiple channels
            "channel" - Single channel export
            "messages" - Raw messages array
            "unknown" - Not a Discord format
        """
        if isinstance(data, dict):
            if "messages" in data and "channel" in data:
                return "channel"
            if "messages" in data:
                return "messages"
        
        if isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict):
                if "author" in first and "content" in first:
                    return "messages"
        
        return "unknown"
    
    def parse_messages(
        self,
        data: Any,
        channel_info: Optional[dict] = None,
    ) -> Iterator[DiscordMessage]:
        """
        Parse Discord messages from export data.
        
        Args:
            data: Raw export data (dict or list)
            channel_info: Optional channel metadata
            
        Yields:
            DiscordMessage objects
        """
        format_type = self.detect_format(data)
        
        if format_type == "channel":
            channel = data.get("channel", {})
            channel_id = channel.get("id", "unknown")
            channel_name = channel.get("name", "unknown")
            
            for msg_data in data.get("messages", []):
                msg = DiscordMessage.from_dict(msg_data)
                msg.channel_id = channel_id
                msg.channel_name = channel_name
                yield msg
        
        elif format_type == "messages":
            if isinstance(data, dict):
                messages = data.get("messages", [])
            else:
                messages = data
            
            for msg_data in messages:
                yield DiscordMessage.from_dict(msg_data)
        
        else:
            # Try to parse as generic messages
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "content" in item:
                        yield DiscordMessage.from_dict(item)
    
    def group_by_channel(
        self,
        messages: list[DiscordMessage],
    ) -> dict[str, list[DiscordMessage]]:
        """Group messages by channel."""
        groups: dict[str, list[DiscordMessage]] = {}
        
        for msg in messages:
            channel_key = msg.channel_name or msg.channel_id or "unknown"
            if channel_key not in groups:
                groups[channel_key] = []
            groups[channel_key].append(msg)
        
        return groups
    
    def group_by_date(
        self,
        messages: list[DiscordMessage],
    ) -> dict[str, list[DiscordMessage]]:
        """Group messages by date."""
        groups: dict[str, list[DiscordMessage]] = {}
        
        for msg in messages:
            # Extract date from timestamp (YYYY-MM-DD)
            if msg.timestamp:
                date_key = msg.timestamp[:10]
            else:
                date_key = "unknown"
            
            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(msg)
        
        return groups
    
    def format_conversation(
        self,
        messages: list[DiscordMessage],
        include_metadata: bool = True,
    ) -> str:
        """Format a list of messages as a conversation."""
        # Sort by timestamp
        sorted_msgs = sorted(
            messages,
            key=lambda m: m.timestamp or ""
        )
        
        lines = []
        for msg in sorted_msgs:
            lines.append(msg.to_text(include_metadata))
        
        return "\n\n".join(lines)
    
    def build_thread_context(
        self,
        messages: list[DiscordMessage],
        target_message_id: str,
        context_before: int = 5,
        context_after: int = 5,
    ) -> list[DiscordMessage]:
        """
        Build context around a specific message.
        
        Includes messages before and after, plus any replies.
        """
        # Find target message index
        sorted_msgs = sorted(messages, key=lambda m: m.timestamp or "")
        target_idx = None
        
        for i, msg in enumerate(sorted_msgs):
            if msg.id == target_message_id:
                target_idx = i
                break
        
        if target_idx is None:
            return []
        
        # Get context window
        start = max(0, target_idx - context_before)
        end = min(len(sorted_msgs), target_idx + context_after + 1)
        
        context = sorted_msgs[start:end]
        
        # Add any messages that reply to messages in context
        context_ids = {m.id for m in context}
        for msg in sorted_msgs:
            if msg.reply_to and msg.reply_to in context_ids and msg not in context:
                context.append(msg)
        
        return sorted(context, key=lambda m: m.timestamp or "")
    
    def get_statistics(
        self,
        messages: list[DiscordMessage],
    ) -> dict:
        """Calculate statistics for a set of messages."""
        authors: dict[str, int] = {}
        channels: dict[str, int] = {}
        dates: dict[str, int] = {}
        
        for msg in messages:
            # Count by author
            authors[msg.author_name] = authors.get(msg.author_name, 0) + 1
            
            # Count by channel
            channel = msg.channel_name or msg.channel_id or "unknown"
            channels[channel] = channels.get(channel, 0) + 1
            
            # Count by date
            date = msg.timestamp[:10] if msg.timestamp else "unknown"
            dates[date] = dates.get(date, 0) + 1
        
        return {
            "total_messages": len(messages),
            "unique_authors": len(authors),
            "unique_channels": len(channels),
            "date_range": {
                "earliest": min(dates.keys()) if dates else None,
                "latest": max(dates.keys()) if dates else None,
            },
            "top_authors": sorted(
                authors.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "messages_per_channel": channels,
        }

