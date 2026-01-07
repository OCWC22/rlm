#!/usr/bin/env python3
"""
Discord Export Extractor - Process Discord channel exports using RLM chunking.

Handles Discord JSON exports (from DiscordChatExporter or similar tools).
These files have a single JSON with a "messages" array containing all channel messages.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import anthropic
except ImportError:
    print("pip install anthropic", file=sys.stderr)
    sys.exit(1)


@dataclass
class ChunkSummary:
    """Summary of a message chunk."""
    chunk_idx: int
    time_range: str
    message_count: int
    topics: list[str] = field(default_factory=list)
    key_discussions: list[str] = field(default_factory=list)
    workflows_mentioned: list[str] = field(default_factory=list)
    tools_nodes: list[str] = field(default_factory=list)
    problems_solved: list[str] = field(default_factory=list)
    tokens_used: int = 0
    error: Optional[str] = None


class DiscordExtractor:
    """Extract insights from Discord channel exports using RLM chunking."""
    
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        deep_model: str = "claude-sonnet-4-20250514",
        rate_limit_delay: float = 0.3,
        max_workers: int = 3,
    ):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Set ANTHROPIC_API_KEY")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.scan_model = model
        self.deep_model = deep_model
        self.rate_limit_delay = rate_limit_delay
        self.max_workers = max_workers
        
        self.stats = {
            "messages_processed": 0,
            "chunks_processed": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }
    
    def _call_llm(self, prompt: str, model: str, max_tokens: int = 1500) -> tuple[str, int]:
        """Make LLM call with rate limiting."""
        time.sleep(self.rate_limit_delay)
        
        try:
            resp = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            tokens = resp.usage.input_tokens + resp.usage.output_tokens
            return resp.content[0].text, tokens
        except Exception as e:
            return f"ERROR: {e}", 0
    
    def _format_messages(self, messages: list[dict], max_chars: int = 30000) -> str:
        """Format messages for LLM consumption, respecting size limit."""
        lines = []
        total_chars = 0
        
        for msg in messages:
            author = msg.get("author", {}).get("name", "Unknown")
            content = msg.get("content", "").strip()
            timestamp = msg.get("timestamp", "")[:10]  # Just date
            
            # Skip empty messages
            if not content:
                continue
            
            # Truncate very long messages
            if len(content) > 500:
                content = content[:500] + "..."
            
            line = f"[{timestamp}] {author}: {content}"
            
            if total_chars + len(line) > max_chars:
                lines.append("... [truncated for context limit]")
                break
            
            lines.append(line)
            total_chars += len(line) + 1
        
        return "\n".join(lines)
    
    def _chunk_messages(
        self,
        messages: list[dict],
        messages_per_chunk: int = 200,
        max_chunks: Optional[int] = None,
    ) -> list[tuple[int, list[dict]]]:
        """Split messages into chunks."""
        chunks = []
        for i in range(0, len(messages), messages_per_chunk):
            chunk = messages[i:i + messages_per_chunk]
            chunks.append((len(chunks), chunk))
            if max_chunks and len(chunks) >= max_chunks:
                break
        return chunks
    
    def analyze_chunk(self, chunk_idx: int, messages: list[dict], context: str) -> ChunkSummary:
        """Analyze a chunk of messages."""
        summary = ChunkSummary(
            chunk_idx=chunk_idx,
            time_range=f"{messages[0].get('timestamp', '')[:10]} to {messages[-1].get('timestamp', '')[:10]}",
            message_count=len(messages),
        )
        
        formatted = self._format_messages(messages)
        
        prompt = f"""Analyze this chunk of Discord messages from a {context} channel.

MESSAGES (chunk {chunk_idx + 1}):
{formatted}

Extract the following in JSON format:
{{
  "topics": ["main topic 1", "main topic 2"],
  "key_discussions": ["Brief summary of important discussion 1", "Brief summary 2"],
  "workflows_mentioned": ["workflow name or description if any"],
  "tools_nodes": ["tool/node/model names mentioned"],
  "problems_solved": ["problem and its solution if discussed"]
}}

Be specific and extract actual content, not generic descriptions. JSON:"""

        response, tokens = self._call_llm(prompt, self.scan_model)
        summary.tokens_used = tokens
        self.stats["total_tokens"] += tokens
        self.stats["chunks_processed"] += 1
        self.stats["messages_processed"] += len(messages)
        
        # Parse response
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                summary.topics = data.get("topics", [])
                summary.key_discussions = data.get("key_discussions", [])
                summary.workflows_mentioned = data.get("workflows_mentioned", [])
                summary.tools_nodes = data.get("tools_nodes", [])
                summary.problems_solved = data.get("problems_solved", [])
        except json.JSONDecodeError:
            summary.error = "JSON parse error"
            summary.key_discussions = [response[:200]]
        
        return summary
    
    def process_export(
        self,
        filepath: str | Path,
        messages_per_chunk: int = 200,
        max_chunks: Optional[int] = None,
        deep_analyze_top_n: int = 5,
    ) -> dict:
        """
        Process a Discord export file.
        
        Returns dict with summaries and aggregated insights.
        """
        filepath = Path(filepath).expanduser()
        
        print(f"[1/4] Loading {filepath.name}...", file=sys.stderr)
        with open(filepath) as f:
            data = json.load(f)
        
        channel_name = data.get("channel", {}).get("name", "unknown")
        guild_name = data.get("guild", {}).get("name", "unknown")
        messages = data.get("messages", [])
        
        print(f"  Channel: #{channel_name} in {guild_name}", file=sys.stderr)
        print(f"  Messages: {len(messages):,}", file=sys.stderr)
        
        # Chunk messages
        print(f"\n[2/4] Chunking into groups of {messages_per_chunk}...", file=sys.stderr)
        chunks = self._chunk_messages(messages, messages_per_chunk, max_chunks)
        print(f"  Created {len(chunks)} chunks", file=sys.stderr)
        
        # Analyze chunks in parallel
        print(f"\n[3/4] Analyzing chunks with {self.scan_model}...", file=sys.stderr)
        summaries = []
        context = f"{channel_name} (ComfyUI/AI image generation)"
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.analyze_chunk, idx, msgs, context): idx
                for idx, msgs in chunks
            }
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    summary = future.result()
                    summaries.append(summary)
                    status = "✓" if not summary.error else "✗"
                    print(f"  [{status}] Chunk {idx + 1}: {summary.message_count} msgs, {summary.time_range}", file=sys.stderr)
                except Exception as e:
                    print(f"  [✗] Chunk {idx + 1}: {e}", file=sys.stderr)
        
        summaries.sort(key=lambda s: s.chunk_idx)
        
        # Aggregate findings
        print(f"\n[4/4] Aggregating insights...", file=sys.stderr)
        result = self._aggregate_findings(summaries, channel_name, guild_name, len(messages))
        
        # Stats
        self.stats["total_cost"] = self.stats["total_tokens"] * 0.00025 / 1000  # Haiku pricing
        
        return result
    
    def _aggregate_findings(
        self,
        summaries: list[ChunkSummary],
        channel_name: str,
        guild_name: str,
        total_messages: int,
    ) -> dict:
        """Aggregate all chunk summaries into final report."""
        
        # Collect all items
        all_topics = []
        all_discussions = []
        all_workflows = []
        all_tools = []
        all_problems = []
        
        for s in summaries:
            all_topics.extend(s.topics)
            all_discussions.extend(s.key_discussions)
            all_workflows.extend(s.workflows_mentioned)
            all_tools.extend(s.tools_nodes)
            all_problems.extend(s.problems_solved)
        
        # Dedupe and count
        def count_items(items):
            from collections import Counter
            cleaned = [i.strip().lower() for i in items if i and len(i) > 2]
            return Counter(cleaned).most_common(30)
        
        # Create synthesis prompt
        top_topics = [t for t, _ in count_items(all_topics)[:15]]
        top_tools = [t for t, _ in count_items(all_tools)[:20]]
        sample_discussions = all_discussions[:20]
        sample_problems = all_problems[:15]
        
        synthesis_prompt = f"""Based on analysis of {len(summaries)} chunks from the #{channel_name} Discord channel ({total_messages:,} messages total), synthesize a comprehensive summary.

TOP TOPICS DISCUSSED:
{json.dumps(top_topics, indent=2)}

TOOLS/NODES/MODELS MENTIONED:
{json.dumps(top_tools, indent=2)}

SAMPLE KEY DISCUSSIONS:
{json.dumps(sample_discussions, indent=2)}

SAMPLE PROBLEMS & SOLUTIONS:
{json.dumps(sample_problems, indent=2)}

Create a well-organized summary covering:
1. Main themes and topics (what does this community discuss most?)
2. Popular tools, nodes, and workflows
3. Common problems and solutions
4. Notable techniques or tips shared
5. Community patterns/behaviors

Write in markdown format with clear headers."""

        response, tokens = self._call_llm(synthesis_prompt, self.deep_model, max_tokens=2500)
        self.stats["total_tokens"] += tokens
        
        return {
            "channel": channel_name,
            "guild": guild_name,
            "total_messages": total_messages,
            "chunks_analyzed": len(summaries),
            "synthesis": response,
            "top_topics": count_items(all_topics),
            "top_tools": count_items(all_tools),
            "top_workflows": count_items(all_workflows),
            "key_discussions": all_discussions[:50],
            "problems_solved": all_problems[:30],
            "stats": self.stats.copy(),
        }
    
    def format_report(self, result: dict) -> str:
        """Format result as markdown report."""
        lines = [
            f"# Discord Channel Analysis: #{result['channel']}",
            f"**Server:** {result['guild']}",
            f"**Messages analyzed:** {result['total_messages']:,}",
            f"**Chunks processed:** {result['chunks_analyzed']}",
            "",
            "---",
            "",
            result['synthesis'],
            "",
            "---",
            "",
            "## Top Tools/Nodes/Models Mentioned",
            "",
        ]
        
        for item, count in result['top_tools'][:20]:
            lines.append(f"- **{item}** ({count} mentions)")
        
        lines.extend([
            "",
            "## Problems & Solutions",
            "",
        ])
        
        for prob in result['problems_solved'][:20]:
            if prob and len(prob) > 10:
                lines.append(f"- {prob}")
        
        lines.extend([
            "",
            "---",
            f"*Tokens used: {result['stats']['total_tokens']:,}*",
            f"*Estimated cost: ${result['stats']['total_cost']:.4f}*",
        ])
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Extract insights from Discord exports")
    parser.add_argument("filepath", help="Path to Discord JSON export")
    parser.add_argument("--messages-per-chunk", type=int, default=200, help="Messages per chunk")
    parser.add_argument("--max-chunks", type=int, default=None, help="Max chunks to process")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--rate-limit", type=float, default=0.3, help="Delay between API calls")
    
    args = parser.parse_args()
    
    extractor = DiscordExtractor(rate_limit_delay=args.rate_limit)
    
    result = extractor.process_export(
        args.filepath,
        messages_per_chunk=args.messages_per_chunk,
        max_chunks=args.max_chunks,
    )
    
    report = extractor.format_report(result)
    
    if args.output:
        Path(args.output).write_text(report)
        print(f"\nReport saved to {args.output}", file=sys.stderr)
    else:
        print(report)
    
    print(f"\n--- Stats ---", file=sys.stderr)
    print(f"Messages: {result['stats']['messages_processed']:,}", file=sys.stderr)
    print(f"Chunks: {result['stats']['chunks_processed']}", file=sys.stderr)
    print(f"Tokens: {result['stats']['total_tokens']:,}", file=sys.stderr)
    print(f"Cost: ${result['stats']['total_cost']:.4f}", file=sys.stderr)


if __name__ == "__main__":
    main()

