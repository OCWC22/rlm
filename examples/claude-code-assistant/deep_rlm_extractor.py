#!/usr/bin/env python3
"""
Deep RLM Extractor - Recursive extraction with configurable max recursion steps.

Uses RLM-style recursive sub-LLM calls to extract comprehensive information
from large files. Each sub-LLM can make further sub-LLM calls up to max_recursion steps.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import anthropic
except ImportError:
    print("pip install anthropic", file=sys.stderr)
    sys.exit(1)


@dataclass
class ExtractionResult:
    """Result from a recursive extraction step."""
    level: int
    chunk_id: str
    content: str
    sub_extractions: list['ExtractionResult'] = field(default_factory=list)
    tokens_used: int = 0
    recursion_depth: int = 0


class DeepRLMExtractor:
    """
    Deep recursive extractor using RLM principles.
    
    Each extraction can recursively call sub-LLMs to dive deeper,
    up to max_recursion_steps levels deep.
    """
    
    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        max_recursion_steps: int = 50,
        rate_limit_delay: float = 0.2,
        max_workers: int = 5,
        verbose: bool = True,
    ):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Set ANTHROPIC_API_KEY")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_recursion_steps = max_recursion_steps
        self.rate_limit_delay = rate_limit_delay
        self.max_workers = max_workers
        self.verbose = verbose
        
        self.stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "max_depth_reached": 0,
            "recursion_count": 0,
            "chunks_processed": 0,
        }
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[RLM] {msg}", file=sys.stderr)
    
    def _call_llm(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> tuple[str, int]:
        """Make LLM call with rate limiting."""
        time.sleep(self.rate_limit_delay)
        self.stats["total_calls"] += 1
        
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            
            resp = self.client.messages.create(**kwargs)
            tokens = resp.usage.input_tokens + resp.usage.output_tokens
            self.stats["total_tokens"] += tokens
            return resp.content[0].text, tokens
        except Exception as e:
            self._log(f"ERROR: {e}")
            return f"ERROR: {e}", 0
    
    def _extract_recursive(
        self,
        content: str,
        query: str,
        level: int = 0,
        chunk_id: str = "root",
        context: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Recursively extract information, allowing sub-LLMs to dive deeper.
        
        Args:
            content: Content to analyze
            query: What to extract
            level: Current recursion level (0 = root)
            chunk_id: Identifier for this chunk
            context: Additional context from parent extractions
        """
        if level >= self.max_recursion_steps:
            self.stats["max_depth_reached"] = max(self.stats["max_depth_reached"], level)
            return ExtractionResult(
                level=level,
                chunk_id=chunk_id,
                content="[Max recursion depth reached]",
                recursion_depth=level,
            )
        
        self.stats["recursion_count"] += 1
        self.stats["max_depth_reached"] = max(self.stats["max_depth_reached"], level)
        
        # Build prompt
        system_prompt = """You are an expert information extractor using recursive decomposition.

Your task is to extract comprehensive information from the given content. You can:
1. Extract information directly from the content
2. Identify areas that need deeper analysis
3. Make recursive sub-extractions by calling sub-LLMs on specific sections

When you identify areas needing deeper analysis, explicitly mark them and suggest
what sub-queries would be useful. The system will automatically make recursive calls.

Be thorough and extract EVERYTHING relevant to the query."""
        
        prompt = f"""EXTRACTION TASK (Level {level}, Chunk: {chunk_id}):
Query: {query}

{f"CONTEXT FROM PARENT EXTRACTIONS:\n{context}\n\n" if context else ""}
CONTENT TO ANALYZE:
{content[:50000]}  # Limit to avoid token overflow

INSTRUCTIONS:
1. Extract ALL relevant information related to the query
2. Be comprehensive - don't skip details
3. If you identify sections that need deeper analysis, list them explicitly
4. Format your extraction clearly with sections and subsections

EXTRACTION:"""
        
        response, tokens = self._call_llm(prompt, system_prompt, max_tokens=4096)
        
        result = ExtractionResult(
            level=level,
            chunk_id=chunk_id,
            content=response,
            tokens_used=tokens,
            recursion_depth=level,
        )
        
        # Check if response suggests deeper analysis needed
        if level < self.max_recursion_steps - 1:
            # Look for sections that might need deeper analysis
            # This is a heuristic - in a full RLM, the LLM would explicitly
            # call sub-LLMs, but here we detect and do it automatically
            
            # If content is very long or mentions "need more analysis", recurse
            if len(content) > 20000 or "deeper analysis" in response.lower():
                # Split content and recurse on sub-sections
                sub_sections = self._split_for_recursion(content)
                if len(sub_sections) > 1:
                    self._log(f"  Level {level}: Recursing into {len(sub_sections)} sub-sections")
                    for i, sub_content in enumerate(sub_sections[:3]):  # Limit to 3 sub-calls per level
                        sub_result = self._extract_recursive(
                            sub_content,
                            query,
                            level=level + 1,
                            chunk_id=f"{chunk_id}.{i}",
                            context=response[:1000],  # Pass parent context
                        )
                        result.sub_extractions.append(sub_result)
        
        return result
    
    def _split_for_recursion(self, content: str) -> list[str]:
        """Split content into sub-sections for recursive analysis."""
        # Try to split by natural boundaries
        if "\n\n" in content:
            sections = content.split("\n\n")
            # Group into reasonable chunks
            chunks = []
            current = []
            current_size = 0
            for section in sections:
                if current_size + len(section) > 10000 and current:
                    chunks.append("\n\n".join(current))
                    current = [section]
                    current_size = len(section)
                else:
                    current.append(section)
                    current_size += len(section)
            if current:
                chunks.append("\n\n".join(current))
            return chunks if len(chunks) > 1 else [content]
        
        # Fallback: split by size
        chunk_size = len(content) // 3
        if chunk_size > 5000:
            return [
                content[i:i + chunk_size]
                for i in range(0, len(content), chunk_size)
            ]
        
        return [content]
    
    def process_discord_export(
        self,
        filepath: str | Path,
        query: str = "Extract everything: topics, workflows, tools, problems, solutions, techniques, patterns, and insights",
        messages_per_chunk: int = 500,
        max_chunks: Optional[int] = None,
    ) -> dict:
        """
        Process Discord export with deep recursive extraction.
        """
        filepath = Path(filepath).expanduser()
        
        self._log(f"[1/5] Loading {filepath.name}...")
        with open(filepath) as f:
            data = json.load(f)
        
        channel_name = data.get("channel", {}).get("name", "unknown")
        messages = data.get("messages", [])
        
        self._log(f"  Channel: #{channel_name}")
        self._log(f"  Messages: {len(messages):,}")
        
        # Format messages
        self._log(f"\n[2/5] Formatting messages...")
        formatted_messages = []
        for msg in messages:
            author = msg.get("author", {}).get("name", "Unknown")
            content = msg.get("content", "").strip()
            timestamp = msg.get("timestamp", "")[:10]
            if content:
                formatted_messages.append(f"[{timestamp}] {author}: {content}")
        
        full_text = "\n".join(formatted_messages)
        self._log(f"  Formatted: {len(full_text):,} characters")
        
        # Chunk
        self._log(f"\n[3/5] Chunking into groups of {messages_per_chunk}...")
        chunks = []
        for i in range(0, len(formatted_messages), messages_per_chunk):
            chunk = "\n".join(formatted_messages[i:i + messages_per_chunk])
            chunks.append((f"chunk_{i//messages_per_chunk}", chunk))
            if max_chunks and len(chunks) >= max_chunks:
                break
        
        self._log(f"  Created {len(chunks)} chunks")
        
        # Process chunks in parallel with recursive extraction
        self._log(f"\n[4/5] Deep recursive extraction (max {self.max_recursion_steps} steps)...")
        results = []
        
        def process_chunk(chunk_id: str, content: str) -> ExtractionResult:
            self._log(f"  Processing {chunk_id}...")
            self.stats["chunks_processed"] += 1
            return self._extract_recursive(content, query, level=0, chunk_id=chunk_id)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_chunk, chunk_id, content): chunk_id
                for chunk_id, content in chunks
            }
            
            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    self._log(f"  ✓ {chunk_id}: {result.tokens_used} tokens, depth={result.recursion_depth}")
                except Exception as e:
                    self._log(f"  ✗ {chunk_id}: {e}")
        
        results.sort(key=lambda r: r.chunk_id)
        
        # Aggregate all results
        self._log(f"\n[5/5] Aggregating {len(results)} extractions...")
        aggregated = self._aggregate_results(results, channel_name, len(messages))
        
        return aggregated
    
    def _aggregate_results(
        self,
        results: list[ExtractionResult],
        channel_name: str,
        total_messages: int,
    ) -> dict:
        """Aggregate all extraction results into final report."""
        
        # Collect all content (including sub-extractions)
        all_content = []
        
        def collect_content(result: ExtractionResult):
            all_content.append(f"=== {result.chunk_id} (Level {result.level}) ===\n{result.content}")
            for sub in result.sub_extractions:
                collect_content(sub)
        
        for result in results:
            collect_content(result)
        
        combined = "\n\n".join(all_content)
        
        # Final synthesis
        synthesis_prompt = f"""Synthesize a comprehensive report from {len(results)} deep extractions
of the #{channel_name} Discord channel ({total_messages:,} messages).

The extractions used recursive sub-LLM calls (up to {self.stats['max_depth_reached']} levels deep)
to ensure thorough analysis.

EXTRACTIONS:
{combined[:100000]}  # Limit size

Create a well-organized markdown report covering:
1. **Main Themes & Topics** - What does this community discuss?
2. **Popular Tools, Nodes, Workflows** - Technical stack and tools
3. **Common Problems & Solutions** - Troubleshooting patterns
4. **Notable Techniques** - Advanced tips and tricks
5. **Community Patterns** - Behavioral insights
6. **Key Insights** - Important takeaways

Be comprehensive and cite specific examples from the extractions."""
        
        # Haiku max is 4096, Sonnet can go higher
        max_synthesis_tokens = 4096 if "haiku" in self.model.lower() else 6000
        final_report, tokens = self._call_llm(synthesis_prompt, max_tokens=max_synthesis_tokens)
        self.stats["total_tokens"] += tokens
        
        return {
            "channel": channel_name,
            "total_messages": total_messages,
            "chunks_processed": len(results),
            "max_recursion_depth": self.stats["max_depth_reached"],
            "total_recursion_calls": self.stats["recursion_count"],
            "report": final_report,
            "stats": self.stats.copy(),
        }
    
    def format_report(self, result: dict) -> str:
        """Format result as markdown report."""
        lines = [
            f"# Deep RLM Extraction Report: #{result['channel']}",
            "",
            f"**Messages analyzed:** {result['total_messages']:,}",
            f"**Chunks processed:** {result['chunks_processed']}",
            f"**Max recursion depth:** {result['max_recursion_depth']}",
            f"**Total recursion calls:** {result['total_recursion_calls']}",
            "",
            "---",
            "",
            result['report'],
            "",
            "---",
            "",
            "## Statistics",
            "",
            f"- **Total LLM calls:** {result['stats']['total_calls']:,}",
            f"- **Total tokens:** {result['stats']['total_tokens']:,}",
            f"- **Estimated cost:** ${result['stats']['total_tokens'] * 0.00025 / 1000:.4f}",
        ]
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Deep RLM extractor with recursive sub-LLM calls"
    )
    parser.add_argument("filepath", help="Path to Discord JSON export")
    parser.add_argument("--query", "-q", default="Extract everything: topics, workflows, tools, problems, solutions, techniques, patterns, and insights",
                       help="Extraction query")
    parser.add_argument("--messages-per-chunk", type=int, default=500,
                       help="Messages per chunk")
    parser.add_argument("--max-chunks", type=int, default=None,
                       help="Max chunks to process")
    parser.add_argument("--max-recursion", type=int, default=50,
                       help="Max recursion steps (default: 50)")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--rate-limit", type=float, default=0.2,
                       help="Delay between API calls")
    
    args = parser.parse_args()
    
    extractor = DeepRLMExtractor(
        max_recursion_steps=args.max_recursion,
        rate_limit_delay=args.rate_limit,
        verbose=True,
    )
    
    result = extractor.process_discord_export(
        args.filepath,
        query=args.query,
        messages_per_chunk=args.messages_per_chunk,
        max_chunks=args.max_chunks,
    )
    
    report = extractor.format_report(result)
    
    if args.output:
        Path(args.output).write_text(report)
        print(f"\nReport saved to {args.output}", file=sys.stderr)
    else:
        print(report)
    
    print(f"\n--- Final Stats ---", file=sys.stderr)
    print(f"Total calls: {result['stats']['total_calls']:,}", file=sys.stderr)
    print(f"Total tokens: {result['stats']['total_tokens']:,}", file=sys.stderr)
    print(f"Max depth: {result['max_recursion_depth']}", file=sys.stderr)
    print(f"Recursion calls: {result['total_recursion_calls']}", file=sys.stderr)


if __name__ == "__main__":
    main()

