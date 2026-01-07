# RLM Context Extension for CLI Coding Agents

A self-contained implementation of **Recursive Language Model (RLM)** context extension for use with Claude Code, Codex CLI, or any CLI-based coding agent.

## Overview

Based on:
- **RLM Paper**: [Recursive Language Models](https://arxiv.org/abs/2512.24601v1)
- **Prime Intellect RLMEnv**: [verifiers/rlm_env.py](https://github.com/PrimeIntellect-ai/verifiers/blob/sebastian/experiment/rlm/verifiers/envs/rlm_env.py)

The RLM approach allows LLMs to process **arbitrarily large contexts** by:

1. **Chunking** - Breaking large inputs into manageable pieces
2. **Mapping** - Processing each chunk with parallel sub-LLM calls (`llm_batch()`)
3. **Reducing** - Aggregating findings into a final answer
4. **Recursion** - Sub-LLMs can themselves make recursive calls

```
┌─────────────────────────────────────────────────────┐
│                 Large Context                       │
│  (codebase, documents, research, etc.)              │
└────────────────────┬────────────────────────────────┘
                     │ chunk
                     ▼
        ┌────────┬────────┬────────┐
        │ Chunk1 │ Chunk2 │ Chunk3 │  ...
        └────┬───┴────┬───┴────┬───┘
             │        │        │
             ▼        ▼        ▼
        ┌────────────────────────────┐
        │     llm_batch() - Parallel │
        │     Sub-LLM Processing     │
        └────────────────────────────┘
             │        │        │
             ▼        ▼        ▼
        ┌────────┬────────┬────────┐
        │Result 1│Result 2│Result 3│  ...
        └────┬───┴────┬───┴────┬───┘
             │        │        │
             └────────┴────────┘
                     │ reduce
                     ▼
        ┌────────────────────────────┐
        │      Final Answer          │
        └────────────────────────────┘
```

## Files

```
examples/claude-code-assistant/
├── rlm_context.py     # Main implementation (self-contained)
├── example_usage.py   # Tests and demos
└── README.md          # This file
```

## Quick Start

### 1. Install Dependencies

```bash
# Anthropic (recommended)
pip install anthropic

# Or OpenAI
pip install openai

# Optional: Exa research
pip install exa-py
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY=your_key_here
# or
export OPENAI_API_KEY=your_key_here
```

### 3. Run Tests

```bash
cd examples/claude-code-assistant
python example_usage.py
```

## Processing Large Files (NEW)

For files too large for Claude Code's 256KB limit (like your 13.4MB JSONL):

```bash
# Analyze a large JSONL file
python large_file_processor.py ~/path/to/large_file.jsonl "Summarize the content"

# For huge files, sample every Nth line
python large_file_processor.py ~/path/to/large_file.jsonl "Find patterns" --sample 10

# Limit chunks for faster results
python large_file_processor.py ~/path/to/large_file.jsonl "Extract errors" --max-chunks 10
```

### 4. Use the CLI

```bash
# Analyze a file
python rlm_context.py "Explain this code" --context ./rlm_context.py

# Analyze a directory
python rlm_context.py "Find potential bugs" --context ../../../rlm/

# Interactive mode with session persistence
python rlm_context.py --interactive --session my-analysis
```

## Usage

### Python API

```python
from rlm_context import RLMContextEngine, create_client, Session

# Create client and engine
client = create_client("anthropic")  # or "openai"
engine = RLMContextEngine(client, verbose=True)

# Process large context
with open("large_file.py") as f:
    code = f.read()

result = engine.process(
    context=code,
    query="Find all security vulnerabilities in this code",
    chunking="code",  # auto, code, markdown, fixed
)
print(result)

# Check stats
print(engine.get_stats())
```

### Parallel Sub-LLM Calls

The key RLM feature - call multiple sub-LLMs in parallel:

```python
# Engine exposes llm_batch for parallel queries
prompts = [
    f"Analyze chunk {i} for issues" 
    for i in range(10)
]
results = engine.llm_batch(prompts)
```

### Session Persistence

```python
from rlm_context import Session

session = Session("my-project")

# Store memories
session.add_memory("architecture", "Microservices with event sourcing")
session.add_memory("tech_stack", "Python, FastAPI, PostgreSQL")

# Search memories
results = session.search_memories("what framework")
# [("tech_stack", "Python, FastAPI, PostgreSQL")]

# Track conversation
session.add_message("user", "What is the main entry point?")
session.add_message("assistant", "The main entry point is app.py...")
```

### Research with Exa

```python
from rlm_context import exa_search

# Direct Exa search (requires EXA_API_KEY)
research = exa_search("FastAPI security best practices")

# Or use CLI with --research flag
```

### Codebase Analysis

```python
from rlm_context import process_codebase

result = process_codebase(
    directory="./my_project",
    query="Find all TODO comments and suggest improvements",
    extensions=['.py', '.js'],
    provider="anthropic",
)
```

## CLI Reference

```
usage: rlm_context.py [-h] [--context CONTEXT] [--provider {anthropic,openai}]
                      [--research] [--research-query RESEARCH_QUERY]
                      [--session SESSION] [--interactive] [--quiet]
                      [query]

RLM Context Extension

positional arguments:
  query                 Query to process

options:
  -h, --help            show this help message and exit
  --context, -c         Context file or directory
  --provider, -p        LLM provider (anthropic or openai)
  --research, -r        Enable Exa research
  --research-query      Custom research query
  --session, -s         Session ID for persistence
  --interactive, -i     Interactive mode
  --quiet, -q           Suppress progress output
```

### Interactive Commands

```
rlm> What is this code about?
[Response...]

rlm> /remember architecture Uses microservices
Stored: architecture

rlm> /recall how is it structured
[architecture] Uses microservices...

rlm> exit
```

## Key Features

### Chunking Strategies

| Strategy | Best For |
|----------|----------|
| `auto` | Auto-detect based on content |
| `code` | Source code (respects function/class boundaries) |
| `markdown` | Documentation (splits by headers) |
| `fixed` | Generic content (fixed size with overlap) |

### Caching

Results are cached by content+query hash to avoid redundant API calls:

```python
engine = RLMContextEngine(client, cache_enabled=True)
engine.process(context, query)  # First call: hits API
engine.process(context, query)  # Second call: uses cache
engine.clear_cache()  # Clear if needed
```

### Statistics

```python
stats = engine.get_stats()
# {
#     "total_chunks": 5,
#     "total_tokens_in": 15000,
#     "total_tokens_out": 3000,
#     "total_time": 12.5,
#     "cache_hits": 2,
# }
```

## Integration with Coding Agents

### Claude Code

```bash
# Use with Claude Code by piping context through RLM first
python rlm_context.py "Summarize architecture" -c ./src | claude-code
```

### Codex CLI

```bash
# Same pattern works with Codex
python rlm_context.py "Generate tests for" -c ./src | codex
```

### Cursor / Continue

Add as a prompt preprocessor - use RLM to analyze large codebases before passing summaries to the agent.

## Architecture Comparison

### Prime Intellect RLMEnv

The [Prime Intellect implementation](https://github.com/PrimeIntellect-ai/verifiers/blob/sebastian/experiment/rlm/verifiers/envs/rlm_env.py) is designed for RL training:

- Async with sandbox isolation
- HTTP proxy for sub-LLM interception
- Full trajectory tracking for training
- Complex tool calling integration

### This Implementation

Simplified for practical coding agent use:

- Synchronous Python
- Direct API calls with parallel threading
- Session persistence for multi-turn workflows
- Easy CLI and Python API
- No sandbox complexity

## Examples

See `example_usage.py` for:

1. **Chunking tests** - Verify chunking strategies work
2. **Session tests** - Test persistence and memory
3. **Mock engine** - Test without API
4. **Real API** - Test with Anthropic/OpenAI
5. **Codebase processing** - Analyze directory

## License

MIT
