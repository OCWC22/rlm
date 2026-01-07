# How RLM Context Extension Works

A complete guide to processing files larger than LLM context windows using the **Recursive Language Model (RLM)** approach.

---

## References

- **Paper**: [Recursive Language Models](https://arxiv.org/abs/2512.24601v1) by Alex L. Zhang, Tim Kraska, Omar Khattab (MIT CSAIL)
- **Original Repo**: [github.com/alexzhang13/rlm](https://github.com/alexzhang13/rlm)
- **Prime Intellect Implementation**: [RLMEnv](https://github.com/PrimeIntellect-ai/verifiers/blob/sebastian/experiment/rlm/verifiers/envs/rlm_env.py)

---

## The Problem

When you try to read a large file in Claude Code:

```
⏺ Read(~/data/conversations.jsonl)
  ⎿  Error: File content (13.4MB) exceeds maximum allowed size (256KB)
```

**Why this happens:**
- LLMs have finite context windows (~200K tokens for Claude)
- 13.4MB ≈ 3-4 million tokens → WAY too big
- Can't just "load it all" into the prompt

---

## The Solution: Recursive Language Models

The RLM paper proposes treating the LLM as an **orchestrator** that can:
1. **Examine** parts of large data
2. **Decompose** into manageable chunks  
3. **Recursively call** sub-LLMs on each chunk
4. **Aggregate** results into a final answer

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RLM ARCHITECTURE                              │
│                                                                      │
│  "The core idea is that an LLM can programmatically examine,        │
│   decompose, and recursively call itself over snippets of           │
│   the prompt." - RLM Paper                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Breakdown

### Step 1: Stream & Chunk

**Never load the entire file into memory.** Read it in chunks.

```
YOUR 13.4MB JSONL FILE
════════════════════════════════════════════════════════════════════

Line 1:    {"messages": [...], "timestamp": "2025-11-15T11:25:33"}
Line 2:    {"messages": [...], "timestamp": "2025-11-15T11:30:00"}
Line 3:    {"messages": [...], "timestamp": "2025-11-15T11:35:00"}
   ⋮
Line 50:   {"messages": [...], "timestamp": "2025-11-15T14:00:00"}
─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
Line 51:   {"messages": [...], "timestamp": "2025-11-15T14:05:00"}
Line 52:   {"messages": [...], "timestamp": "2025-11-15T14:10:00"}
   ⋮
Line 100:  {"messages": [...], "timestamp": "2025-11-15T17:00:00"}
─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
   ⋮                              ⋮
Line 9950: {"messages": [...], "timestamp": "2025-11-16T20:00:00"}
   ⋮
Line 10000: {"messages": [...], "timestamp": "2025-11-16T20:45:00"}

════════════════════════════════════════════════════════════════════
```

**Code:**

```python
def read_jsonl_chunks(filepath, lines_per_chunk=50):
    """
    Generator that yields chunks of lines.
    Never loads entire file into memory!
    """
    chunk = []
    chunk_idx = 0
    
    with open(filepath, 'r') as f:
        for line in f:                    # Stream line by line
            obj = json.loads(line)
            chunk.append(obj)
            
            if len(chunk) >= lines_per_chunk:
                yield (chunk_idx, chunk)  # Yield chunk
                chunk = []                # Reset
                chunk_idx += 1
        
        if chunk:                         # Don't forget remainder
            yield (chunk_idx, chunk)
```

**Result:**

```
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│    CHUNK 0     │  │    CHUNK 1     │  │    CHUNK 2     │   ...
│  Lines 1-50    │  │  Lines 51-100  │  │  Lines 101-150 │
│    ~100KB      │  │     ~100KB     │  │     ~100KB     │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

### Step 2: Map Phase (Parallel Sub-LLM Calls)

Each chunk is sent to an LLM independently. This is the **`llm_batch()`** function from the RLM paper.

```
                         ┌─────────────────────────────────────┐
                         │           YOUR QUERY                │
                         │  "Summarize the conversations"      │
                         └──────────────────┬──────────────────┘
                                            │
            ┌───────────────────────────────┼───────────────────────────────┐
            │                               │                               │
            ▼                               ▼                               ▼
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
│      CHUNK 0          │   │      CHUNK 1          │   │      CHUNK 2          │
│   Lines 1-50          │   │   Lines 51-100        │   │   Lines 101-150       │
└───────────┬───────────┘   └───────────┬───────────┘   └───────────┬───────────┘
            │                           │                           │
            ▼                           ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
│     ┌─────────┐       │   │     ┌─────────┐       │   │     ┌─────────┐       │
│     │ CLAUDE  │       │   │     │ CLAUDE  │       │   │     │ CLAUDE  │       │
│     │   API   │       │   │     │   API   │       │   │     │   API   │       │
│     └─────────┘       │   │     └─────────┘       │   │     └─────────┘       │
│                       │   │                       │   │                       │
│  "Analyze chunk 0     │   │  "Analyze chunk 1     │   │  "Analyze chunk 2     │
│   for: Summarize      │   │   for: Summarize      │   │   for: Summarize      │
│   the conversations"  │   │   the conversations"  │   │   the conversations"  │
└───────────┬───────────┘   └───────────┬───────────┘   └───────────┬───────────┘
            │                           │                           │
            │      PARALLEL             │       EXECUTION           │
            │      (ThreadPool)         │                           │
            ▼                           ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
│     RESULT 0          │   │     RESULT 1          │   │     RESULT 2          │
│                       │   │                       │   │                       │
│  "This chunk has      │   │  "These conversations │   │  "Found discussions   │
│   disk cleanup        │   │   are about code      │   │   about error         │
│   discussions..."     │   │   refactoring..."     │   │   debugging..."       │
└───────────────────────┘   └───────────────────────┘   └───────────────────────┘
```

**Code:**

```python
def llm_batch(prompts: list[str]) -> list[str]:
    """
    Process multiple prompts in parallel.
    This is the key function from the RLM paper!
    """
    results = []
    
    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all jobs
        futures = {
            executor.submit(call_claude, prompt): i 
            for i, prompt in enumerate(prompts)
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            idx = futures[future]
            result = future.result()
            results.append((idx, result))
    
    # Sort by original order
    results.sort(key=lambda x: x[0])
    return [r[1] for r in results]


# Usage in our processor:
prompts = []
for chunk_idx, chunk_data in chunks:
    prompt = f"""
    Analyze chunk {chunk_idx} for: {user_query}
    
    DATA:
    {json.dumps(chunk_data)}
    
    ANALYSIS:
    """
    prompts.append(prompt)

# Process all chunks in parallel!
chunk_results = llm_batch(prompts)
```

---

### Step 3: Reduce Phase (Aggregate Results)

Combine all chunk results into a final coherent answer.

```
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│     RESULT 0      │   │     RESULT 1      │   │     RESULT 2      │
│  "Disk cleanup    │   │  "Code refactor   │   │  "Error debug     │
│   discussions"    │   │   requests"       │   │   sessions"       │
└─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │                             │
                    │       AGGREGATION LLM       │
                    │                             │
                    │  "Based on analysis of      │
                    │   multiple chunks:          │
                    │                             │
                    │   [Chunk 0]: disk cleanup   │
                    │   [Chunk 1]: refactoring    │
                    │   [Chunk 2]: debugging      │
                    │                             │
                    │   Synthesize into final     │
                    │   comprehensive answer"     │
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │                             │
                    │       FINAL ANSWER          │
                    │                             │
                    │  "The conversations cover   │
                    │   three main topics:        │
                    │                             │
                    │   1. System maintenance     │
                    │      (disk cleanup, cache   │
                    │      clearing)              │
                    │                             │
                    │   2. Code improvements      │
                    │      (refactoring, type     │
                    │      safety)                │
                    │                             │
                    │   3. Troubleshooting        │
                    │      (error fixing,         │
                    │      debugging)"            │
                    │                             │
                    └─────────────────────────────┘
```

**Code:**

```python
def aggregate_results(chunk_results: list[str], query: str) -> str:
    """
    Combine all chunk analyses into final answer.
    """
    # Filter out empty/irrelevant results
    findings = []
    for i, result in enumerate(chunk_results):
        if "No relevant" not in result:
            findings.append(f"[Chunk {i}]\n{result}")
    
    # Ask LLM to synthesize
    prompt = f"""
    Based on analysis of {len(findings)} chunks, provide a comprehensive answer.
    
    ORIGINAL QUERY: {query}
    
    FINDINGS:
    {chr(10).join(findings)}
    
    SYNTHESIS:
    """
    
    return call_claude(prompt)
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE RLM FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

     USER                           RLM PROCESSOR                    CLAUDE API
       │                                  │                              │
       │  "Summarize conversations"       │                              │
       │  + path to 13.4MB file           │                              │
       │ ────────────────────────────────>│                              │
       │                                  │                              │
       │                          ┌───────┴───────┐                      │
       │                          │ STREAM FILE   │                      │
       │                          │ (line by line)│                      │
       │                          └───────┬───────┘                      │
       │                                  │                              │
       │                          ┌───────┴───────┐                      │
       │                          │ CREATE CHUNKS │                      │
       │                          │ (50 lines ea) │                      │
       │                          └───────┬───────┘                      │
       │                                  │                              │
       │                                  │  Chunk 0                     │
       │                                  │ ────────────────────────────>│
       │                                  │                              │
       │                                  │  Chunk 1 (parallel)          │
       │                                  │ ────────────────────────────>│
       │                                  │                              │
       │                                  │  Chunk 2 (parallel)          │
       │                                  │ ────────────────────────────>│
       │                                  │                              │
       │                                  │<──────────────────────────── │
       │                                  │        Results 0,1,2         │
       │                                  │                              │
       │                          ┌───────┴───────┐                      │
       │                          │  AGGREGATE    │                      │
       │                          │   RESULTS     │                      │
       │                          └───────┬───────┘                      │
       │                                  │                              │
       │                                  │  "Synthesize findings"       │
       │                                  │ ────────────────────────────>│
       │                                  │                              │
       │                                  │<──────────────────────────── │
       │                                  │        Final answer          │
       │                                  │                              │
       │<─────────────────────────────────│                              │
       │  "The conversations cover..."    │                              │
       │                                  │                              │
```

---

## Why This Works

| Traditional Approach | RLM Approach |
|---------------------|--------------|
| Load 13.4MB into prompt | Stream 50 lines at a time |
| ❌ Exceeds context limit | ✅ Each chunk fits easily |
| Single LLM call | Multiple parallel calls |
| All or nothing | Graceful degradation |
| Memory explosion | Constant memory usage |

---

## Key Concepts from the Paper

### 1. REPL Environment as Extended Memory

> "The REPL environment acts as extended working memory. Variables persist across iterations."

In our implementation, this is the chunk results that persist between calls.

### 2. Sub-LLM Calls via `llm_batch()`

> "Within the REPL, the Root LM can call Sub-LMs to process chunks of data."

This is exactly what we do - each chunk gets its own LLM call.

### 3. Divide and Conquer

> "Instead of trying to fit everything into one context window, RLM writes code to chunk the data intelligently."

We chunk based on:
- JSONL: lines (50 per chunk)
- Code: function/class boundaries
- Text: paragraphs or fixed size

---

## Usage Examples

### Basic Usage

```bash
# Set API key
export ANTHROPIC_API_KEY=your_key_here

# Process large JSONL file
python large_file_processor.py \
    ~/data/conversations.jsonl \
    "What are the main topics discussed?"
```

### Sampling for Huge Files

```bash
# Sample every 10th line (10x faster, good for exploration)
python large_file_processor.py \
    ~/data/huge_file.jsonl \
    "Find error patterns" \
    --sample 10
```

### Limit Chunks

```bash
# Only process first 5 chunks (faster iteration)
python large_file_processor.py \
    ~/data/conversations.jsonl \
    "Summarize" \
    --max-chunks 5
```

### Python API

```python
from large_file_processor import LargeFileProcessor

processor = LargeFileProcessor(provider="anthropic")

result = processor.process_jsonl(
    filepath="~/data/conversations.jsonl",
    query="Extract all error messages and their solutions",
    lines_per_chunk=50,
    sample_every=5,  # Sample for speed
)

print(result)
print(processor.get_stats())
```

---

## Performance Characteristics

| File Size | Chunks (50 lines) | API Calls | Est. Time | Est. Cost |
|-----------|-------------------|-----------|-----------|-----------|
| 1MB       | ~20               | 21        | ~30s      | ~$0.10    |
| 10MB      | ~200              | 201       | ~5min     | ~$1.00    |
| 100MB     | ~2000             | 2001      | ~50min    | ~$10.00   |

**Tips:**
- Use `--sample 10` for quick exploration (10x faster)
- Use `--max-chunks 20` to limit cost during development
- Use `--workers 5` for faster parallel processing (watch rate limits)

---

## References

1. **RLM Paper**: Zhang, A.L., Kraska, T., & Khattab, O. (2025). *Recursive Language Models*. arXiv:2512.24601. https://arxiv.org/abs/2512.24601v1

2. **Original Implementation**: https://github.com/alexzhang13/rlm

3. **Prime Intellect RLMEnv**: https://github.com/PrimeIntellect-ai/verifiers/blob/sebastian/experiment/rlm/verifiers/envs/rlm_env.py

4. **Blog Post**: https://alexzhang13.github.io/blog/2025/rlm/

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   RLM = "LLMs that recursively call themselves or other LLMs               │
│          before providing a final answer"                                   │
│                                                                             │
│   Key Insight: Treat large data as an ENVIRONMENT to explore,              │
│                not a PROMPT to consume all at once.                         │
│                                                                             │
│   Implementation:                                                           │
│     1. CHUNK the data (stream, don't load)                                  │
│     2. MAP each chunk through sub-LLM calls (parallel)                      │
│     3. REDUCE results into final answer                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

