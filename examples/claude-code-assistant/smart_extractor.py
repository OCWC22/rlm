#!/usr/bin/env python3
"""
Smart Conversation Extractor - Detailed but Cost-Efficient.

Strategy:
1. First pass: Use cheap/fast model to identify which conversations have interesting content
2. Second pass: Deep dive only on interesting ones with better model
3. Rate limiting to avoid API throttling
4. Structured extraction to minimize tokens

Cost optimization:
- claude-3-haiku for scanning (cheap)
- claude-sonnet-4-20250514 only for deep extraction
- Aggressive summarization in prompts
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
class ConversationSummary:
    """Structured summary of a conversation."""
    index: int
    project: str
    message_count: int
    # Extracted details
    tasks: list[str] = field(default_factory=list)
    solutions: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    commands_run: list[str] = field(default_factory=list)
    errors_encountered: list[str] = field(default_factory=list)
    key_insights: list[str] = field(default_factory=list)
    # Meta
    tokens_used: int = 0
    is_interesting: bool = False


class SmartExtractor:
    """
    Two-pass extractor for cost efficiency.
    """
    
    def __init__(
        self,
        scan_model: str = "claude-3-haiku-20240307",
        deep_model: str = "claude-sonnet-4-20250514",
        rate_limit_delay: float = 0.5,
        max_workers: int = 3,
    ):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Set ANTHROPIC_API_KEY")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.scan_model = scan_model
        self.deep_model = deep_model
        self.rate_limit_delay = rate_limit_delay
        self.max_workers = max_workers
        
        self.stats = {
            "conversations_scanned": 0,
            "conversations_deep_analyzed": 0,
            "total_tokens": 0,
            "total_cost_estimate": 0.0,
        }
    
    def _call_llm(self, prompt: str, model: str, max_tokens: int = 1024) -> tuple[str, int]:
        """Make LLM call, return (response, tokens_used)."""
        time.sleep(self.rate_limit_delay)  # Rate limit
        
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
    
    def _truncate_conversation(self, conv: dict, max_messages: int = 30) -> str:
        """Truncate conversation to fit in context, keeping first and last messages."""
        messages = conv.get("messages", [])
        project = conv.get("project_name", "unknown")
        
        if len(messages) <= max_messages:
            selected = messages
        else:
            # Keep first 10, last 10, and sample middle
            first = messages[:10]
            last = messages[-10:]
            middle_indices = range(10, len(messages) - 10, max(1, (len(messages) - 20) // 10))
            middle = [messages[i] for i in middle_indices]
            selected = first + middle + last
        
        # Format compactly
        lines = [f"Project: {project}", f"Total messages: {len(messages)}", "---"]
        for msg in selected:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"[{role}]: {content[:200]}")
        
        return "\n".join(lines)
    
    def scan_conversation(self, conv: dict, index: int) -> ConversationSummary:
        """Quick scan to determine if conversation is interesting."""
        project = conv.get("project_name", "unknown")
        messages = conv.get("messages", [])
        
        summary = ConversationSummary(
            index=index,
            project=project,
            message_count=len(messages),
        )
        
        # Quick heuristics first (free)
        content_str = json.dumps(conv).lower()
        interesting_keywords = [
            "error", "bug", "fix", "problem", "issue", "fail",
            "implement", "create", "build", "design", "architecture",
            "database", "api", "deploy", "test", "debug",
        ]
        
        keyword_count = sum(1 for kw in interesting_keywords if kw in content_str)
        
        if keyword_count < 2 or len(messages) < 5:
            # Skip boring conversations
            summary.is_interesting = False
            return summary
        
        # Quick LLM scan with cheap model
        truncated = self._truncate_conversation(conv, max_messages=20)
        
        prompt = f"""Quickly scan this conversation and extract key points in JSON format.
Be concise - just capture the essence.

CONVERSATION:
{truncated}

Return JSON with these fields (use empty arrays if none):
{{"tasks": ["task1", "task2"], "files": ["file1.py"], "commands": ["cmd1"], "has_errors": true/false, "summary": "one line"}}

JSON:"""
        
        response, tokens = self._call_llm(prompt, self.scan_model, max_tokens=500)
        summary.tokens_used = tokens
        self.stats["total_tokens"] += tokens
        self.stats["conversations_scanned"] += 1
        
        # Parse response
        try:
            # Find JSON in response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                summary.tasks = data.get("tasks", [])
                summary.files_modified = data.get("files", [])
                summary.commands_run = data.get("commands", [])
                summary.is_interesting = bool(data.get("has_errors")) or len(summary.tasks) > 0
                summary.key_insights = [data.get("summary", "")]
        except json.JSONDecodeError:
            summary.key_insights = [response[:200]]
            summary.is_interesting = True  # Assume interesting if parsing failed
        
        return summary
    
    def deep_analyze(self, conv: dict, summary: ConversationSummary) -> ConversationSummary:
        """Deep analysis of interesting conversation."""
        truncated = self._truncate_conversation(conv, max_messages=50)
        
        prompt = f"""Analyze this conversation in detail. Extract EVERY specific action taken.

CONVERSATION:
{truncated}

Provide a detailed JSON extraction:
{{
  "tasks": ["Specific task 1 with details", "Specific task 2..."],
  "solutions": ["How task 1 was solved", "How task 2 was solved..."],
  "files_modified": ["path/to/file1.py", "path/to/file2.ts"],
  "commands_run": ["npm install X", "git commit..."],
  "errors_encountered": ["Error message 1", "Error message 2"],
  "key_code_changes": ["Changed function X to do Y", "Added class Z"],
  "insights": ["Important learning 1", "Important learning 2"]
}}

Be thorough but concise. JSON:"""
        
        response, tokens = self._call_llm(prompt, self.deep_model, max_tokens=1500)
        summary.tokens_used += tokens
        self.stats["total_tokens"] += tokens
        self.stats["conversations_deep_analyzed"] += 1
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                summary.tasks = data.get("tasks", summary.tasks)
                summary.solutions = data.get("solutions", [])
                summary.files_modified = data.get("files_modified", summary.files_modified)
                summary.commands_run = data.get("commands_run", summary.commands_run)
                summary.errors_encountered = data.get("errors_encountered", [])
                summary.key_insights = data.get("insights", summary.key_insights)
        except json.JSONDecodeError:
            summary.key_insights.append(f"[Parse error] {response[:300]}")
        
        return summary
    
    def process_file(
        self,
        filepath: Path,
        max_conversations: Optional[int] = None,
        deep_analyze_top_n: int = 10,
    ) -> list[ConversationSummary]:
        """
        Process JSONL file with two-pass extraction.
        
        Args:
            filepath: Path to JSONL file
            max_conversations: Limit total conversations to scan
            deep_analyze_top_n: Number of interesting conversations to deep analyze
        """
        filepath = Path(filepath).expanduser()
        
        # Load conversations
        conversations = []
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                if max_conversations and i >= max_conversations:
                    break
                try:
                    conversations.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        print(f"[1/3] Loaded {len(conversations)} conversations", file=sys.stderr)
        
        # Pass 1: Quick scan (parallel)
        print(f"[2/3] Quick scanning with {self.scan_model}...", file=sys.stderr)
        summaries = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.scan_conversation, conv, i): i
                for i, conv in enumerate(conversations)
            }
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    summary = future.result()
                    summaries.append(summary)
                    status = "★" if summary.is_interesting else "·"
                    print(f"  {status} Conv {idx + 1}: {summary.project[:30]} ({summary.message_count} msgs)", file=sys.stderr)
                except Exception as e:
                    print(f"  ✗ Conv {idx + 1}: {e}", file=sys.stderr)
        
        # Sort by interestingness (message count + has tasks)
        interesting = [s for s in summaries if s.is_interesting]
        interesting.sort(key=lambda s: (len(s.tasks), s.message_count), reverse=True)
        
        print(f"\n[3/3] Deep analyzing top {min(deep_analyze_top_n, len(interesting))} interesting conversations with {self.deep_model}...", file=sys.stderr)
        
        # Pass 2: Deep analyze top N
        for i, summary in enumerate(interesting[:deep_analyze_top_n]):
            conv = conversations[summary.index]
            print(f"  → Deep analyzing conv {summary.index + 1}: {summary.project[:40]}...", file=sys.stderr)
            self.deep_analyze(conv, summary)
        
        # Estimate cost
        # Haiku: $0.25/M input, $1.25/M output (estimate 50/50 split)
        # Sonnet: $3/M input, $15/M output
        haiku_tokens = self.stats["conversations_scanned"] * 500  # Rough estimate
        sonnet_tokens = self.stats["conversations_deep_analyzed"] * 1500
        self.stats["total_cost_estimate"] = (haiku_tokens * 0.00075 + sonnet_tokens * 0.009) / 1000
        
        return summaries
    
    def format_report(self, summaries: list[ConversationSummary]) -> str:
        """Generate a detailed report."""
        lines = ["# Conversation Extraction Report\n"]
        
        # Stats
        interesting = [s for s in summaries if s.is_interesting]
        lines.append(f"**Total conversations:** {len(summaries)}")
        lines.append(f"**Interesting:** {len(interesting)}")
        lines.append(f"**Tokens used:** {self.stats['total_tokens']:,}")
        lines.append(f"**Estimated cost:** ${self.stats['total_cost_estimate']:.4f}")
        lines.append("")
        
        # Detailed findings
        lines.append("## Detailed Findings\n")
        
        for s in sorted(interesting, key=lambda x: len(x.tasks), reverse=True):
            lines.append(f"### Conv {s.index + 1}: {s.project}")
            lines.append(f"*{s.message_count} messages*\n")
            
            if s.tasks:
                lines.append("**Tasks:**")
                for t in s.tasks:
                    lines.append(f"- {t}")
                lines.append("")
            
            if s.solutions:
                lines.append("**Solutions:**")
                for sol in s.solutions:
                    lines.append(f"- {sol}")
                lines.append("")
            
            if s.files_modified:
                lines.append(f"**Files:** `{'`, `'.join(s.files_modified[:10])}`")
                lines.append("")
            
            if s.commands_run:
                lines.append("**Commands:**")
                for cmd in s.commands_run[:5]:
                    lines.append(f"```\n{cmd}\n```")
                lines.append("")
            
            if s.errors_encountered:
                lines.append("**Errors:**")
                for err in s.errors_encountered[:5]:
                    lines.append(f"- {err}")
                lines.append("")
            
            if s.key_insights:
                lines.append("**Insights:**")
                for ins in s.key_insights:
                    if ins:
                        lines.append(f"- {ins}")
                lines.append("")
            
            lines.append("---\n")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Smart two-pass conversation extractor")
    parser.add_argument("filepath", help="Path to JSONL file")
    parser.add_argument("--max-convs", type=int, default=None, help="Max conversations to scan")
    parser.add_argument("--deep-top-n", type=int, default=10, help="Deep analyze top N interesting")
    parser.add_argument("--rate-limit", type=float, default=0.3, help="Delay between API calls (seconds)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    extractor = SmartExtractor(rate_limit_delay=args.rate_limit)
    
    summaries = extractor.process_file(
        args.filepath,
        max_conversations=args.max_convs,
        deep_analyze_top_n=args.deep_top_n,
    )
    
    report = extractor.format_report(summaries)
    
    if args.output:
        Path(args.output).write_text(report)
        print(f"\nReport saved to {args.output}", file=sys.stderr)
    else:
        print(report)
    
    print(f"\n--- Stats ---", file=sys.stderr)
    print(f"Scanned: {extractor.stats['conversations_scanned']}", file=sys.stderr)
    print(f"Deep analyzed: {extractor.stats['conversations_deep_analyzed']}", file=sys.stderr)
    print(f"Total tokens: {extractor.stats['total_tokens']:,}", file=sys.stderr)
    print(f"Estimated cost: ${extractor.stats['total_cost_estimate']:.4f}", file=sys.stderr)


if __name__ == "__main__":
    main()

