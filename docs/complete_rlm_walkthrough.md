# Complete RLM (Recursive Language Model) Paper & Code Walkthrough

> **Source Paper/Blogpost:** [Recursive Language Models by Alex Zhang](https://alexzhang13.github.io/blog/2025/rlm/)

This document provides a comprehensive, line-by-line walkthrough of the Recursive Language Model (RLM) concept and its implementation. It is designed for engineers who want to deeply understand how RLMs work, both conceptually and in practice.

---

## Table of Contents

1. [The RLM Paper: Core Concepts](#1-the-rlm-paper-core-concepts)
2. [Architecture Overview](#2-architecture-overview)
3. [Code Structure](#3-code-structure)
4. [Detailed File-by-File Walkthrough](#4-detailed-file-by-file-walkthrough)
5. [Data Flow & Execution](#5-data-flow--execution)
6. [Key Algorithms & Patterns](#6-key-algorithms--patterns)
7. [Practical Usage Examples](#7-practical-usage-examples)

---

## 1. The RLM Paper: Core Concepts

### 1.1 The Problem: Context Window Limitations

Traditional Large Language Models (LLMs) have a fundamental limitation: **finite context windows**. Even the most advanced models can only process a limited amount of text at once (e.g., 128K tokens for GPT-4, ~500K characters for newer models). This creates challenges when:

- Analyzing large codebases
- Processing extensive documents
- Searching through massive datasets (needle-in-a-haystack problems)
- Understanding long conversation histories

### 1.2 The Solution: Recursive Language Models

**RLM (Recursive Language Model)** solves this by introducing a **hierarchical, recursive architecture** where:

1. A **Root LM** orchestrates the overall task
2. The Root LM has access to a **REPL (Read-Eval-Print Loop) environment**
3. Within the REPL, the Root LM can call **Sub-LMs** to process chunks of data
4. The process is **iterative** - the Root LM continues until it finds a final answer

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                              │
│                    "Find the magic number"                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ROOT LM                                  │
│         (Orchestrator - decides what to do next)                │
│                                                                 │
│  "I need to search through this massive context.                │
│   Let me chunk it and query sub-LMs..."                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REPL ENVIRONMENT                             │
│         (Sandboxed Python execution environment)                │
│                                                                 │
│  Available:                                                     │
│  - context variable (the data to analyze)                       │
│  - llm_query() function (calls sub-LM)                          │
│  - FINAL_VAR() function (return variables as answer)            │
│  - Python standard library                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      ┌──────────┐      ┌──────────┐      ┌──────────┐
      │ SUB-LM 1 │      │ SUB-LM 2 │      │ SUB-LM N │
      │ Chunk 1  │      │ Chunk 2  │      │ Chunk N  │
      └──────────┘      └──────────┘      └──────────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGGREGATED RESULT                           │
│              "The magic number is 1298418"                      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Innovations from the Paper

#### 1.3.1 Divide and Conquer via Code Execution

Instead of trying to fit everything into one context window, RLM:
- Writes code to **chunk** the data intelligently
- Calls sub-LMs on each chunk
- **Aggregates** results programmatically

#### 1.3.2 Iterative Reasoning

The Root LM doesn't just make one call - it **iterates**:
1. Examines the context
2. Writes code to process it
3. Sees the results
4. Decides what to do next
5. Repeats until done

#### 1.3.3 REPL as a Cognitive Tool

The REPL environment acts as **extended working memory**:
- Variables persist across iterations
- Results from sub-LMs are stored
- The LM can build up complex state over time

### 1.4 Why This Works

| Traditional LLM | RLM |
|----------------|-----|
| Single-pass processing | Iterative refinement |
| Fixed context window | Virtually unlimited via chunking |
| Static analysis | Dynamic code execution |
| One model, one call | Hierarchical model coordination |
| Memory limited to context | REPL variables as extended memory |

---

## 2. Architecture Overview

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RLM_REPL CLASS                                 │
│                         (Main Entry Point)                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  - completion(context, query) → str                                   │  │
│  │  - setup_context(context, query)                                      │  │
│  │  - Main iteration loop (max_iterations)                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         OpenAIClient                                  │  │
│  │  - completion(messages) → str                                         │  │
│  │  - Wraps OpenAI API calls                                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          REPLEnv CLASS                                │  │
│  │  - code_execution(code) → REPLResult                                  │  │
│  │  - Sandboxed Python execution                                         │  │
│  │  - Contains: context, llm_query(), FINAL_VAR()                        │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                        Sub_RLM CLASS                            │  │  │
│  │  │  - completion(prompt) → str                                     │  │  │
│  │  │  - Simple LM for chunk processing                               │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Class Hierarchy

```
RLM (Abstract Base Class)
├── RLM_REPL (Main implementation with REPL environment)
└── Sub_RLM (Simplified LM for recursive calls within REPL)
```

---

## 3. Code Structure

```
rlm/
├── __init__.py              # Package init - exports RLM base class
├── rlm.py                   # Abstract base class definition
├── rlm_repl.py              # Main RLM implementation with REPL
├── repl.py                  # REPL environment + Sub_RLM class
├── logger/
│   ├── __init__.py          # Empty - package marker
│   ├── root_logger.py       # Colorful console logging for Root LM
│   └── repl_logger.py       # Rich-based Jupyter-style REPL output
└── utils/
    ├── __init__.py          # Empty - package marker
    ├── llm.py               # OpenAI API client wrapper
    ├── prompts.py           # System prompts and prompt templates
    └── utils.py             # Code execution, parsing, utilities
```

---

## 4. Detailed File-by-File Walkthrough

### 4.1 `rlm/__init__.py` - Package Entry Point

```python
from .rlm import RLM
```

**Purpose:** Makes the `RLM` base class available when you import the package.

**Usage:**
```python
from rlm import RLM  # Import the base class
```

---

### 4.2 `rlm/rlm.py` - Abstract Base Class

```python
from abc import ABC, abstractmethod

class RLM(ABC):
    @abstractmethod
    def completion(self, context: list[str] | str | dict[str, str], query: str) -> str:
        pass

    @abstractmethod
    def cost_summary(self) -> dict[str, float]:
        pass

    @abstractmethod
    def reset(self):
        pass
```

**Purpose:** Defines the interface that all RLM implementations must follow.

**Line-by-Line Explanation:**

| Line | Code | Explanation |
|------|------|-------------|
| 1 | `from abc import ABC, abstractmethod` | Import Python's Abstract Base Class machinery |
| 3 | `class RLM(ABC):` | Define RLM as an abstract class (cannot be instantiated directly) |
| 4-5 | `@abstractmethod def completion(...)` | **Core method** - takes context + query, returns answer. Must be implemented. |
| 8-9 | `@abstractmethod def cost_summary(...)` | Returns API cost tracking info. Placeholder for production use. |
| 12-13 | `@abstractmethod def reset(...)` | Resets internal state for new queries. |

**Design Decision:** Using an ABC ensures all RLM variants (RLM_REPL, Sub_RLM, future implementations) share the same interface.

---

### 4.3 `rlm/rlm_repl.py` - Main RLM Implementation

This is the **heart of the system**. Let's walk through it section by section.

#### 4.3.1 Imports and Dependencies

```python
"""
Simple Recursive Language Model (RLM) with REPL environment.
"""

from typing import Dict, List, Optional, Any 

from rlm import RLM
from rlm.repl import REPLEnv
from rlm.utils.llm import OpenAIClient
from rlm.utils.prompts import DEFAULT_QUERY, next_action_prompt, build_system_prompt
import rlm.utils.utils as utils

from rlm.logger.root_logger import ColorfulLogger
from rlm.logger.repl_logger import REPLEnvLogger
```

**Dependencies Map:**

| Import | Purpose |
|--------|---------|
| `RLM` | Base class to inherit from |
| `REPLEnv` | The sandboxed code execution environment |
| `OpenAIClient` | Wrapper for OpenAI API calls |
| `DEFAULT_QUERY`, `next_action_prompt`, `build_system_prompt` | Prompt templates |
| `utils` | Code parsing, execution helpers |
| `ColorfulLogger` | Console output for Root LM interactions |
| `REPLEnvLogger` | Jupyter-style output for REPL executions |

#### 4.3.2 Class Definition and Constructor

```python
class RLM_REPL(RLM):
    """
    LLM Client that can handle long contexts by recursively calling itself.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "gpt-5",
                 recursive_model: str = "gpt-5",
                 max_iterations: int = 20,
                 depth: int = 0,
                 enable_logging: bool = False,
                 ):
        self.api_key = api_key
        self.model = model
        self.recursive_model = recursive_model
        self.llm = OpenAIClient(api_key, model) # Replace with other client
        
        # Track recursive call depth to prevent infinite loops
        self.repl_env = None
        self.depth = depth # Unused in this version.
        self._max_iterations = max_iterations
        
        # Initialize colorful logger
        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)
        
        self.messages = [] # Initialize messages list
        self.query = None
```

**Constructor Parameters Explained:**

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `api_key` | `None` | OpenAI API key (falls back to env var) |
| `model` | `"gpt-5"` | Model for the **Root LM** (orchestrator) |
| `recursive_model` | `"gpt-5"` | Model for **Sub-LMs** (chunk processors) |
| `max_iterations` | `20` | Maximum iterations before forcing final answer |
| `depth` | `0` | Recursion depth tracking (unused in this version) |
| `enable_logging` | `False` | Enable colorful console output |

**Instance Variables:**

| Variable | Purpose |
|----------|---------|
| `self.llm` | OpenAI client for Root LM calls |
| `self.repl_env` | The REPL environment (initialized later) |
| `self._max_iterations` | Safety limit to prevent infinite loops |
| `self.logger` | Root LM logging |
| `self.repl_env_logger` | REPL execution logging |
| `self.messages` | Conversation history with the Root LM |
| `self.query` | The current user query |

#### 4.3.3 Context Setup Method

```python
def setup_context(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None):
    """
    Setup the context for the RLMClient.

    Args:
        context: The large context to analyze in the form of a list of messages, string, or Dict
        query: The user's question
    """
    if query is None:
        query = DEFAULT_QUERY

    self.query = query
    self.logger.log_query_start(query)

    # Initialize the conversation with the REPL prompt
    self.messages = build_system_prompt()
    self.logger.log_initial_messages(self.messages)
    
    # Initialize REPL environment with context data
    context_data, context_str = utils.convert_context_for_repl(context)
    
    self.repl_env = REPLEnv(
        context_json=context_data, 
        context_str=context_str, 
        recursive_model=self.recursive_model,
    )
    
    return self.messages
```

**Step-by-Step Flow:**

1. **Set default query** if none provided
2. **Log the query start** (for debugging/visibility)
3. **Build system prompt** - tells the LM about the REPL environment
4. **Convert context** - transforms user-provided context into REPL-compatible format
5. **Create REPL environment** - sandboxed Python execution space with context loaded

**Context Conversion Logic:**

The `convert_context_for_repl` function handles multiple input formats:
- **String**: Saved as `context.txt`, loaded as string
- **Dict**: Saved as `context.json`, loaded as Python dict
- **List of Dicts**: Extracted and saved as JSON

#### 4.3.4 The Main Completion Loop (Core Algorithm)

```python
def completion(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None) -> str:
    """
    Given a query and a (potentially long) context, recursively call the LM
    to explore the context and provide an answer using a REPL environment.
    """
    self.messages = self.setup_context(context, query)
    
    # Main loop runs for fixed # of root LM iterations
    for iteration in range(self._max_iterations):
        
        # Query root LM to interact with REPL environment
        response = self.llm.completion(self.messages + [next_action_prompt(query, iteration)])
        
        # Check for code blocks
        code_blocks = utils.find_code_blocks(response)
        self.logger.log_model_response(response, has_tool_calls=code_blocks is not None)
        
        # Process code execution or add assistant message
        if code_blocks is not None:
            self.messages = utils.process_code_execution(
                response, self.messages, self.repl_env, 
                self.repl_env_logger, self.logger
            )
        else:
            # Add assistant message when there are no code blocks
            assistant_message = {"role": "assistant", "content": "You responded with:\n" + response}
            self.messages.append(assistant_message)
        
        # Check that model produced a final answer
        final_answer = utils.check_for_final_answer(
            response, self.repl_env, self.logger,
        )

        # In practice, you may need some guardrails here.
        if final_answer:
            self.logger.log_final_response(final_answer)
            return final_answer

        
    # If we reach here, no final answer was found in any iteration
    print("No final answer found in any iteration")
    self.messages.append(next_action_prompt(query, iteration, final_answer=True))
    final_answer = self.llm.completion(self.messages)
    self.logger.log_final_response(final_answer)

    return final_answer
```

**The Core Loop Visualized:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ITERATION LOOP                                    │
│                     (max 20 iterations by default)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Query Root LM                                                     │
│ ─────────────────────                                                     │
│ self.llm.completion(messages + [next_action_prompt])                      │
│                                                                           │
│ The prompt tells the LM:                                                  │
│ - What the query is                                                       │
│ - That it has a REPL environment                                          │
│ - To write ```repl``` code blocks to execute                              │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Parse Response                                                    │
│ ─────────────────────                                                     │
│ code_blocks = utils.find_code_blocks(response)                            │
│                                                                           │
│ Looking for patterns like:                                                │
│ ```repl                                                                   │
│ chunk = context[:10000]                                                   │
│ result = llm_query(f"Find the magic number: {chunk}")                     │
│ print(result)                                                             │
│ ```                                                                       │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │ Has Code Blocks       │       │ No Code Blocks        │
        │ ───────────────       │       │ ──────────────        │
        │ Execute in REPL       │       │ Add as assistant msg  │
        │ Add results to msgs   │       │                       │
        └───────────────────────┘       └───────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Check for Final Answer                                            │
│ ──────────────────────────────                                            │
│ final_answer = utils.check_for_final_answer(response, repl_env)           │
│                                                                           │
│ Looking for:                                                              │
│ - FINAL(the answer is 42)                                                 │
│ - FINAL_VAR(my_result_variable)                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │ Final Answer Found    │       │ No Final Answer       │
        │ ──────────────────    │       │ ───────────────       │
        │ RETURN answer         │       │ CONTINUE to next      │
        │                       │       │ iteration             │
        └───────────────────────┘       └───────────────────────┘
```

**Key Design Decisions:**

1. **Iteration Limit**: Prevents infinite loops (default 20)
2. **Code Block Detection**: Uses regex to find ```` ```repl ```` blocks
3. **Message Accumulation**: Each response and execution result is added to messages
4. **Final Answer Detection**: Two formats supported:
   - `FINAL(direct answer)` - answer provided inline
   - `FINAL_VAR(variable_name)` - answer stored in REPL variable

---

### 4.4 `rlm/repl.py` - REPL Environment & Sub-LM

This file contains two key classes:

#### 4.4.1 Sub_RLM Class

```python
class Sub_RLM(RLM):
    """Recursive LLM client for REPL environment with fixed configuration."""
    
    def __init__(self, model: str = "gpt-5"):
        # Configuration - model can be specified
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.model = model

        # Initialize OpenAI client
        from rlm.utils.llm import OpenAIClient
        self.client = OpenAIClient(api_key=self.api_key, model=model)
        
    
    def completion(self, prompt) -> str:
        """
        Simple LM query for sub-LM call.
        """
        try:
            # Handle both string and dictionary/list inputs
            response = self.client.completion(
                messages=prompt,
                timeout=300
            )
            
            return response
                
        except Exception as e:
            error_msg = f"Error making LLM query: {str(e)}"
            return error_msg
    
    def cost_summary(self) -> dict[str, float]:
        raise NotImplementedError("Cost tracking is not implemented for the Sub-RLM.")
    
    def reset(self):
        raise NotImplementedError("Reset is not implemented for the Sub-RLM.")
```

**Purpose:** This is a simplified RLM that only makes single API calls. It's used by the `llm_query()` function inside the REPL environment.

**Key Points:**
- 300-second timeout for long operations
- Handles both string and message list inputs
- Error handling returns error message (doesn't crash)

**Why Not Use RLM_REPL for Sub-Calls?**

The paper discusses that you *could* use `RLM_REPL` for sub-calls to enable arbitrary recursion depth. However, this implementation uses `Sub_RLM` for simplicity:

```python
# Current implementation (depth=1):
self.sub_rlm: RLM = Sub_RLM(model=recursive_model)

# For infinite recursion (mentioned in paper):
# self.sub_rlm: RLM = RLM_REPL(model=recursive_model, depth=depth+1)
```

#### 4.4.2 REPLResult Dataclass

```python
@dataclass
class REPLResult:
    stdout: str
    stderr: str
    locals: dict
    execution_time: float

    def __init__(self, stdout: str, stderr: str, locals: dict, execution_time: float=None):
        self.stdout = stdout
        self.stderr = stderr
        self.locals = locals
        self.execution_time = execution_time
    
    def __str__(self):
        return f"REPLResult(stdout={self.stdout}, stderr={self.stderr}, locals={self.locals}, execution_time={self.execution_time})"
```

**Purpose:** Container for code execution results.

| Field | Type | Description |
|-------|------|-------------|
| `stdout` | str | Standard output from `print()` statements |
| `stderr` | str | Error messages if execution failed |
| `locals` | dict | All variables created during execution |
| `execution_time` | float | How long the code took to run |

#### 4.4.3 REPLEnv Class - The Sandboxed Environment

```python
class REPLEnv:
    def __init__(
        self,
        recursive_model: str = "gpt-5-mini",
        context_json: Optional[dict | list] = None,
        context_str: Optional[str] = None,
        setup_code: str = None,
    ):
```

**Constructor Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REPLEnv INITIALIZATION                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 1. Store original working directory                                       │
│    self.original_cwd = os.getcwd()                                        │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 2. Create temporary directory for isolation                               │
│    self.temp_dir = tempfile.mkdtemp(prefix="repl_env_")                   │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 3. Initialize Sub-RLM for llm_query() function                            │
│    self.sub_rlm = Sub_RLM(model=recursive_model)                          │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 4. Create sandboxed globals with safe built-ins                           │
│    self.globals = { '__builtins__': { ... safe functions ... } }          │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 5. Load context into environment                                          │
│    self.load_context(context_json, context_str)                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 6. Register special functions in globals                                  │
│    - llm_query(prompt) → calls sub-LM                                     │
│    - FINAL_VAR(var_name) → retrieves variable for final answer            │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 7. Run setup code if provided                                             │
│    if setup_code: self.code_execution(setup_code)                         │
└───────────────────────────────────────────────────────────────────────────┘
```

#### 4.4.4 Safe Built-ins (Security Sandbox)

The REPL environment restricts what Python functions are available:

```python
self.globals = {
    '__builtins__': {
        # ALLOWED - Safe functions
        'print': print, 'len': len, 'str': str, 'int': int, 'float': float,
        'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'bool': bool,
        'type': type, 'isinstance': isinstance, 'enumerate': enumerate,
        'zip': zip, 'map': map, 'filter': filter, 'sorted': sorted,
        'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round,
        # ... many more safe built-ins ...
        
        # ALLOWED - File access (needed for context loading)
        '__import__': __import__,
        'open': open,
        
        # BLOCKED - Dangerous functions
        'input': None,      # Block interactive input
        'eval': None,       # Block dynamic code evaluation
        'exec': None,       # Block dynamic code execution
        'compile': None,    # Block code compilation
        'globals': None,    # Block access to global namespace
        'locals': None,     # Block access to local namespace
    }
}
```

**Security Considerations:**

| Allowed | Reason |
|---------|--------|
| `open`, `__import__` | Needed to read context files and import libraries |
| `print` | Required for REPL output |
| Math/string functions | Safe and useful for data processing |

| Blocked | Reason |
|---------|--------|
| `eval`, `exec` | Could execute arbitrary code outside sandbox |
| `input` | Would hang waiting for user input |
| `globals`, `locals` | Could access internal state |

#### 4.4.5 The llm_query Function

```python
def llm_query(prompt: str) -> str:
    """Query the LLM with the given prompt."""
    return self.sub_rlm.completion(prompt)

# Add (R)LM query function to globals
self.globals['llm_query'] = llm_query
```

**This is the key function that enables recursion!**

When code inside the REPL calls `llm_query("What is the magic number in: " + chunk)`:
1. The `Sub_RLM.completion()` method is called
2. That makes an API call to the LLM
3. The response is returned as a string
4. The REPL code can use that response

**Example Usage in REPL:**

```python
# Inside REPL, the LM might write:
chunks = [context[i:i+100000] for i in range(0, len(context), 100000)]
results = []
for chunk in chunks:
    result = llm_query(f"Find the magic number in this text: {chunk}")
    results.append(result)
final_answer = llm_query(f"Combine these results: {results}")
```

#### 4.4.6 Code Execution Method

```python
def code_execution(self, code) -> REPLResult:
    """
    Simple code execution "notebook-style" in a REPL environment.
    """
    start_time = time.time()
    with self._capture_output() as (stdout_buffer, stderr_buffer):
        with self._temp_working_directory():
            try:
                # Split code into import statements and other code
                lines = code.split('\n')
                import_lines = []
                other_lines = []
                
                for line in lines:
                    if line.startswith(('import ', 'from ')) and not line.startswith('#'):
                        import_lines.append(line)
                    else:
                        other_lines.append(line)
                
                # Execute imports first in globals to make them available
                if import_lines:
                    import_code = '\n'.join(import_lines)
                    exec(import_code, self.globals, self.globals)
                
                # Execute the rest of the code
                if other_lines:
                    other_code = '\n'.join(other_lines)
                    combined_namespace = {**self.globals, **self.locals}
                    # ... expression handling logic ...
                    exec(other_code, combined_namespace, combined_namespace)
                    
                    # Update locals with any new variables created
                    for key, value in combined_namespace.items():
                        if key not in self.globals:
                            self.locals[key] = value
```

**Execution Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CODE EXECUTION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
            Input: "import re\nx = re.findall(r'\d+', context)\nprint(x)"
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 1. CAPTURE OUTPUT                                                         │
│    Redirect stdout/stderr to buffers                                      │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 2. CHANGE TO TEMP DIRECTORY                                               │
│    Isolate file operations                                                │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 3. SEPARATE IMPORTS                                                       │
│    import_lines = ["import re"]                                           │
│    other_lines = ["x = re.findall(r'\\d+', context)", "print(x)"]         │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 4. EXECUTE IMPORTS IN GLOBALS                                             │
│    exec("import re", globals, globals)                                    │
│    → 're' module now available                                            │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 5. EXECUTE OTHER CODE                                                     │
│    combined = {**globals, **locals}                                       │
│    exec(other_code, combined, combined)                                   │
│    → 'x' variable created                                                 │
│    → print() output captured                                              │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 6. UPDATE LOCALS                                                          │
│    self.locals['x'] = [...]  # Store new variable                         │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 7. RETURN RESULT                                                          │
│    REPLResult(stdout="[...]", stderr="", locals={'x': [...]}, time=0.01)  │
└───────────────────────────────────────────────────────────────────────────┘
```

**Why Separate Imports?**

Imports need to be added to `globals` so they're available across multiple code executions. Other variables go into `locals` to track the REPL state.

---

### 4.5 `rlm/utils/llm.py` - OpenAI Client Wrapper

```python
"""
OpenAI Client wrapper specifically for GPT-5 models.
"""

import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

        # Implement cost tracking logic here.
    
    def completion(
        self,
        messages: list[dict[str, str]] | str,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        try:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                messages = [messages]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"Error generating completion: {str(e)}")
```

**Features:**

1. **Flexible Input Handling**: Accepts strings, single dicts, or message lists
2. **Environment Variable Fallback**: Uses `OPENAI_API_KEY` if not provided
3. **Cost Tracking Placeholder**: Comment indicates where to add billing logic
4. **Error Wrapping**: Converts exceptions to RuntimeError with context

---

### 4.6 `rlm/utils/prompts.py` - Prompt Engineering

This file contains the carefully crafted prompts that make RLM work.

#### 4.6.1 System Prompt

```python
REPL_SYSTEM_PROMPT = """You are tasked with answering a query with associated context. You can access, transform, and analyze this context interactively in a REPL environment that can recursively query sub-LLMs, which you are strongly encouraged to use as much as possible. You will be queried iteratively until you provide a final answer.

The REPL environment is initialized with:
1. A `context` variable that contains extremely important information about your query. You should check the content of the `context` variable to understand what you are working with. Make sure you look through it sufficiently as you answer your query.
2. A `llm_query` function that allows you to query an LLM (that can handle around 500K chars) inside your REPL environment.
3. The ability to use `print()` statements to view the output of your REPL code and continue your reasoning.

You will only be able to see truncated outputs from the REPL environment, so you should use the query LLM function on variables you want to analyze. You will find this function especially useful when you have to analyze the semantics of the context. Use these variables as buffers to build up your final answer.
Make sure to explicitly look through the entire context in REPL before answering your query. An example strategy is to first look at the context and figure out a chunking strategy, then break up the context into smart chunks, and query an LLM per chunk with a particular question and save the answers to a buffer, then query an LLM with all the buffers to produce your final answer.

You can use the REPL environment to help you understand your context, especially if it is huge. Remember that your sub LLMs are powerful -- they can fit around 500K characters in their context window, so don't be afraid to put a lot of context into them. For example, a viable strategy is to feed 10 documents per sub-LLM query. Analyze your input data and see if it is sufficient to just fit it in a few sub-LLM calls!

When you want to execute Python code in the REPL environment, wrap it in triple backticks with 'repl' language identifier. For example:
```repl
chunk = context[:10000]
answer = llm_query(f"What is the magic number in the context? Here is the chunk: {chunk}")
print(answer)
```

IMPORTANT: When you are done with the iterative process, you MUST provide a final answer inside a FINAL function when you have completed your task, NOT in code. Do not use these tags unless you have completed your task. You have two options:
1. Use FINAL(your final answer here) to provide the answer directly
2. Use FINAL_VAR(variable_name) to return a variable you have created in the REPL environment as your final output
"""
```

**Prompt Engineering Breakdown:**

| Section | Purpose |
|---------|---------|
| Role definition | "You are tasked with answering a query..." - sets context |
| Available tools | Lists `context`, `llm_query()`, `print()` |
| Strategy guidance | Suggests chunking → sub-LM queries → aggregation |
| Code format | Shows ```` ```repl ```` syntax |
| Termination | Explains `FINAL()` and `FINAL_VAR()` syntax |

#### 4.6.2 Iteration Prompts

```python
USER_PROMPT = """Think step-by-step on what to do using the REPL environment (which contains the context) to answer the original query: \"{query}\".\n\nContinue using the REPL environment, which has the `context` variable, and querying sub-LLMs by writing to ```repl``` tags, and determine your answer. Your next action:""" 

def next_action_prompt(query: str, iteration: int = 0, final_answer: bool = False) -> Dict[str, str]:
    if final_answer:
        return {"role": "user", "content": "Based on all the information you have, provide a final answer to the user's query."}
    if iteration == 0:
        safeguard = "You have not interacted with the REPL environment or seen your context yet. Your next action should be to look through, don't just provide a final answer yet.\n\n"
        return {"role": "user", "content": safeguard + USER_PROMPT.format(query=query)}
    else:
        return {"role": "user", "content": "The history before is your previous interactions with the REPL environment. " + USER_PROMPT.format(query=query)}
```

**Iteration Logic:**

| Iteration | Prompt Behavior |
|-----------|-----------------|
| 0 (first) | Adds safeguard: "You haven't seen the context yet, look through it first" |
| 1+ | Reminds: "The history before is your previous interactions..." |
| Final | "Based on all information, provide a final answer" |

---

### 4.7 `rlm/utils/utils.py` - Utility Functions

#### 4.7.1 Code Block Detection

```python
def find_code_blocks(text: str) -> List[str]:
    """
    Find REPL code blocks in text wrapped in triple backticks and return List of content(s).
    Returns None if no code blocks are found.
    """
    pattern = r'```repl\s*\n(.*?)\n```'
    results = []
    
    for match in re.finditer(pattern, text, re.DOTALL):
        code_content = match.group(1).strip()
        results.append(code_content)
    
    return results
```

**Regex Breakdown:**

```
```repl     - Literal "```repl"
\s*\n       - Optional whitespace, then newline
(.*?)       - Capture group: any content (non-greedy)
\n```       - Newline, then closing "```"
```

**Example Match:**

```
Input: "Let me write some code:\n```repl\nprint('hello')\n```\nDone!"
Output: ["print('hello')"]
```

#### 4.7.2 Final Answer Detection

```python
def find_final_answer(text: str) -> Optional[Tuple[str, str]]:
    """
    Find FINAL(...) or FINAL_VAR(...) statement in response and return (type, content).
    Returns None if neither pattern is found.
    """
    # Check for FINAL_VAR pattern first - must be at start of line
    final_var_pattern = r'^\s*FINAL_VAR\((.*?)\)'
    match = re.search(final_var_pattern, text, re.MULTILINE | re.DOTALL)
    if match:
        return ('FINAL_VAR', match.group(1).strip())
    
    # Check for FINAL pattern - must be at start of line
    final_pattern = r'^\s*FINAL\((.*?)\)'
    match = re.search(final_pattern, text, re.MULTILINE | re.DOTALL)
    if match:
        return ('FINAL', match.group(1).strip())
    
    return None
```

**Pattern Priority:**

1. Check `FINAL_VAR(...)` first (variable reference)
2. Then check `FINAL(...)` (direct answer)
3. Return `None` if neither found

#### 4.7.3 Code Execution Processing

```python
def process_code_execution(
    response: str,
    messages: List[Dict[str, str]],
    repl_env,
    repl_env_logger,
    logger,
) -> List[Dict[str, str]]:
    """
    Process code execution from the model response.
    """
    code_blocks = find_code_blocks(response)
    
    if code_blocks:
        for code in code_blocks:
            execution_result = execute_code(repl_env, code, repl_env_logger, logger)
            messages = add_execution_result_to_messages(
                messages, code, execution_result, 
            )
    
    return messages
```

**Flow:**

1. Extract code blocks from response
2. Execute each block in REPL
3. Add results to conversation messages
4. Return updated messages

#### 4.7.4 Context Conversion

```python
def convert_context_for_repl(context):
    """
    Convert REPL context to either some 
    """
    if isinstance(context, dict):
        context_data = context
        context_str = None
    elif isinstance(context, str):
        context_data = None
        context_str = context
    elif isinstance(context, list):
        if len(context) > 0 and isinstance(context[0], dict):
            if "content" in context[0]:
                context_data = [msg.get("content", "") for msg in context]
            else:
                context_data = context
            context_str = None
        else:
            context_data = context
            context_str = None
    else:
        context_data = context
        context_str = None
    
    return context_data, context_str
```

**Input → Output Mapping:**

| Input Type | context_data | context_str |
|------------|--------------|-------------|
| `str` | `None` | The string |
| `dict` | The dict | `None` |
| `list[dict]` with "content" | Extracted contents | `None` |
| `list[dict]` without "content" | The list | `None` |
| `list[other]` | The list | `None` |

---

### 4.8 Logger Files

#### 4.8.1 `rlm/logger/root_logger.py` - ColorfulLogger

Provides ANSI-colored console output for the Root LM's activities:

```python
class ColorfulLogger:
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        # ...
    }
```

**Methods:**

| Method | Purpose |
|--------|---------|
| `log_query_start(query)` | Logs the beginning of a new query |
| `log_initial_messages(messages)` | Shows the system prompt setup |
| `log_model_response(response, has_tool_calls)` | Shows each LM response |
| `log_tool_execution(tool_call, result)` | Shows code execution |
| `log_final_response(response)` | Shows the final answer |

#### 4.8.2 `rlm/logger/repl_logger.py` - REPLEnvLogger

Uses the `rich` library for Jupyter-notebook-style output:

```python
class REPLEnvLogger:
    def __init__(self, max_output_length: int = 2000, enabled: bool = True):
        self.console = Console()  # Rich console
        self.executions: List[CodeExecution] = []
```

**Features:**

- Syntax-highlighted code blocks
- Colored panels for input/output
- Error highlighting
- Execution timing display
- Truncation for long outputs

---

### 4.9 `main.py` - Example Usage

```python
from rlm.rlm_repl import RLM_REPL
import random

def generate_massive_context(num_lines: int = 1_000_000, answer: str = "1298418") -> str:
    print("Generating massive context with 1M lines...")
    
    random_words = ["blah", "random", "text", "data", "content", "information", "sample"]
    
    lines = []
    for _ in range(num_lines):
        num_words = random.randint(3, 8)
        line_words = [random.choice(random_words) for _ in range(num_words)]
        lines.append(" ".join(line_words))
    
    # Insert the magic number at a random position
    magic_position = random.randint(400000, 600000)
    lines[magic_position] = f"The magic number is {answer}"
    
    print(f"Magic number inserted at position {magic_position}")
    
    return "\n".join(lines)

def main():
    print("Example of using RLM (REPL) with GPT-5-nano on a needle-in-haystack problem.")
    answer = str(random.randint(1000000, 9999999))
    context = generate_massive_context(num_lines=1_000_000, answer=answer)

    rlm = RLM_REPL(
        model="gpt-5-nano",
        recursive_model="gpt-5",
        enable_logging=True,
        max_iterations=10
    )
    query = "I'm looking for a magic number. What is it?"
    result = rlm.completion(context=context, query=query)
    print(f"Result: {result}. Expected: {answer}")

if __name__ == "__main__":
    main()
```

**This demonstrates the classic "needle in a haystack" problem:**

1. Generate 1 million lines of random text
2. Hide a magic number somewhere in the middle
3. Ask the RLM to find it

**Why This Works:**

A normal LLM couldn't process 1M lines. RLM:
1. Chunks the text
2. Uses sub-LMs to search each chunk
3. Aggregates results to find the needle

---

## 5. Data Flow & Execution

### 5.1 Complete Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ USER: "Find the magic number in this 1M line text file"                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ RLM_REPL.completion(context="<1M lines>", query="Find magic number")        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SETUP PHASE                                                                 │
│ ───────────                                                                 │
│ 1. Build system prompt (REPL_SYSTEM_PROMPT)                                 │
│ 2. Convert context to string                                                │
│ 3. Create REPLEnv with:                                                     │
│    - context saved to temp file                                             │
│    - 'context' variable loaded                                              │
│    - llm_query() function registered                                        │
│    - FINAL_VAR() function registered                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ITERATION 1                                                                 │
│ ───────────                                                                 │
│ Prompt: "You haven't seen context yet. Your next action:"                   │
│                                                                             │
│ ROOT LM Response:                                                           │
│ "Let me first check the size of the context...                              │
│ ```repl                                                                     │
│ print(f'Context length: {len(context)} characters')                         │
│ print(context[:500])  # First 500 chars                                     │
│ ```"                                                                        │
│                                                                             │
│ REPL Output: "Context length: 15000000 characters\nblah random text..."     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ITERATION 2                                                                 │
│ ───────────                                                                 │
│ Prompt: "Previous interactions... Your next action:"                        │
│                                                                             │
│ ROOT LM Response:                                                           │
│ "The context is huge. Let me chunk it and search with sub-LMs...            │
│ ```repl                                                                     │
│ chunk_size = 500000                                                         │
│ chunks = [context[i:i+chunk_size] for i in range(0, len(context), chunk_size)]
│ print(f'Created {len(chunks)} chunks')                                      │
│ ```"                                                                        │
│                                                                             │
│ REPL Output: "Created 30 chunks"                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ITERATION 3                                                                 │
│ ───────────                                                                 │
│ ROOT LM Response:                                                           │
│ "Now I'll search each chunk for the magic number...                         │
│ ```repl                                                                     │
│ results = []                                                                │
│ for i, chunk in enumerate(chunks):                                          │
│     result = llm_query(f'Find the magic number in this text. If found,      │
│                         return ONLY the number. Text: {chunk}')             │
│     results.append(f'Chunk {i}: {result}')                                  │
│     print(f'Processed chunk {i}')                                           │
│ ```"                                                                        │
│                                                                             │
│ [Sub-LM calls happen here - one per chunk]                                  │
│                                                                             │
│ REPL Output: "Processed chunk 0\nProcessed chunk 1\n..."                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ITERATION 4                                                                 │
│ ───────────                                                                 │
│ ROOT LM Response:                                                           │
│ "Let me check the results...                                                │
│ ```repl                                                                     │
│ for r in results:                                                           │
│     if 'magic' in r.lower() or any(c.isdigit() for c in r):                 │
│         print(r)                                                            │
│ ```"                                                                        │
│                                                                             │
│ REPL Output: "Chunk 15: The magic number is 7384921"                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ITERATION 5 (FINAL)                                                         │
│ ───────────────────                                                         │
│ ROOT LM Response:                                                           │
│ "I found the magic number in chunk 15.                                      │
│                                                                             │
│ FINAL(7384921)"                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ RETURN: "7384921"                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Message Accumulation

The `messages` list grows with each iteration:

```python
messages = [
    # Initial setup
    {"role": "system", "content": REPL_SYSTEM_PROMPT},
    
    # Iteration 1
    {"role": "user", "content": "You haven't seen context yet..."},
    {"role": "user", "content": "Code executed:\n```python\nprint(len(context))\n```\n\nREPL output:\n15000000"},
    
    # Iteration 2
    {"role": "user", "content": "Previous interactions... Your next action:"},
    {"role": "user", "content": "Code executed:\n```python\nchunks = ...\n```\n\nREPL output:\nCreated 30 chunks"},
    
    # ... continues growing ...
]
```

---

## 6. Key Algorithms & Patterns

### 6.1 The Chunking Pattern

```python
# Common pattern the LM learns to use:
chunk_size = 500000  # ~500K chars, within sub-LM context limit
chunks = [context[i:i+chunk_size] for i in range(0, len(context), chunk_size)]

results = []
for chunk in chunks:
    result = llm_query(f"<task description>: {chunk}")
    results.append(result)

final = llm_query(f"Combine these results: {results}")
```

### 6.2 The Map-Reduce Pattern

```python
# Map phase: process each chunk independently
mapped = []
for chunk in chunks:
    mapped.append(llm_query(f"Extract key info from: {chunk}"))

# Reduce phase: combine results
reduced = llm_query(f"Synthesize these findings: {mapped}")
```

### 6.3 The Iterative Refinement Pattern

```python
# Initial analysis
preliminary = llm_query(f"Initial analysis of: {context[:100000]}")

# Targeted follow-up
if "need more info" in preliminary:
    detailed = llm_query(f"Deep dive into: {context[100000:200000]}")
    
# Final synthesis
final = llm_query(f"Combine: {preliminary} and {detailed}")
```

---

## 7. Practical Usage Examples

### 7.1 Basic Usage

```python
from rlm.rlm_repl import RLM_REPL

# Initialize RLM
rlm = RLM_REPL(
    model="gpt-5",           # Root LM (orchestrator)
    recursive_model="gpt-5", # Sub-LM (chunk processor)
    max_iterations=20,       # Safety limit
    enable_logging=True      # See what's happening
)

# Process a query
result = rlm.completion(
    context="<your large context here>",
    query="What are the key themes in this document?"
)
print(result)
```

### 7.2 Processing Large Documents

```python
# Load a large document
with open("massive_document.txt", "r") as f:
    content = f.read()

rlm = RLM_REPL(model="gpt-5", recursive_model="gpt-5")
summary = rlm.completion(
    context=content,
    query="Provide a comprehensive summary with key insights"
)
```

### 7.3 Structured Data Analysis

```python
# JSON/dict context
data = {
    "users": [...],  # 10,000 users
    "transactions": [...],  # 1M transactions
    "products": [...]  # 50,000 products
}

rlm = RLM_REPL(model="gpt-5", recursive_model="gpt-5")
analysis = rlm.completion(
    context=data,
    query="Which products have the highest customer satisfaction based on transaction patterns?"
)
```

### 7.4 Code Analysis

```python
# Analyze a codebase
import os

def read_codebase(directory):
    files = {}
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):
                path = os.path.join(root, filename)
                with open(path, 'r') as f:
                    files[path] = f.read()
    return files

codebase = read_codebase("./my_project")

rlm = RLM_REPL(model="gpt-5", recursive_model="gpt-5")
review = rlm.completion(
    context=codebase,
    query="Find potential security vulnerabilities and suggest fixes"
)
```

---

## Summary

The RLM architecture enables LLMs to:

1. **Process unlimited context** through intelligent chunking
2. **Maintain state** across multiple reasoning steps via REPL variables
3. **Execute code dynamically** to transform and analyze data
4. **Coordinate hierarchically** between root and sub-LMs
5. **Iterate until solved** rather than making single-pass attempts

The key insight from the paper is that **LLMs can be their own orchestrators** - they don't need external agents to manage complex multi-step tasks. By giving them a REPL environment and recursive sub-LM access, they can autonomously decide how to chunk, process, and synthesize information.

This implementation provides a minimal but functional version of the RLM concept, suitable for experimentation and extension.

---

## References

- [Original RLM Blogpost by Alex Zhang](https://alexzhang13.github.io/blog/2025/rlm/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Python `exec` and `eval` Documentation](https://docs.python.org/3/library/functions.html#exec)
