# Externalized Reasoning: A Complete Guide to RLMs, Chain-of-Thought, MCP, and Context Engineering

> **The Unified Theory of Extended AI Reasoning Through External State**
>
> This document synthesizes cutting-edge research and production patterns for dramatically improving LLM reasoning and context handling by externalizing state.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Part I: Core Concepts Deep Dive](#part-i-core-concepts-deep-dive)
   - [Chain-of-Thought (CoT) Reasoning](#21-chain-of-thought-cot-reasoning)
   - [Recursive Language Models (RLMs)](#22-recursive-language-models-rlms)
   - [Model Context Protocol (MCP)](#23-model-context-protocol-mcp)
   - [Everything is Context: File System Abstraction](#24-everything-is-context-file-system-abstraction)
   - [Dynamic Context Discovery (Cursor)](#25-dynamic-context-discovery-cursor)
   - [Clear Thought 1.5](#26-clear-thought-15)
3. [Part II: Omar Khattab's Key Insights](#part-ii-omar-khattabs-key-insights)
4. [Part III: What Works, What Doesn't, and Why](#part-iii-what-works-what-doesnt-and-why)
5. [Part IV: The Unified Synthesis](#part-iv-the-unified-synthesis)
6. [Part V: Production Architecture](#part-v-production-architecture)
7. [High-Signal Summary](#high-signal-summary)
8. [References](#references)

---

## 1. Executive Summary

### The Core Problem

Large Language Models have a fundamental limitation: **they process prompts as raw token sequences within fixed context windows**. This creates three critical issues:

1. **Context limits**: Can't process data beyond ~200K tokens
2. **Attention dilution**: Quality degrades as context grows
3. **No persistent state**: Everything must fit in one forward pass

### The Solution: Externalized State

All modern approaches converge on one insight:

> **Store prompts, context, history, and intermediate results as symbolic objects external to the LLM, accessible through tools and file operations.**

This transforms LLMs from stateless token processors into stateful reasoning systems with:
- Unlimited effective context
- Persistent memory across calls
- Structured, composable operations
- Traceable, auditable reasoning

### The Key Equation

```
Traditional LLM:  output = LLM(tokens)
                  ↓ Limited, lossy, stateless

Externalized:     output = LLM(read(state), tools, recursive_call)
                  ↓ Unlimited, structured, persistent
```

---

# Part I: Core Concepts Deep Dive

## 2.1 Chain-of-Thought (CoT) Reasoning

### What It Is

Chain-of-Thought is a prompting technique where the LLM explicitly shows its reasoning steps before reaching a conclusion.

### How It Works

```
Without CoT:
Q: "What is 17 × 24?"
A: "408"

With CoT:
Q: "What is 17 × 24? Think step by step."
A: "Let me work through this:
    17 × 24 = 17 × (20 + 4)
    = (17 × 20) + (17 × 4)
    = 340 + 68
    = 408"
```

### Why It Matters

| Aspect | Without CoT | With CoT |
|--------|-------------|----------|
| Accuracy | Lower | Higher (especially on multi-step) |
| Transparency | None | Full reasoning visible |
| Debuggability | Hard | Easy to spot errors |
| Token cost | Lower | Higher |

### Variants

| Variant | Description |
|---------|-------------|
| **Zero-shot CoT** | Add "Let's think step by step" |
| **Few-shot CoT** | Provide examples with reasoning |
| **Self-consistency** | Sample multiple chains, vote |
| **Tree-of-Thought** | Branch and explore multiple paths |
| **Graph-of-Thought** | Non-linear reasoning connections |

### The Limitation

CoT reasoning still happens **within the context window**. For truly complex problems or large data:
- The reasoning chain gets truncated
- Earlier steps get "forgotten" (attention dilution)
- No persistent state between queries

**This is where RLMs come in.**

---

## 2.2 Recursive Language Models (RLMs)

### What It Is

**Recursive Language Models (RLMs)** are an inference strategy where LLMs can:
1. Store their prompt/context as **symbolic objects** (not tokens)
2. **Recursively call themselves** or other LLMs
3. Operate within a **persistent environment** (like a REPL)

### The Key Insight (From Omar Khattab)

> "If you store the input prompt as a symbolic object external to the LLM, create a tool for recursive calls, and allow for a persistent coding environment, you are implementing a complete RLM."

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RLM ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐                                          │
│   │ USER PROMPT  │ ← Stored as FILE, not tokens             │
│   │ (External)   │                                          │
│   └──────┬───────┘                                          │
│          │                                                   │
│   ┌──────▼───────┐                                          │
│   │   ROOT LLM   │ ← Orchestrates, decides strategy         │
│   │              │                                          │
│   └──────┬───────┘                                          │
│          │                                                   │
│   ┌──────▼───────────────────────────────────────────┐      │
│   │              REPL ENVIRONMENT                     │      │
│   │                                                   │      │
│   │  globals = {                                      │      │
│   │    'context': <loaded from file>,                 │      │
│   │    'llm_query': <recursive LLM call>,             │      │
│   │    'FINAL_VAR': <return variable as answer>,      │      │
│   │  }                                                │      │
│   │                                                   │      │
│   │  locals = {                                       │      │
│   │    # Persistent across iterations                 │      │
│   │    'chunks': [...],                               │      │
│   │    'results': [...],                              │      │
│   │    'intermediate_state': {...},                   │      │
│   │  }                                                │      │
│   │                                                   │      │
│   └──────┬───────────────────────────────────────────┘      │
│          │                                                   │
│          ├─────────────┬─────────────┬─────────────┐        │
│          ▼             ▼             ▼             ▼        │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│   │ SUB-LLM  │  │ SUB-LLM  │  │ SUB-LLM  │  │ SUB-LLM  │   │
│   │ Chunk 1  │  │ Chunk 2  │  │ Chunk 3  │  │ Chunk N  │   │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### The Algorithm

```python
def rlm_completion(context: str, query: str) -> str:
    """
    RLM Processing Loop
    
    1. SETUP: Create REPL environment with:
       - context loaded from file (not as tokens)
       - llm_query() tool for recursive calls
       - FINAL_VAR() to return answers
    
    2. MAIN LOOP (max_iterations):
       a. Query Root LLM with conversation history
       b. Parse response for:
          - ```repl``` code blocks → Execute in REPL
          - FINAL(answer) → Return answer
       c. Execute code, capture output
       d. Add results to conversation history
       e. Check for final answer
    
    3. FALLBACK: Force final answer if max iterations reached
    """
    
    # Initialize REPL with external context
    repl = REPLEnv(
        context_json=load_context(context),
        recursive_model="gpt-4"
    )
    
    messages = build_system_prompt()
    
    for iteration in range(max_iterations):
        response = llm.completion(messages + [next_action_prompt(query, iteration)])
        
        code_blocks = find_code_blocks(response)
        if code_blocks:
            # Execute LLM-generated code in REPL
            for code in code_blocks:
                result = repl.code_execution(code)
                messages.append({"role": "tool", "content": result.stdout})
        
        if final_answer := check_for_final_answer(response, repl):
            return final_answer
    
    return force_final_answer(messages)
```

### Why It Works

| Traditional LLM | RLM |
|-----------------|-----|
| Context = tokens in attention | Context = file on disk |
| Single forward pass | Multiple iterations |
| No memory between calls | Persistent variables |
| Can't decompose problems | Recursively processes chunks |
| Fixed algorithms | LLM decides strategy dynamically |

### Example: Needle in Haystack

```python
# Traditional LLM: FAILS (context too large)
llm.completion("Find the magic number in this 1M line document: {document}")
# → Context exceeds limit, or model loses the needle

# RLM: SUCCEEDS
rlm.completion(
    context=one_million_lines,
    query="Find the magic number"
)
# LLM generates:
```

```python
# RLM's self-generated strategy:
chunks = [context[i:i+500000] for i in range(0, len(context), 500000)]
results = []
for i, chunk in enumerate(chunks):
    result = llm_query(f"Search for 'magic number' in this text: {chunk[:100000]}")
    if "magic number" in result.lower():
        results.append((i, result))
        
if results:
    FINAL(f"Found magic number in chunk {results[0][0]}: {results[0][1]}")
```

---

## 2.3 Model Context Protocol (MCP)

### What It Is

**MCP (Model Context Protocol)** is an open standard by Anthropic for connecting LLMs to external data sources and tools in a standardized way.

### Core Components

```
┌──────────────────────────────────────────────────────────────┐
│                     MCP ARCHITECTURE                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐        MCP Protocol         ┌─────────────┐ │
│  │  MCP Host   │ ◄────────────────────────► │  MCP Server │ │
│  │  (Claude,   │                             │  (Your App) │ │
│  │   Cursor)   │                             │             │ │
│  └─────────────┘                             └──────┬──────┘ │
│                                                      │        │
│                                              ┌───────▼──────┐ │
│                                              │   Resources  │ │
│                                              │   - files    │ │
│                                              │   - DBs      │ │
│                                              │   - APIs     │ │
│                                              └──────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Key Primitives

| Primitive | Purpose | Example |
|-----------|---------|---------|
| **Resources** | Read-only data sources | Files, databases, APIs |
| **Tools** | Executable actions | `search_codebase`, `run_query` |
| **Prompts** | Templated interactions | Pre-built workflows |
| **Sampling** | LLM requests from server | Server asks host LLM for help |

### Why MCP Matters for Externalized State

MCP provides the **transport layer** for externalized reasoning:

```typescript
// MCP Server exposes context as resources
server.resources = [
  {
    uri: "context://prompt",
    name: "Current Prompt",
    mimeType: "text/plain"
  },
  {
    uri: "context://history",
    name: "Conversation History",
    mimeType: "application/json"
  }
];

// MCP Server exposes recursive call as tool
server.tools = [
  {
    name: "llm_query",
    description: "Recursively call LLM on a sub-prompt",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string" }
      }
    }
  }
];
```

### MCP + RLM Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP + RLM Combined                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Claude /   │ MCP  │  RLM Server  │                     │
│  │   Cursor     │◄────►│              │                     │
│  └──────────────┘      └──────┬───────┘                     │
│                               │                              │
│                        ┌──────▼───────┐                     │
│                        │   Resources   │                     │
│                        │ ┌───────────┐ │                     │
│                        │ │ prompt.txt│ │ ← Externalized      │
│                        │ │ context/* │ │   prompt/context    │
│                        │ │ state.json│ │                     │
│                        │ └───────────┘ │                     │
│                        └───────────────┘                     │
│                               │                              │
│                        ┌──────▼───────┐                     │
│                        │    Tools      │                     │
│                        │ ┌───────────┐ │                     │
│                        │ │ llm_query │ │ ← Recursive calls   │
│                        │ │ execute   │ │                     │
│                        │ │ read_chunk│ │                     │
│                        │ └───────────┘ │                     │
│                        └───────────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.4 Everything is Context: File System Abstraction

### The Paper (arXiv 2512.05470)

**"Everything is Context: Agentic File System Abstraction for Context Engineering"** by Xu et al. at CSIRO Data61.

### Core Thesis

> The emerging challenge is no longer model fine-tuning but **context engineering**—how systems capture, structure, and govern external knowledge, memory, tools, and human input to enable trustworthy reasoning.

### The Unix Philosophy Applied to AI

Just as Unix treats "everything as a file," this paper proposes treating **everything as context files**:

```
┌────────────────────────────────────────────────────────────┐
│               AGENTIC FILE SYSTEM ABSTRACTION               │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  /context/                                                  │
│  ├── user_input.txt          ← User's original request     │
│  ├── system_instructions.md  ← System prompt               │
│  ├── retrieved/              ← RAG results                 │
│  │   ├── doc1.txt                                          │
│  │   └── doc2.txt                                          │
│  ├── tools/                  ← Tool definitions            │
│  │   ├── search.json                                       │
│  │   └── execute.json                                      │
│  ├── memory/                 ← Persistent state            │
│  │   ├── session.json                                      │
│  │   └── facts.json                                        │
│  └── history/                ← Conversation turns          │
│      ├── turn_001.json                                     │
│      ├── turn_002.json                                     │
│      └── turn_003.json                                     │
│                                                             │
│  /output/                                                   │
│  ├── response.txt            ← LLM's response              │
│  ├── reasoning.json          ← Chain of thought            │
│  └── citations.json          ← Sources used                │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **Uniform interface** | All context accessed via file operations |
| **Traceability** | Every artifact is versioned and auditable |
| **Composability** | Standard tools (grep, cat, etc.) work |
| **Persistence** | Context survives across sessions |
| **Governance** | Access control via file permissions |

### The AIGNE Framework Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Context   │───►│   Context   │───►│   Context   │
│ Constructor │    │   Loader    │    │  Evaluator  │
│             │    │             │    │             │
│ Assembles   │    │ Delivers to │    │ Validates   │
│ artifacts   │    │ LLM prompt  │    │ outputs     │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Relation to RLM

The file system abstraction **implements** what RLM theorizes:

| RLM Concept | File System Implementation |
|-------------|---------------------------|
| Symbolic prompt | `/context/user_input.txt` |
| External context | `/context/data/*` |
| Persistent state | `/context/memory/session.json` |
| Recursive results | `/context/history/turn_*.json` |

---

## 2.5 Dynamic Context Discovery (Cursor)

### The Blog Post

**"Dynamic Context Discovery"** from Cursor's engineering blog (January 2026).

### Core Insight

> "As models have become better as agents, we've found success by providing fewer details up front, making it easier for the agent to pull relevant context on its own."

### Static vs Dynamic Context

| Static Context | Dynamic Context |
|----------------|-----------------|
| Always in prompt | Loaded on-demand |
| Bloats token count | Token-efficient |
| May confuse model | Only relevant data |
| Fixed at start | Adapts during task |

### Five Implementation Patterns

#### Pattern 1: Long Tool Responses → Files

**Problem:** MCP/shell output bloats context.

**Solution:** Write to file, let agent read with `tail`/`grep`.

```
Before: { "tool_output": "...10,000 lines of JSON..." }
After:  { "tool_output": "Written to /tmp/result.json" }
        Agent: `tail -100 /tmp/result.json`
```

**Result:** No truncation, no data loss.

#### Pattern 2: Chat History → Files

**Problem:** Summarization loses details.

**Solution:** Store full history as file, let agent search.

```
/history/
├── turn_001.json
├── turn_002.json
└── turn_003.json

Agent: `grep -l "authentication" /history/*.json`
```

**Result:** Agent can recover forgotten details.

#### Pattern 3: Agent Skills → Files

**Problem:** Skills bloat system prompt.

**Solution:** Skills are files, discovered via search.

```
/skills/
├── python_debugging.md
├── react_patterns.md
└── sql_optimization.md

Agent: codebase_search("how to debug Python")
→ Finds python_debugging.md, loads it
```

#### Pattern 4: MCP Tools → Files

**Problem:** MCP tool descriptions bloat context.

**Solution:** Sync tool metadata to folder, load on-demand.

```
/mcp_tools/
├── github_search.json
├── slack_post.json
└── jira_create.json

# Only tool NAMES in prompt
# Agent looks up tool when needed
```

**Result:** **46.9% token reduction** in A/B test.

#### Pattern 5: Terminal Sessions → Files

**Problem:** Can't reference terminal output.

**Solution:** Sync terminal to filesystem.

```
/terminals/
├── 1.txt  ← Terminal 1 output
└── 2.txt  ← Terminal 2 output

Agent: `grep "Error" /terminals/1.txt`
```

---

## 2.6 Clear Thought 1.5

### What It Is

**Clear Thought 1.5** is an MCP server providing 30+ structured reasoning operations with session state management.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   CLEAR THOUGHT 1.5                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Single Tool: clear_thought                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  {                                                      │  │
│  │    "operation": "sequential_thinking" | "tree_of_thought"│ │
│  │                 | "pdr_reasoning" | "decision_framework" │ │
│  │                 | ... (30+ operations),                  │ │
│  │    "prompt": "Your reasoning task",                     │  │
│  │    "sessionId": "persistent-session-id",                │  │
│  │    "parameters": { ... }                                │  │
│  │  }                                                      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  Session State:                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  SessionState {                                         │  │
│  │    unifiedStore: Map<type, data[]>,                     │  │
│  │    pdrGraphs: Map<id, PDRKnowledgeGraph>,               │  │
│  │    oodaSessions: Map<id, OODASession>,                  │  │
│  │    ulyssesSessions: Map<id, UlyssesSession>,            │  │
│  │  }                                                      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Key Operations

| Category | Operations |
|----------|------------|
| **Core** | `sequential_thinking`, `mental_model`, `debugging_approach`, `creative_thinking` |
| **Patterns** | `tree_of_thought`, `beam_search`, `mcts`, `graph_of_thought` |
| **Analysis** | `causal_analysis`, `statistical_reasoning`, `ethical_analysis` |
| **Metagame** | `ooda_loop`, `ulysses_protocol`, `pdr_reasoning` |
| **Session** | `session_info`, `session_export`, `session_import` |

### PDR Knowledge Graph

Clear Thought maintains a **hierarchical knowledge graph**:

```typescript
interface PDRNode {
  id: string;
  content: string;
  type: "subject" | "observation" | "hypothesis" | "evidence" | "conclusion";
  depth: number;
  parentId?: string;
  childrenIds: Set<string>;
  scores: {
    confidence: number;
    centrality: number;
  };
}
```

This is **externalized reasoning state**—exactly what RLM theorizes.

---

# Part II: Omar Khattab's Key Insights

## Who Is Omar Khattab?

- **Position:** Assistant Professor at MIT CSAIL
- **Research:** ColBERT, DSPy, RLMs, GEPA
- **Twitter:** [@lateinteraction](https://x.com/lateinteraction) (27,800+ followers)
- **Impact:** Co-author of the RLM paper with Alex Zhang

## The Core Tweet (January 6, 2026)

> **FAQ: Can I get similar results to an RLM if I modify Claude Code to (1) read my prompt/request from a local file and (2) access a new tool/skill for recursive llm_query?**
>
> **Yes.** If you store the input prompt as a symbolic object external to the LLM, create a tool for recursive calls, and allow for a persistent coding environment, you are implementing a complete RLM.
>
> Notice that this is not how CC handles user prompts by default. For sufficiently long requests, this RLM approach of externalizing the prompt may work better than (or better with) the typical compaction method.
>
> It's that simple and general. **We think all LLMs in the future should have symbolic access to their prompts.**

## The Sub-Agents Clarification

> **FAQ#2: Can I just use some kind of 'sub-agents'?**
>
> **No.** If your prompt is a sequence of tokens given directly to the Transformer/DNN, it's not an RLM and is vastly less expressive. The LLM will often fail to process the full prompt or to write the sub-calls non-symbolically.

## Key Principles Extracted

### Principle 1: Symbolic vs Token Access

```
Token Access (Traditional):
  prompt → tokenizer → [token_1, token_2, ... token_N] → Transformer
  ↓
  Lossy, compressed, no structure

Symbolic Access (RLM):
  prompt → file_system["prompt.txt"]
  ↓
  LLM reads: open("prompt.txt").read()
  ↓
  Full structure preserved, arbitrarily large
```

### Principle 2: The Three Requirements

An RLM requires exactly three things:

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| **1. External prompt** | Prompt stored as object, not tokens | File, database, variable |
| **2. Recursive tool** | LLM can call LLMs | `llm_query()` function |
| **3. Persistent environment** | State survives across calls | REPL, session state |

### Principle 3: Expressiveness Gap

> "If your prompt is a sequence of tokens given directly to the Transformer/DNN, it's not an RLM and is **vastly less expressive**."

The gap isn't incremental—it's **categorical**:

| Capability | Token-Based | RLM |
|------------|-------------|-----|
| Max context | ~200K tokens | **Unlimited** |
| Decomposition | Model tries to hold in attention | **Programmatic chunking** |
| State | None | **Persistent variables** |
| Strategy | Fixed by prompt | **Dynamic, self-determined** |
| Recursion | Simulated | **Actual recursive calls** |

### Principle 4: Future of LLMs

> "We think all LLMs in the future should have symbolic access to their prompts."

This predicts a fundamental architecture shift:

```
Current: LLM(tokens) → output

Future:  LLM(
           prompt = read("prompt.md"),
           context = query("memory.db"),
           tools = load("tools/*.json"),
           state = session.get("state")
         ) → output, state'
```

---

# Part III: What Works, What Doesn't, and Why

## What Didn't Work

### 1. Larger Context Windows

| Approach | Why It Failed |
|----------|---------------|
| 128K → 200K → 1M tokens | **Attention dilution**: Quality degrades with length |
| Longer training | **O(n²) cost**: 10x context = 100x compute |
| Infinite context claims | **Doesn't exist**: All models have limits |

**Evidence:** Models with 1M context still struggle with needle-in-haystack at scale.

### 2. Naive RAG

| Approach | Why It Failed |
|----------|---------------|
| Chunk + embed + retrieve | **Semantic chunking is lossy**: Breaks meaning |
| Top-K retrieval | **Wrong K**: Miss relevant, include irrelevant |
| Reranking | **Still bounded**: Can't correlate across entire corpus |

**Evidence:** RAG accuracy drops to ~60% on complex multi-hop queries.

### 3. Multi-Agent Without External State

| Approach | Why It Failed |
|----------|---------------|
| Spawn sub-agents | **Each sees tokens, not objects** |
| Agent handoffs | **Context compressed at each handoff** |
| Orchestration | **No shared memory** |

**Evidence:** Omar's FAQ#2 directly addresses this.

### 4. Simple Tool Use

| Approach | Why It Failed |
|----------|---------------|
| Function calling | **Can't express arbitrary algorithms** |
| Structured output | **JSON can't represent iteration** |
| Predefined workflows | **Can't adapt to problem** |

**Evidence:** RLM outperforms fixed tool pipelines by adapting strategy.

## What Works

### 1. Externalized Prompt Storage

**Implementation:**
```python
# Store prompt as file
with open("prompt.txt", "w") as f:
    f.write(user_prompt)

# LLM accesses symbolically
prompt = open("prompt.txt").read()
```

**Why it works:** Prompt retains structure, can be arbitrarily large, accessible via code.

### 2. Recursive LLM Calls

**Implementation:**
```python
def llm_query(sub_prompt: str) -> str:
    """Call LLM on a sub-problem."""
    return openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": sub_prompt}]
    ).choices[0].message.content
```

**Why it works:** Decomposes problems, distributes context, enables any algorithm.

### 3. Persistent REPL Environment

**Implementation:**
```python
class REPLEnv:
    def __init__(self):
        self.globals = {"llm_query": llm_query}
        self.locals = {}  # Persists across iterations
    
    def execute(self, code: str):
        exec(code, self.globals, self.locals)
```

**Why it works:** Variables persist, results accumulate, state builds up.

### 4. File-Based Context Discovery

**Implementation:**
```python
# Write context to files
context_dir = Path("/context")
context_dir.mkdir(exist_ok=True)
(context_dir / "data.json").write_text(json.dumps(large_data))

# LLM discovers via tools
def read_context(path: str) -> str:
    return Path(path).read_text()

def search_context(query: str) -> list[str]:
    return grep(query, context_dir)
```

**Why it works:** On-demand loading, no token bloat, standard tooling.

## Why It Works: The Unified Theory

All successful approaches share three properties:

| Property | Description | Mechanism |
|----------|-------------|-----------|
| **Externalization** | State outside attention window | Files, DBs, variables |
| **Symbolic access** | LLM manipulates objects, not tokens | Code execution, tools |
| **Persistence** | State survives across calls | Session, filesystem |

The key insight:

> **Transform the LLM from a stateless function on tokens to a stateful agent with symbolic access to its environment.**

---

# Part IV: The Unified Synthesis

## The Convergence

All five approaches (RLM, MCP, Cursor, File System, Clear Thought) converge on the same architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    EXTERNAL STATE LAYER                   │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐          │   │
│  │  │   Files    │  │   Memory   │  │   History  │          │   │
│  │  │ /context/  │  │  session   │  │  /history/ │          │   │
│  │  │ /tools/    │  │   state    │  │  /turns/   │          │   │
│  │  └────────────┘  └────────────┘  └────────────┘          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     MCP / TOOL LAYER                      │   │
│  │                                                           │   │
│  │  read_file()    write_file()    llm_query()              │   │
│  │  search()       execute()       clear_thought()           │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    REASONING LAYER                        │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │   Clear     │  │    RLM      │  │   Custom    │       │   │
│  │  │   Thought   │  │    REPL     │  │  Patterns   │       │   │
│  │  │             │  │             │  │             │       │   │
│  │  │ 30+ ops     │  │ llm_query() │  │ Your logic  │       │   │
│  │  │ PDR graphs  │  │ persistent  │  │             │       │   │
│  │  │ sessions    │  │ variables   │  │             │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      LLM LAYER                            │   │
│  │                                                           │   │
│  │  Root LLM (orchestrator) + Sub-LLMs (workers)            │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## The Integration Formula

```typescript
// Unified Externalized Reasoning System
interface ExternalizedReasoningSystem {
  // 1. External State (File System Abstraction)
  state: {
    prompt: FilePath;           // /context/prompt.txt
    context: FilePath[];        // /context/data/*
    history: FilePath[];        // /history/turn_*.json
    memory: SessionState;       // Persistent key-value
  };
  
  // 2. Tools (MCP + RLM)
  tools: {
    llm_query: (prompt: string) => string;          // RLM recursive
    clear_thought: (op: Operation) => Result;       // Structured reasoning
    read_file: (path: string) => string;            // Context access
    search: (query: string) => string[];            // Discovery
    execute: (code: string) => ExecutionResult;     // REPL
  };
  
  // 3. Reasoning Patterns (Clear Thought + Custom)
  patterns: {
    sequential: ChainOfThought;
    tree: TreeOfThought;
    pdr: ProbeDetectRespond;
    decision: MultiCriteriaDecision;
  };
  
  // 4. Session Management
  session: {
    id: string;
    export: () => JSON;
    import: (data: JSON) => void;
    persist: () => void;
  };
}
```

## Combining All Approaches

### Step 1: Externalize Everything

```python
# Instead of: llm.chat("Analyze this: {giant_context}")

# Do this:
context_path = Path("/context")
(context_path / "prompt.txt").write_text(user_prompt)
(context_path / "data.json").write_text(json.dumps(large_data))
(context_path / "instructions.md").write_text(system_prompt)
```

### Step 2: Provide Recursive Tools

```python
def create_tools(session_id: str) -> dict:
    return {
        "llm_query": lambda p: call_llm(p),
        "clear_thought": lambda op, p, params: mcp_call("clear_thought", {
            "operation": op,
            "prompt": p,
            "parameters": params,
            "sessionId": session_id
        }),
        "read_file": lambda p: Path(p).read_text(),
        "write_file": lambda p, c: Path(p).write_text(c),
        "search": lambda q: grep(q, "/context"),
    }
```

### Step 3: Create Persistent Environment

```python
class UnifiedREPL:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.tools = create_tools(session_id)
        self.locals = {}  # Persistent across calls
        
        # Load session state
        self.session = SessionState.load(session_id)
    
    def execute(self, code: str) -> REPLResult:
        namespace = {**self.tools, **self.locals}
        exec(code, namespace, namespace)
        
        # Update locals
        self.locals = {k: v for k, v in namespace.items() 
                       if k not in self.tools}
        
        # Persist session
        self.session.save()
        
        return REPLResult(...)
```

### Step 4: Use Structured Reasoning

```python
# In REPL, LLM can invoke structured patterns:
result = clear_thought(
    "tree_of_thought",
    "Explore three approaches to this bug",
    {"branchingFactor": 3, "maxDepth": 3}
)

# Or use PDR for systematic investigation:
investigation = clear_thought(
    "pdr_reasoning",
    "Probe the authentication failure",
    {"mode": "probe"}
)
```

### Step 5: Dynamic Discovery

```python
# LLM discovers context on-demand
chunks = search("authentication error")  # → ["context/logs.json"]
relevant = read_file("context/logs.json")
analysis = llm_query(f"Analyze these logs: {relevant[:50000]}")
```

---

# Part V: Production Architecture

## Complete Production System

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      API LAYER                               │    │
│  │  FastAPI / Express                                          │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │  POST /reason                                         │   │    │
│  │  │  {                                                    │   │    │
│  │  │    "prompt": "...",                                   │   │    │
│  │  │    "context_ids": ["ctx_123", "ctx_456"],             │   │    │
│  │  │    "session_id": "sess_789"                           │   │    │
│  │  │  }                                                    │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                               │                                      │
│                               ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     QUEUE LAYER                              │    │
│  │  Redis / RabbitMQ / SQS                                     │    │
│  │  ┌────────────────────────────────────────────────────┐     │    │
│  │  │  Job: { id, prompt_path, context_paths, session }  │     │    │
│  │  └────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                               │                                      │
│                               ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    WORKER LAYER                              │    │
│  │  Kubernetes Pods / Docker Containers                        │    │
│  │  ┌────────────────────────────────────────────────────┐     │    │
│  │  │  Worker Pod                                         │     │    │
│  │  │  ┌────────────────────────────────────────────┐    │     │    │
│  │  │  │  SANDBOX CONTAINER                          │    │     │    │
│  │  │  │  - Network isolated                         │    │     │    │
│  │  │  │  - Resource limited                         │    │     │    │
│  │  │  │  - Read-only filesystem (except /tmp)       │    │     │    │
│  │  │  │                                             │    │     │    │
│  │  │  │  ┌──────────────────────────────────────┐  │    │     │    │
│  │  │  │  │  Unified REPL                        │  │    │     │    │
│  │  │  │  │  + MCP Client (Clear Thought)        │  │    │     │    │
│  │  │  │  │  + File System Access                │  │    │     │    │
│  │  │  │  │  + LLM Client                        │  │    │     │    │
│  │  │  │  └──────────────────────────────────────┘  │    │     │    │
│  │  │  └────────────────────────────────────────────┘    │     │    │
│  │  └────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                               │                                      │
│                               ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    STORAGE LAYER                             │    │
│  │                                                              │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │    │
│  │  │   Object   │  │  Session   │  │   Result   │             │    │
│  │  │   Store    │  │   Store    │  │   Store    │             │    │
│  │  │            │  │            │  │            │             │    │
│  │  │  S3/R2     │  │   Redis    │  │  Postgres  │             │    │
│  │  │  contexts  │  │   states   │  │   outputs  │             │    │
│  │  └────────────┘  └────────────┘  └────────────┘             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Implementation: TypeScript MCP Server

```typescript
// externalized-reasoning-server.ts

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { z } from "zod";

// Schema for the unified reasoning tool
const ReasoningParamsSchema = z.object({
  operation: z.enum([
    // RLM operations
    "recursive_query",
    "chunk_process",
    
    // Clear Thought operations  
    "sequential_thinking",
    "tree_of_thought",
    "pdr_reasoning",
    "decision_framework",
    
    // File operations
    "read_context",
    "write_context",
    "search_context",
    
    // Session operations
    "session_info",
    "session_export",
    "session_import",
  ]),
  prompt: z.string(),
  sessionId: z.string().optional(),
  parameters: z.record(z.any()).optional(),
});

// Session state management
class ExternalizedSessionState {
  private store: Map<string, any> = new Map();
  private history: Array<{role: string, content: string}> = [];
  private variables: Map<string, any> = new Map();
  
  constructor(private sessionId: string) {
    this.load();
  }
  
  // Persist to file system (externalized state)
  save() {
    const state = {
      store: Object.fromEntries(this.store),
      history: this.history,
      variables: Object.fromEntries(this.variables),
    };
    fs.writeFileSync(
      `/sessions/${this.sessionId}.json`,
      JSON.stringify(state, null, 2)
    );
  }
  
  load() {
    try {
      const data = JSON.parse(
        fs.readFileSync(`/sessions/${this.sessionId}.json`, 'utf-8')
      );
      this.store = new Map(Object.entries(data.store || {}));
      this.history = data.history || [];
      this.variables = new Map(Object.entries(data.variables || {}));
    } catch {
      // New session
    }
  }
  
  // Methods for externalized operations
  setVariable(name: string, value: any) {
    this.variables.set(name, value);
    this.save();
  }
  
  getVariable(name: string): any {
    return this.variables.get(name);
  }
  
  addToHistory(role: string, content: string) {
    this.history.push({ role, content });
    this.save();
  }
  
  getHistory(): Array<{role: string, content: string}> {
    return this.history;
  }
}

// Main server
const server = new Server({
  name: "externalized-reasoning",
  version: "1.0.0",
}, {
  capabilities: {
    tools: {},
    resources: {},
  }
});

// Register the unified tool
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { operation, prompt, sessionId, parameters } = 
    ReasoningParamsSchema.parse(request.params.arguments);
  
  const session = new ExternalizedSessionState(sessionId || "default");
  
  switch (operation) {
    case "recursive_query": {
      // RLM-style recursive call
      const result = await llmClient.chat([
        { role: "system", content: "You are a sub-processor." },
        { role: "user", content: prompt }
      ]);
      session.addToHistory("assistant", result);
      return { content: [{ type: "text", text: result }] };
    }
    
    case "chunk_process": {
      // Process large context in chunks
      const contextPath = parameters?.contextPath;
      const context = await fs.promises.readFile(contextPath, 'utf-8');
      const chunkSize = parameters?.chunkSize || 100000;
      
      const chunks = [];
      for (let i = 0; i < context.length; i += chunkSize) {
        chunks.push(context.slice(i, i + chunkSize));
      }
      
      const results = [];
      for (const chunk of chunks) {
        const result = await llmClient.chat([
          { role: "user", content: `${prompt}\n\nChunk:\n${chunk}` }
        ]);
        results.push(result);
      }
      
      session.setVariable("chunk_results", results);
      return { content: [{ type: "text", text: JSON.stringify(results) }] };
    }
    
    case "sequential_thinking": {
      // Clear Thought style sequential reasoning
      const thoughts = [];
      const totalThoughts = parameters?.totalThoughts || 5;
      
      for (let i = 1; i <= totalThoughts; i++) {
        const previousThoughts = thoughts.map((t, idx) => 
          `Thought ${idx + 1}: ${t}`
        ).join("\n");
        
        const thought = await llmClient.chat([
          { role: "system", content: `Think step by step. This is thought ${i} of ${totalThoughts}.` },
          { role: "user", content: `${prompt}\n\nPrevious thoughts:\n${previousThoughts}\n\nWhat is thought ${i}?` }
        ]);
        
        thoughts.push(thought);
        session.setVariable(`thought_${i}`, thought);
      }
      
      return { 
        content: [{ 
          type: "text", 
          text: JSON.stringify({ thoughts, sessionId: session.sessionId })
        }]
      };
    }
    
    case "read_context": {
      // Dynamic context discovery
      const path = parameters?.path;
      const content = await fs.promises.readFile(path, 'utf-8');
      return { content: [{ type: "text", text: content }] };
    }
    
    case "search_context": {
      // Search externalized context
      const query = parameters?.query;
      const contextDir = parameters?.contextDir || "/context";
      
      const { stdout } = await exec(`grep -r "${query}" ${contextDir}`);
      return { content: [{ type: "text", text: stdout }] };
    }
    
    // ... more operations
  }
});

// Register resources for context discovery
server.setRequestHandler(ListResourcesRequestSchema, () => ({
  resources: [
    {
      uri: "context://prompt",
      name: "Current Prompt",
      description: "The externalized user prompt",
      mimeType: "text/plain"
    },
    {
      uri: "context://history",
      name: "Conversation History", 
      description: "Full conversation history",
      mimeType: "application/json"
    },
    {
      uri: "context://variables",
      name: "Session Variables",
      description: "Persistent REPL variables",
      mimeType: "application/json"
    }
  ]
}));
```

## Implementation: Python RLM with Clear Thought

```python
# unified_rlm.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import json
import asyncio

from mcp import ClientSession
from openai import OpenAI

@dataclass
class UnifiedSession:
    """Externalized session state."""
    session_id: str
    prompt_path: Path
    context_dir: Path
    history: list[dict] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    thoughts: list[str] = field(default_factory=list)
    
    def save(self):
        state_path = self.context_dir / f"session_{self.session_id}.json"
        state_path.write_text(json.dumps({
            "history": self.history,
            "variables": {k: str(v) for k, v in self.variables.items()},
            "thoughts": self.thoughts,
        }, indent=2))
    
    @classmethod
    def load(cls, session_id: str, context_dir: Path) -> "UnifiedSession":
        state_path = context_dir / f"session_{session_id}.json"
        if state_path.exists():
            data = json.loads(state_path.read_text())
            return cls(
                session_id=session_id,
                prompt_path=context_dir / "prompt.txt",
                context_dir=context_dir,
                history=data.get("history", []),
                variables=data.get("variables", {}),
                thoughts=data.get("thoughts", []),
            )
        return cls(
            session_id=session_id,
            prompt_path=context_dir / "prompt.txt",
            context_dir=context_dir,
        )


class UnifiedRLM:
    """
    Unified RLM combining:
    - Externalized state (file system)
    - Recursive LLM calls
    - Clear Thought structured reasoning
    - Dynamic context discovery
    """
    
    def __init__(
        self,
        model: str = "gpt-4",
        context_dir: Path = Path("/context"),
        mcp_server_url: Optional[str] = None,
    ):
        self.llm = OpenAI()
        self.model = model
        self.context_dir = context_dir
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.mcp_client = None
        self.mcp_server_url = mcp_server_url
    
    async def setup_mcp(self):
        """Connect to Clear Thought MCP server."""
        if self.mcp_server_url:
            self.mcp_client = await ClientSession.connect(self.mcp_server_url)
    
    def externalize_prompt(self, prompt: str, session_id: str) -> Path:
        """Store prompt as external file (RLM principle 1)."""
        prompt_path = self.context_dir / f"prompt_{session_id}.txt"
        prompt_path.write_text(prompt)
        return prompt_path
    
    def externalize_context(self, context: Any, name: str) -> Path:
        """Store context as external file."""
        context_path = self.context_dir / f"{name}.json"
        context_path.write_text(json.dumps(context, indent=2))
        return context_path
    
    def llm_query(self, prompt: str, session: UnifiedSession) -> str:
        """Recursive LLM call (RLM principle 2)."""
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.choices[0].message.content
        
        # Track in session
        session.history.append({"role": "assistant", "content": result})
        session.save()
        
        return result
    
    async def clear_thought(
        self, 
        operation: str, 
        prompt: str, 
        session: UnifiedSession,
        parameters: dict = None,
    ) -> dict:
        """Call Clear Thought MCP for structured reasoning."""
        if not self.mcp_client:
            await self.setup_mcp()
        
        result = await self.mcp_client.call_tool("clear_thought", {
            "operation": operation,
            "prompt": prompt,
            "sessionId": session.session_id,
            "parameters": parameters or {},
        })
        
        # Store in session
        session.thoughts.append(json.dumps(result))
        session.save()
        
        return result
    
    def read_context(self, path: str) -> str:
        """Dynamic context discovery."""
        return Path(path).read_text()
    
    def search_context(self, query: str) -> list[str]:
        """Search externalized context."""
        import subprocess
        result = subprocess.run(
            ["grep", "-r", "-l", query, str(self.context_dir)],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip().split("\n") if result.stdout else []
    
    async def completion(
        self,
        prompt: str,
        context: Any = None,
        session_id: str = "default",
        max_iterations: int = 20,
    ) -> str:
        """
        Main RLM completion with externalized state.
        """
        # 1. Externalize prompt and context
        prompt_path = self.externalize_prompt(prompt, session_id)
        if context:
            self.externalize_context(context, f"context_{session_id}")
        
        # 2. Load or create session
        session = UnifiedSession.load(session_id, self.context_dir)
        session.prompt_path = prompt_path
        
        # 3. Build tools for REPL
        tools = {
            "llm_query": lambda p: self.llm_query(p, session),
            "clear_thought": lambda op, p, params=None: asyncio.run(
                self.clear_thought(op, p, session, params)
            ),
            "read_context": self.read_context,
            "search_context": self.search_context,
            "get_variable": lambda name: session.variables.get(name),
            "set_variable": lambda name, value: session.variables.update({name: value}),
        }
        
        # 4. Build system prompt
        system_prompt = self._build_system_prompt(tools)
        
        # 5. Main RLM loop
        messages = [{"role": "system", "content": system_prompt}]
        
        for iteration in range(max_iterations):
            # Add current prompt
            current_prompt = self._build_iteration_prompt(
                prompt_path.read_text(), 
                iteration,
                session,
            )
            messages.append({"role": "user", "content": current_prompt})
            
            # Query LLM
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            assistant_msg = response.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_msg})
            
            # Parse and execute code blocks
            code_blocks = self._extract_code_blocks(assistant_msg)
            for code in code_blocks:
                result = self._execute_in_repl(code, tools, session)
                messages.append({"role": "tool", "content": result})
            
            # Check for final answer
            if final := self._check_final_answer(assistant_msg, session):
                return final
            
            session.save()
        
        # Fallback
        return self._force_final_answer(messages, session)
    
    def _build_system_prompt(self, tools: dict) -> str:
        return f"""You are an RLM (Recursive Language Model) with externalized state.

You have access to these tools via Python code blocks:
- llm_query(prompt): Recursively call an LLM on a sub-prompt
- clear_thought(operation, prompt, params): Use structured reasoning (tree_of_thought, pdr_reasoning, etc.)
- read_context(path): Read from the externalized context
- search_context(query): Search the context directory
- get_variable(name): Get a persistent variable
- set_variable(name, value): Set a persistent variable

Your context is stored externally in files, not as tokens. You can process unlimited context by:
1. Reading chunks with read_context()
2. Processing chunks with llm_query()
3. Storing intermediate results with set_variable()
4. Using structured reasoning with clear_thought()

To provide a final answer, use: FINAL(your_answer)
Or to return a variable: FINAL_VAR(variable_name)

Write Python code in ```repl blocks to execute."""
    
    def _build_iteration_prompt(
        self, 
        prompt: str, 
        iteration: int, 
        session: UnifiedSession,
    ) -> str:
        variables_str = "\n".join(
            f"  {k}: {v}" for k, v in session.variables.items()
        ) or "  (none)"
        
        return f"""Iteration {iteration + 1}

Original prompt (from file): {prompt[:500]}...

Current session variables:
{variables_str}

What is your next action? Write code in ```repl blocks or provide FINAL(answer)."""
    
    def _extract_code_blocks(self, text: str) -> list[str]:
        import re
        pattern = r"```(?:repl|python)\n(.*?)```"
        return re.findall(pattern, text, re.DOTALL)
    
    def _execute_in_repl(
        self, 
        code: str, 
        tools: dict, 
        session: UnifiedSession,
    ) -> str:
        import io
        import sys
        
        # Capture output
        stdout = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout
        
        try:
            namespace = {**tools, **session.variables}
            exec(code, namespace, namespace)
            
            # Update session variables
            for k, v in namespace.items():
                if k not in tools and not k.startswith("_"):
                    session.variables[k] = v
            
            output = stdout.getvalue()
            return f"Execution successful.\nOutput:\n{output}"
        except Exception as e:
            return f"Execution error: {e}"
        finally:
            sys.stdout = old_stdout
    
    def _check_final_answer(self, text: str, session: UnifiedSession) -> Optional[str]:
        import re
        
        # Check for FINAL(answer)
        if match := re.search(r"FINAL\((.*?)\)", text, re.DOTALL):
            return match.group(1).strip()
        
        # Check for FINAL_VAR(name)
        if match := re.search(r"FINAL_VAR\([\"']?(\w+)[\"']?\)", text):
            var_name = match.group(1)
            return str(session.variables.get(var_name, f"Variable {var_name} not found"))
        
        return None
    
    def _force_final_answer(self, messages: list, session: UnifiedSession) -> str:
        messages.append({
            "role": "user", 
            "content": "Maximum iterations reached. Please provide your final answer now with FINAL(answer)."
        })
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        
        return response.choices[0].message.content


# Usage example
async def main():
    rlm = UnifiedRLM(
        model="gpt-4",
        context_dir=Path("./context"),
        mcp_server_url="http://localhost:3000/mcp",
    )
    
    # Large context that wouldn't fit in a single call
    large_document = Path("huge_document.txt").read_text()
    
    result = await rlm.completion(
        prompt="Find all mentions of 'authentication' and summarize the security implications",
        context={"document": large_document[:1000000]},  # 1M chars
        session_id="security_analysis",
    )
    
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

---

# High-Signal Summary

## The One-Sentence Insight

> **Store prompts, context, and state as symbolic objects external to the LLM, provide tools for recursive calls and structured reasoning, and let the LLM dynamically discover and process information—this transforms bounded token processors into unbounded reasoning systems.**

## The Three Requirements

| # | Requirement | Implementation |
|---|-------------|----------------|
| 1 | **External prompt/context** | Files, databases, object stores |
| 2 | **Recursive LLM tool** | `llm_query()` function |
| 3 | **Persistent environment** | REPL with surviving variables |

## The Five Key Patterns

| Pattern | Source | Implementation |
|---------|--------|----------------|
| **Symbolic prompt access** | RLM/Omar | Store prompt as file, read via code |
| **Recursive decomposition** | RLM | `llm_query()` on sub-problems |
| **Dynamic context discovery** | Cursor | Write to files, agent greps/reads |
| **File system abstraction** | arXiv paper | `/context/*`, `/history/*`, `/tools/*` |
| **Structured reasoning** | Clear Thought | MCP operations with session state |

## The Production Checklist

```
□ Externalize prompts to files (not tokens)
□ Externalize large context to object storage
□ Implement llm_query() recursive tool
□ Create persistent session state
□ Add file read/write/search tools
□ Integrate structured reasoning (Clear Thought or similar)
□ Sandbox code execution (containers)
□ Add cost/latency monitoring
□ Implement session export/import
□ Set up async job processing
```

## The Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                 EXTERNALIZED REASONING SYSTEM                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  /context/                    ┌─────────────────────────┐   │
│  ├── prompt.txt              │      MCP TOOLS          │   │
│  ├── data/*.json             │  ┌─────────────────┐    │   │
│  └── history/*.json          │  │ llm_query()     │    │   │
│           │                   │  │ clear_thought() │    │   │
│           ▼                   │  │ read_file()     │    │   │
│  ┌─────────────┐             │  │ search()        │    │   │
│  │   REPL      │◄────────────┤  └─────────────────┘    │   │
│  │  + locals   │             │                          │   │
│  │  + session  │             └─────────────────────────┘   │
│  └──────┬──────┘                                            │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    ROOT LLM                          │   │
│  │  Generates code → Executes → Checks results → Loops │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Metrics

| Metric | Traditional | Externalized | Improvement |
|--------|-------------|--------------|-------------|
| Max context | ~200K tokens | **Unlimited** | ∞ |
| Token usage (MCP) | 100% | 53.1% | **46.9% reduction** |
| State persistence | None | Full | **Stateful** |
| Reasoning patterns | Ad-hoc | Structured | **30+ patterns** |

---

# References

## Papers

1. **Recursive Language Models** - Zhang, Kraska, Khattab (2025)
   - arXiv: https://arxiv.org/abs/2512.24601
   - Blog: https://alexzhang13.github.io/blog/2025/rlm/
   - Code: https://github.com/alexzhang13/rlm

2. **Everything is Context: Agentic File System Abstraction** - Xu et al. (2025)
   - arXiv: https://arxiv.org/abs/2512.05470
   - AIGNE Framework implementation

## Blog Posts

3. **Dynamic Context Discovery** - Cursor (January 2026)
   - https://cursor.com/blog/dynamic-context-discovery

4. **Notes on Recursive Language Models** - Navendu Pottekkat
   - https://navendu.me/posts/recursive-language-models/

## Code & Frameworks

5. **Clear Thought 1.5** - WaldzellAI
   - https://github.com/waldzellai/clearthought-onepointfive

6. **Model Context Protocol** - Anthropic
   - https://modelcontextprotocol.io/

## Key Figures

7. **Omar Khattab** (@lateinteraction)
   - MIT CSAIL, co-author of RLM, DSPy, ColBERT
   - https://x.com/lateinteraction

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Author: Synthesized from RLM, MCP, Cursor, Clear Thought, and "Everything is Context" research*

