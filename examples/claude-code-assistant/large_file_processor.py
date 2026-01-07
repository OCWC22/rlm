#!/usr/bin/env python3
"""
Large File Processor using RLM approach.

Handles files too large for LLM context windows by:
1. Reading in chunks (streaming)
2. Processing each chunk with sub-LLM calls
3. Aggregating results

Perfect for:
- Large JSONL files (conversation logs, data exports)
- Huge log files
- Large codebases
- Any file > 256KB

Usage:
    python large_file_processor.py path/to/large_file.jsonl "Summarize the conversations"
    python large_file_processor.py path/to/large_file.jsonl "Find all error messages" --format jsonl
    python large_file_processor.py path/to/large_file.jsonl "Extract key themes" --sample 100
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Iterator, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time

# Try to import LLM clients
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class ChunkResult:
    """Result from processing a chunk."""
    chunk_index: int
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    elapsed: float = 0.0
    error: Optional[str] = None


def read_jsonl_chunks(
    filepath: Path,
    lines_per_chunk: int = 100,
    max_chunks: Optional[int] = None,
    sample_every: Optional[int] = None,
) -> Iterator[tuple[int, list[dict]]]:
    """
    Read JSONL file in chunks.
    
    Args:
        filepath: Path to JSONL file
        lines_per_chunk: Lines per chunk
        max_chunks: Maximum number of chunks to return
        sample_every: Sample every N lines (for large files)
    
    Yields:
        (chunk_index, list of parsed JSON objects)
    """
    chunk = []
    chunk_idx = 0
    line_count = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            
            # Sampling
            if sample_every and line_num % sample_every != 0:
                continue
            
            try:
                obj = json.loads(line)
                chunk.append(obj)
                line_count += 1
            except json.JSONDecodeError:
                continue
            
            if len(chunk) >= lines_per_chunk:
                yield (chunk_idx, chunk)
                chunk = []
                chunk_idx += 1
                
                if max_chunks and chunk_idx >= max_chunks:
                    return
    
    # Yield remaining
    if chunk:
        yield (chunk_idx, chunk)


def read_text_chunks(
    filepath: Path,
    chunk_size: int = 50_000,  # Characters
    max_chunks: Optional[int] = None,
) -> Iterator[tuple[int, str]]:
    """
    Read text file in character chunks.
    
    Tries to break at line boundaries.
    """
    chunk_idx = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        buffer = ""
        
        while True:
            # Read more data
            data = f.read(chunk_size)
            if not data:
                break
            
            buffer += data
            
            # Find last newline for clean break
            last_newline = buffer.rfind('\n')
            if last_newline > 0:
                yield (chunk_idx, buffer[:last_newline])
                buffer = buffer[last_newline + 1:]
                chunk_idx += 1
                
                if max_chunks and chunk_idx >= max_chunks:
                    return
            elif len(buffer) > chunk_size * 2:
                # Force break if no newlines
                yield (chunk_idx, buffer[:chunk_size])
                buffer = buffer[chunk_size:]
                chunk_idx += 1
                
                if max_chunks and chunk_idx >= max_chunks:
                    return
        
        # Yield remaining
        if buffer:
            yield (chunk_idx, buffer)


class LargeFileProcessor:
    """
    Process large files using RLM-style chunking.
    """
    
    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        max_workers: int = 3,
        verbose: bool = True,
    ):
        self.provider = provider
        self.model = model
        self.max_workers = max_workers
        self.verbose = verbose
        
        self._init_client()
        
        self.stats = {
            "chunks_processed": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_time": 0.0,
        }
    
    def _init_client(self):
        """Initialize the LLM client."""
        if self.provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise ImportError("pip install anthropic")
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Set ANTHROPIC_API_KEY environment variable")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = self.model or "claude-sonnet-4-20250514"
        
        elif self.provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("pip install openai")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("Set OPENAI_API_KEY environment variable")
            self.client = OpenAI(api_key=api_key)
            self.model = self.model or "gpt-4.1"
        
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[RLM] {msg}", file=sys.stderr)
    
    def _query_llm(self, prompt: str, system: Optional[str] = None) -> ChunkResult:
        """Make a single LLM call."""
        start = time.perf_counter()
        
        try:
            if self.provider == "anthropic":
                resp = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=system or "You are a helpful data analyst.",
                    messages=[{"role": "user", "content": prompt}],
                )
                elapsed = time.perf_counter() - start
                return ChunkResult(
                    chunk_index=-1,
                    content=resp.content[0].text,
                    tokens_in=resp.usage.input_tokens,
                    tokens_out=resp.usage.output_tokens,
                    elapsed=elapsed,
                )
            
            elif self.provider == "openai":
                resp = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[
                        {"role": "system", "content": system or "You are a helpful data analyst."},
                        {"role": "user", "content": prompt},
                    ],
                )
                elapsed = time.perf_counter() - start
                return ChunkResult(
                    chunk_index=-1,
                    content=resp.choices[0].message.content,
                    tokens_in=resp.usage.prompt_tokens,
                    tokens_out=resp.usage.completion_tokens,
                    elapsed=elapsed,
                )
        
        except Exception as e:
            return ChunkResult(
                chunk_index=-1,
                content="",
                elapsed=time.perf_counter() - start,
                error=str(e),
            )
    
    def process_jsonl(
        self,
        filepath: str | Path,
        query: str,
        lines_per_chunk: int = 50,
        max_chunks: Optional[int] = None,
        sample_every: Optional[int] = None,
    ) -> str:
        """
        Process a large JSONL file.
        
        Args:
            filepath: Path to JSONL file
            query: What to analyze/extract
            lines_per_chunk: How many JSON lines per chunk
            max_chunks: Maximum chunks to process (None = all)
            sample_every: Sample every N lines (for huge files)
        
        Returns:
            Aggregated analysis result
        """
        filepath = Path(filepath).expanduser()
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_size = filepath.stat().st_size
        self._log(f"Processing {filepath.name} ({file_size / 1024 / 1024:.1f} MB)")
        
        # Collect chunks
        chunks = list(read_jsonl_chunks(
            filepath,
            lines_per_chunk=lines_per_chunk,
            max_chunks=max_chunks,
            sample_every=sample_every,
        ))
        
        self._log(f"Split into {len(chunks)} chunks")
        
        # Process chunks in parallel
        chunk_results = self._process_chunks_parallel(chunks, query, is_jsonl=True)
        
        # Aggregate
        return self._aggregate_results(chunk_results, query)
    
    def process_text(
        self,
        filepath: str | Path,
        query: str,
        chunk_size: int = 50_000,
        max_chunks: Optional[int] = None,
    ) -> str:
        """
        Process a large text file.
        """
        filepath = Path(filepath).expanduser()
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_size = filepath.stat().st_size
        self._log(f"Processing {filepath.name} ({file_size / 1024 / 1024:.1f} MB)")
        
        # Collect chunks
        chunks = list(read_text_chunks(
            filepath,
            chunk_size=chunk_size,
            max_chunks=max_chunks,
        ))
        
        self._log(f"Split into {len(chunks)} chunks")
        
        # Process chunks in parallel
        chunk_results = self._process_chunks_parallel(chunks, query, is_jsonl=False)
        
        # Aggregate
        return self._aggregate_results(chunk_results, query)
    
    def _process_chunks_parallel(
        self,
        chunks: list,
        query: str,
        is_jsonl: bool = True,
    ) -> list[ChunkResult]:
        """Process chunks in parallel."""
        results = []
        
        def process_one(chunk_data):
            idx, data = chunk_data
            
            if is_jsonl:
                # Format JSONL data
                content = json.dumps(data, indent=2, ensure_ascii=False)
                prompt = f"""Analyze this chunk of JSON data (chunk {idx + 1}).

TASK: {query}

DATA:
{content}

Provide a focused analysis relevant to the task. If this chunk doesn't contain relevant information, say "No relevant data in this chunk."

ANALYSIS:"""
            else:
                # Plain text
                prompt = f"""Analyze this chunk of text (chunk {idx + 1}).

TASK: {query}

TEXT:
{data}

Provide a focused analysis relevant to the task. If this chunk doesn't contain relevant information, say "No relevant data in this chunk."

ANALYSIS:"""
            
            result = self._query_llm(prompt)
            result.chunk_index = idx
            return result
        
        # Process in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(process_one, chunk): chunk[0] for chunk in chunks}
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    self.stats["chunks_processed"] += 1
                    self.stats["total_tokens_in"] += result.tokens_in
                    self.stats["total_tokens_out"] += result.tokens_out
                    self.stats["total_time"] += result.elapsed
                    
                    if self.verbose:
                        status = "✓" if not result.error else "✗"
                        print(f"  [{status}] Chunk {idx + 1}: {result.tokens_in + result.tokens_out} tokens, {result.elapsed:.1f}s", file=sys.stderr)
                
                except Exception as e:
                    results.append(ChunkResult(
                        chunk_index=idx,
                        content="",
                        error=str(e),
                    ))
        
        # Sort by chunk index
        results.sort(key=lambda r: r.chunk_index)
        return results
    
    def _aggregate_results(self, results: list[ChunkResult], query: str) -> str:
        """Aggregate chunk results into final answer."""
        # Filter out errors and empty results
        findings = []
        for r in results:
            if r.error:
                continue
            if "No relevant data" in r.content:
                continue
            findings.append(f"[Chunk {r.chunk_index + 1}]\n{r.content}")
        
        if not findings:
            return "No relevant information found in the file."
        
        self._log(f"Aggregating {len(findings)} findings...")
        
        # Synthesize
        prompt = f"""Based on analysis of multiple chunks from a large file, provide a comprehensive answer.

ORIGINAL TASK: {query}

FINDINGS FROM CHUNKS:
{"=" * 40}
{chr(10).join(findings)}
{"=" * 40}

Synthesize all findings into a clear, comprehensive response. Cite specific chunks when relevant."""

        result = self._query_llm(prompt)
        
        self.stats["total_tokens_in"] += result.tokens_in
        self.stats["total_tokens_out"] += result.tokens_out
        self.stats["total_time"] += result.elapsed
        
        if result.error:
            return f"Aggregation failed: {result.error}\n\nRaw findings:\n" + "\n\n".join(findings)
        
        return result.content
    
    def get_stats(self) -> dict:
        return self.stats.copy()


def main():
    parser = argparse.ArgumentParser(
        description="Process large files using RLM approach",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a large JSONL file
  python large_file_processor.py data.jsonl "Summarize the conversations"

  # Sample every 10th line for huge files
  python large_file_processor.py huge.jsonl "Find patterns" --sample 10

  # Limit to first 20 chunks
  python large_file_processor.py data.jsonl "Extract errors" --max-chunks 20

  # Process plain text file
  python large_file_processor.py logs.txt "Find error messages" --format text

  # Use OpenAI instead of Anthropic
  python large_file_processor.py data.jsonl "Analyze" --provider openai
        """,
    )
    
    parser.add_argument("filepath", help="Path to large file")
    parser.add_argument("query", help="What to analyze/extract")
    parser.add_argument("--format", "-f", choices=["jsonl", "text", "auto"], default="auto",
                        help="File format (default: auto-detect)")
    parser.add_argument("--provider", "-p", choices=["anthropic", "openai"], default="anthropic",
                        help="LLM provider")
    parser.add_argument("--lines-per-chunk", type=int, default=50,
                        help="Lines per chunk for JSONL (default: 50)")
    parser.add_argument("--chunk-size", type=int, default=50000,
                        help="Characters per chunk for text (default: 50000)")
    parser.add_argument("--max-chunks", type=int, default=None,
                        help="Maximum chunks to process")
    parser.add_argument("--sample", type=int, default=None,
                        help="Sample every N lines (for huge files)")
    parser.add_argument("--workers", type=int, default=3,
                        help="Parallel workers (default: 3)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress progress output")
    
    args = parser.parse_args()
    
    filepath = Path(args.filepath).expanduser()
    
    # Auto-detect format
    if args.format == "auto":
        if filepath.suffix.lower() in [".jsonl", ".ndjson"]:
            file_format = "jsonl"
        else:
            file_format = "text"
    else:
        file_format = args.format
    
    try:
        processor = LargeFileProcessor(
            provider=args.provider,
            max_workers=args.workers,
            verbose=not args.quiet,
        )
        
        if file_format == "jsonl":
            result = processor.process_jsonl(
                filepath,
                args.query,
                lines_per_chunk=args.lines_per_chunk,
                max_chunks=args.max_chunks,
                sample_every=args.sample,
            )
        else:
            result = processor.process_text(
                filepath,
                args.query,
                chunk_size=args.chunk_size,
                max_chunks=args.max_chunks,
            )
        
        print(result)
        
        if not args.quiet:
            stats = processor.get_stats()
            print(f"\n--- Stats ---", file=sys.stderr)
            print(f"Chunks: {stats['chunks_processed']}", file=sys.stderr)
            print(f"Tokens: {stats['total_tokens_in']} in, {stats['total_tokens_out']} out", file=sys.stderr)
            print(f"Time: {stats['total_time']:.1f}s", file=sys.stderr)
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

