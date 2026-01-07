"""
RLM Context Extension for CLI Coding Agents.

Inspired by:
- Original RLM paper: https://arxiv.org/abs/2512.24601v1
- Prime Intellect RLMEnv: https://github.com/PrimeIntellect-ai/verifiers

This module provides context window extension using RLM-style recursive
decomposition. Works with Claude Code, Codex CLI, or direct API calls.

Key Features:
- Intelligent chunking (code-aware, semantic, markdown)
- Parallel sub-LLM calls via llm_batch()
- Session persistence
- Exa MCP research integration
"""

import os
import re
import json
import time
import hashlib
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from abc import ABC, abstractmethod

# Optional imports
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


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Chunk:
    """A chunk of context with metadata."""
    content: str
    index: int
    total: int
    metadata: dict = field(default_factory=dict)
    
    @property
    def size(self) -> int:
        return len(self.content)


@dataclass 
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    elapsed_seconds: float = 0.0
    success: bool = True
    error: Optional[str] = None


# =============================================================================
# LLM Clients
# =============================================================================

class BaseLLMClient(ABC):
    """Abstract base for LLM clients."""
    
    @abstractmethod
    def query(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        pass
    
    @abstractmethod
    def get_context_limit(self) -> int:
        """Return max context in characters."""
        pass


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ):
        if not HAS_ANTHROPIC:
            raise ImportError("pip install anthropic")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        
        self.model = model
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def get_context_limit(self) -> int:
        return 800_000  # ~200K tokens
    
    def query(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        start = time.perf_counter()
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system or "You are a helpful coding assistant.",
                messages=[{"role": "user", "content": prompt}],
            )
            elapsed = time.perf_counter() - start
            return LLMResponse(
                content=resp.content[0].text,
                model=self.model,
                tokens_in=resp.usage.input_tokens,
                tokens_out=resp.usage.output_tokens,
                elapsed_seconds=elapsed,
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                elapsed_seconds=time.perf_counter() - start,
                success=False,
                error=str(e),
            )


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT API client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4.1",
        max_tokens: int = 4096,
    ):
        if not HAS_OPENAI:
            raise ImportError("pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required")
        
        self.model = model
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=self.api_key)
    
    def get_context_limit(self) -> int:
        return 500_000  # ~128K tokens
    
    def query(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        start = time.perf_counter()
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system or "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            elapsed = time.perf_counter() - start
            return LLMResponse(
                content=resp.choices[0].message.content,
                model=self.model,
                tokens_in=resp.usage.prompt_tokens,
                tokens_out=resp.usage.completion_tokens,
                elapsed_seconds=elapsed,
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                elapsed_seconds=time.perf_counter() - start,
                success=False,
                error=str(e),
            )


def create_client(provider: str = "anthropic", **kwargs) -> BaseLLMClient:
    """Factory to create LLM client."""
    if provider == "anthropic":
        return AnthropicClient(**kwargs)
    elif provider == "openai":
        return OpenAIClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# =============================================================================
# Chunking Strategies
# =============================================================================

def chunk_fixed_size(content: str, chunk_size: int = 100_000, overlap: int = 1000) -> list[Chunk]:
    """Simple fixed-size chunking with overlap."""
    chunks = []
    start = 0
    idx = 0
    
    while start < len(content):
        end = min(start + chunk_size, len(content))
        
        # Adjust to word boundary
        if end < len(content):
            last_space = content.rfind(' ', start, end)
            if last_space > start:
                end = last_space + 1
        
        chunks.append(Chunk(
            content=content[start:end],
            index=idx,
            total=0,
        ))
        idx += 1
        start = end - overlap if end < len(content) else end
    
    for c in chunks:
        c.total = len(chunks)
    return chunks


def chunk_code_aware(content: str, chunk_size: int = 100_000) -> list[Chunk]:
    """Chunk respecting code structure (functions, classes)."""
    # Find boundaries at function/class definitions
    patterns = [
        r'^(class\s+\w+)',
        r'^(def\s+\w+)',
        r'^(async\s+def\s+\w+)',
        r'^(function\s+\w+)',
    ]
    
    lines = content.split('\n')
    boundaries = [0]
    
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.match(pattern, line):
                if i not in boundaries:
                    boundaries.append(i)
                break
    
    boundaries.append(len(lines))
    
    # Build chunks respecting boundaries
    chunks = []
    current_lines = []
    current_size = 0
    idx = 0
    
    for i in range(len(boundaries) - 1):
        section = lines[boundaries[i]:boundaries[i+1]]
        section_size = sum(len(line) + 1 for line in section)
        
        if current_size + section_size > chunk_size and current_lines:
            chunks.append(Chunk(
                content='\n'.join(current_lines),
                index=idx,
                total=0,
                metadata={"type": "code"},
            ))
            idx += 1
            current_lines = []
            current_size = 0
        
        current_lines.extend(section)
        current_size += section_size
    
    if current_lines:
        chunks.append(Chunk(
            content='\n'.join(current_lines),
            index=idx,
            total=0,
            metadata={"type": "code"},
        ))
    
    for c in chunks:
        c.total = len(chunks)
    return chunks


def chunk_markdown(content: str, chunk_size: int = 100_000) -> list[Chunk]:
    """Chunk by markdown headers."""
    sections = re.split(r'(^#{1,6}\s+.*$)', content, flags=re.MULTILINE)
    
    chunks = []
    current = []
    current_size = 0
    current_header = None
    idx = 0
    
    for section in sections:
        if re.match(r'^#{1,6}\s+', section):
            if current and current_size > chunk_size:
                chunks.append(Chunk(
                    content=''.join(current),
                    index=idx,
                    total=0,
                    metadata={"header": current_header},
                ))
                idx += 1
                current = []
                current_size = 0
            current_header = section.strip()
        
        current.append(section)
        current_size += len(section)
    
    if current:
        chunks.append(Chunk(
            content=''.join(current),
            index=idx,
            total=0,
            metadata={"header": current_header},
        ))
    
    for c in chunks:
        c.total = len(chunks)
    return chunks


def auto_chunk(content: str, chunk_size: int = 100_000) -> list[Chunk]:
    """Auto-detect best chunking strategy."""
    # Check for markdown
    if re.search(r'^#{1,6}\s+', content, re.MULTILINE):
        return chunk_markdown(content, chunk_size)
    
    # Check for code
    code_patterns = [r'def\s+\w+', r'class\s+\w+', r'function\s+\w+', r'import\s+']
    if any(re.search(p, content) for p in code_patterns):
        return chunk_code_aware(content, chunk_size)
    
    # Default to fixed size
    return chunk_fixed_size(content, chunk_size)


# =============================================================================
# RLM Context Engine
# =============================================================================

class RLMContextEngine:
    """
    RLM-style context extension engine.
    
    Implements the map-reduce pattern from the RLM paper:
    1. Chunk large context
    2. Map: Process each chunk with sub-LLM calls
    3. Reduce: Aggregate results into final answer
    
    Similar to Prime Intellect's RLMEnv but simpler and synchronous.
    """
    
    def __init__(
        self,
        client: BaseLLMClient,
        chunk_size: int = 100_000,
        max_workers: int = 4,
        cache_enabled: bool = True,
        verbose: bool = True,
    ):
        self.client = client
        self.chunk_size = chunk_size
        self.max_workers = max_workers
        self.cache_enabled = cache_enabled
        self.verbose = verbose
        
        self._cache: dict[str, str] = {}
        self._variables: dict[str, Any] = {}
        self._stats = {
            "total_chunks": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_time": 0.0,
            "cache_hits": 0,
        }
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"[RLM] {msg}")
    
    def _cache_key(self, content: str, query: str) -> str:
        combined = f"{content[:500]}|{query}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def llm_batch(self, prompts: list[str], system: Optional[str] = None) -> list[str]:
        """
        Make multiple sub-LLM calls in parallel.
        
        This is the key function from the RLM paper - enables recursive
        decomposition by allowing the model to make sub-LLM calls.
        """
        start = time.perf_counter()
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.client.query, p, system): i 
                for i, p in enumerate(prompts)
            }
            
            # Collect results in order
            indexed_results = {}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    resp = future.result()
                    indexed_results[idx] = resp.content
                    self._stats["total_tokens_in"] += resp.tokens_in
                    self._stats["total_tokens_out"] += resp.tokens_out
                except Exception as e:
                    indexed_results[idx] = f"Error: {e}"
            
            results = [indexed_results[i] for i in range(len(prompts))]
        
        elapsed = time.perf_counter() - start
        self._log(f"llm_batch: {len(prompts)} call(s) in {elapsed:.2f}s")
        
        return results
    
    def process(
        self,
        context: str | dict | list,
        query: str,
        system_prompt: Optional[str] = None,
        chunking: str = "auto",  # auto, code, markdown, fixed
    ) -> str:
        """
        Process a query against potentially large context.
        
        If context fits in window, does single call.
        Otherwise, uses chunked map-reduce.
        """
        # Convert to string
        if isinstance(context, (dict, list)):
            context_str = json.dumps(context, indent=2)
        else:
            context_str = str(context)
        
        self._variables["context"] = context_str
        self._variables["query"] = query
        
        context_limit = self.client.get_context_limit()
        
        # Single pass if small enough
        if len(context_str) < context_limit * 0.8:
            self._log(f"Context fits ({len(context_str):,} chars), single pass")
            prompt = f"Context:\n{context_str}\n\nQuery: {query}"
            resp = self.client.query(prompt, system_prompt)
            
            self._stats["total_tokens_in"] += resp.tokens_in
            self._stats["total_tokens_out"] += resp.tokens_out
            
            if not resp.success:
                raise RuntimeError(f"LLM error: {resp.error}")
            
            return resp.content
        
        # Chunked processing
        self._log(f"Context too large ({len(context_str):,} chars), chunking...")
        return self._chunked_process(context_str, query, system_prompt, chunking)
    
    def _chunked_process(
        self,
        context: str,
        query: str,
        system_prompt: Optional[str],
        chunking: str,
    ) -> str:
        """Map-reduce processing for large context."""
        # Chunk
        if chunking == "code":
            chunks = chunk_code_aware(context, self.chunk_size)
        elif chunking == "markdown":
            chunks = chunk_markdown(context, self.chunk_size)
        elif chunking == "fixed":
            chunks = chunk_fixed_size(context, self.chunk_size)
        else:
            chunks = auto_chunk(context, self.chunk_size)
        
        self._stats["total_chunks"] = len(chunks)
        self._log(f"Created {len(chunks)} chunks")
        self._variables["chunks"] = [{"index": c.index, "size": c.size} for c in chunks]
        
        # Map phase: process each chunk
        map_prompt_template = """You are analyzing chunk {index} of {total} of a larger context.

TASK: {query}

Analyze this chunk and extract any relevant information for the task.
If this chunk doesn't contain relevant information, say "No relevant information in this chunk."

CHUNK CONTENT:
{content}

ANALYSIS:"""

        prompts = [
            map_prompt_template.format(
                index=c.index + 1,
                total=c.total,
                query=query,
                content=c.content,
            )
            for c in chunks
        ]
        
        # Check cache
        results = []
        uncached_indices = []
        uncached_prompts = []
        
        for i, (prompt, chunk) in enumerate(zip(prompts, chunks)):
            cache_key = self._cache_key(chunk.content, query)
            if self.cache_enabled and cache_key in self._cache:
                results.append((i, self._cache[cache_key]))
                self._stats["cache_hits"] += 1
            else:
                uncached_indices.append(i)
                uncached_prompts.append(prompt)
                results.append((i, None))
        
        # Process uncached
        if uncached_prompts:
            self._log(f"Processing {len(uncached_prompts)} chunks ({self._stats['cache_hits']} cached)")
            batch_results = self.llm_batch(uncached_prompts, system_prompt)
            
            for idx, result in zip(uncached_indices, batch_results):
                results[idx] = (idx, result)
                # Cache result
                if self.cache_enabled:
                    cache_key = self._cache_key(chunks[idx].content, query)
                    self._cache[cache_key] = result
        
        # Sort by index
        results.sort(key=lambda x: x[0])
        chunk_results = [r[1] for r in results]
        self._variables["chunk_results"] = chunk_results
        
        # Filter relevant findings
        findings = []
        for i, result in enumerate(chunk_results):
            if result and "No relevant information" not in result:
                findings.append(f"[Chunk {i+1}]\n{result}")
        
        if not findings:
            return "No relevant information found in the context."
        
        # Reduce phase: synthesize findings
        self._log(f"Reducing {len(findings)} findings...")
        
        reduce_prompt = f"""Based on analysis of {len(chunks)} chunks, provide a comprehensive answer.

ORIGINAL TASK: {query}

FINDINGS FROM CHUNKS:
{chr(10).join(findings)}

Synthesize all findings into a clear, comprehensive response.
Cite specific chunks when referencing information."""

        resp = self.client.query(reduce_prompt, system_prompt)
        
        self._stats["total_tokens_in"] += resp.tokens_in
        self._stats["total_tokens_out"] += resp.tokens_out
        
        if not resp.success:
            # Fallback to concatenated findings
            return f"Aggregation failed. Raw findings:\n\n{chr(10).join(findings)}"
        
        self._variables["final_result"] = resp.content
        return resp.content
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return self._stats.copy()
    
    def get_variable(self, name: str) -> Any:
        """Get stored variable (REPL-style access)."""
        return self._variables.get(name)
    
    def clear_cache(self):
        """Clear the result cache."""
        self._cache.clear()


# =============================================================================
# Session Persistence
# =============================================================================

class Session:
    """Simple session persistence for context memory."""
    
    def __init__(self, session_id: str, storage_dir: Optional[Path] = None):
        self.session_id = session_id
        self.storage_dir = storage_dir or Path.home() / ".rlm_sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.messages: list[dict] = []
        self.memories: dict[str, str] = {}
        self._load()
    
    @property
    def path(self) -> Path:
        return self.storage_dir / f"{self.session_id}.json"
    
    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.messages = data.get("messages", [])
                self.memories = data.get("memories", {})
            except Exception:
                pass
    
    def save(self):
        data = {
            "session_id": self.session_id,
            "messages": self.messages,
            "memories": self.memories,
            "updated_at": time.time(),
        }
        self.path.write_text(json.dumps(data, indent=2))
    
    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        self.save()
    
    def add_memory(self, key: str, content: str):
        self.memories[key] = content
        self.save()
    
    def get_memory(self, key: str) -> Optional[str]:
        return self.memories.get(key)
    
    def search_memories(self, query: str, limit: int = 5) -> list[tuple[str, str]]:
        """Simple keyword search in memories."""
        query_words = set(query.lower().split())
        scored = []
        
        for key, content in self.memories.items():
            content_words = set(content.lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                scored.append((overlap, key, content))
        
        scored.sort(reverse=True)
        return [(k, c) for _, k, c in scored[:limit]]


# =============================================================================
# Exa Research Integration (via MCP or API)
# =============================================================================

def exa_search(query: str, num_results: int = 5, api_key: Optional[str] = None) -> str:
    """
    Search web via Exa API.
    
    For MCP integration, call the mcp_exa_web_search_exa tool instead.
    This function is for direct API usage.
    """
    try:
        from exa_py import Exa
        
        key = api_key or os.getenv("EXA_API_KEY")
        if not key:
            return "[Exa API key not set]"
        
        exa = Exa(api_key=key)
        resp = exa.search_and_contents(
            query=query,
            num_results=num_results,
            text={"max_characters": 2000},
        )
        
        results = []
        for r in resp.results:
            results.append(f"**{r.title}**\n{r.url}\n{r.text[:500]}...")
        
        return "\n\n---\n\n".join(results)
    
    except ImportError:
        return "[exa-py not installed: pip install exa-py]"
    except Exception as e:
        return f"[Exa error: {e}]"


# =============================================================================
# Convenience Functions
# =============================================================================

def process_codebase(
    directory: str | Path,
    query: str,
    extensions: list[str] = None,
    provider: str = "anthropic",
    **kwargs
) -> str:
    """
    Convenience function to process a codebase directory.
    
    Args:
        directory: Path to codebase
        query: Analysis query
        extensions: File extensions to include
        provider: LLM provider (anthropic or openai)
        **kwargs: Additional arguments for client
    """
    directory = Path(directory).expanduser()
    extensions = extensions or ['.py', '.js', '.ts', '.go', '.rs', '.java']
    
    # Load files
    files = []
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix in extensions:
            # Skip common non-source dirs
            if any(p in path.parts for p in ['node_modules', '__pycache__', '.git', 'venv']):
                continue
            try:
                content = path.read_text()
                rel_path = path.relative_to(directory)
                files.append(f"=== {rel_path} ===\n{content}")
            except Exception:
                continue
    
    if not files:
        raise ValueError(f"No source files found in {directory}")
    
    context = "\n\n".join(files)
    print(f"Loaded {len(files)} files ({len(context):,} chars)")
    
    # Process
    client = create_client(provider, **kwargs)
    engine = RLMContextEngine(client)
    
    return engine.process(context, query, chunking="code")


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Simple CLI for RLM context engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RLM Context Extension")
    parser.add_argument("query", nargs="?", help="Query to process")
    parser.add_argument("--context", "-c", help="Context file or directory")
    parser.add_argument("--provider", "-p", default="anthropic", choices=["anthropic", "openai"])
    parser.add_argument("--research", "-r", action="store_true", help="Enable Exa research")
    parser.add_argument("--research-query", help="Custom research query")
    parser.add_argument("--session", "-s", help="Session ID for persistence")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--quiet", "-q", action="store_true")
    
    args = parser.parse_args()
    
    # Create client and engine
    try:
        client = create_client(args.provider)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    engine = RLMContextEngine(client, verbose=not args.quiet)
    
    # Load context
    context = ""
    if args.context:
        path = Path(args.context).expanduser()
        if path.is_file():
            context = path.read_text()
        elif path.is_dir():
            # Load directory
            files = []
            for p in path.rglob("*"):
                if p.is_file() and p.suffix in ['.py', '.js', '.ts', '.md', '.txt']:
                    if not any(x in p.parts for x in ['node_modules', '__pycache__', '.git']):
                        try:
                            files.append(f"=== {p.relative_to(path)} ===\n{p.read_text()}")
                        except Exception:
                            pass
            context = "\n\n".join(files)
            if not args.quiet:
                print(f"Loaded {len(files)} files")
    
    # Session
    session = None
    if args.session:
        session = Session(args.session)
    
    # Interactive mode
    if args.interactive:
        print("RLM Interactive Mode (type 'exit' to quit)")
        while True:
            try:
                query = input("rlm> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if query.lower() == "exit":
                break
            
            if query.startswith("/remember "):
                parts = query[10:].split(" ", 1)
                if len(parts) == 2 and session:
                    session.add_memory(parts[0], parts[1])
                    print(f"Stored: {parts[0]}")
                continue
            
            if query.startswith("/recall "):
                if session:
                    results = session.search_memories(query[8:])
                    for k, v in results:
                        print(f"[{k}] {v[:100]}...")
                continue
            
            try:
                result = engine.process(context, query)
                print(f"\n{result}\n")
                if session:
                    session.add_message("user", query)
                    session.add_message("assistant", result)
            except Exception as e:
                print(f"Error: {e}")
        
        return 0
    
    # Single query mode
    if not args.query:
        parser.print_help()
        return 1
    
    # Research
    if args.research:
        research_query = args.research_query or args.query
        if not args.quiet:
            print(f"Researching: {research_query}")
        research = exa_search(research_query)
        context = f"{context}\n\n--- RESEARCH ---\n{research}" if context else research
    
    try:
        result = engine.process(context, args.query)
        print(result)
        
        if session:
            session.add_message("user", args.query)
            session.add_message("assistant", result)
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())


