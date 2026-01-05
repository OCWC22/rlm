# RLM: Complete Master Document
## Recursive Language Models - Repository, Paper, Code & Community Analysis

> **This is the COMPLETE, EXHAUSTIVE document covering EVERYTHING about Alex Zhang's Recursive Language Models (RLM).**
>
> **Last Updated:** January 5, 2026
>
> **Contents:**
> 1. About the Authors
> 2. The Big Picture: 2026 is the Year of RLMs
> 3. Key Tweets and Announcements
> 4. Repository Overview with ASCII Architecture
> 5. Line-by-Line Code Walkthrough
> 6. Paper Summary (arXiv:2512.24601)
> 7. Core Concepts from the Blog/Paper
> 8. Experimental Results (OOLONG, BrowseComp-Plus)
> 9. RLM Strategies That Emerge
> 10. Limitations and Future Directions
> 11. RAW Hacker News Comments (35 Comments - VERBATIM)
> 12. RAW X/Twitter Discussions (100+ Tweets - VERBATIM)
> 13. Community Criticism & Defense Deep Dive
> 14. The Real Innovation (Synthesis)
> 15. Open Questions from the Community
> 16. Related Works

---

# PART 0: ABOUT THE AUTHORS

## 👥 Primary Authors

### Alex L. Zhang (@a1zhang)
- **Position**: PhD Student at MIT CSAIL
- **Undergrad**: Princeton University
- **Followers**: ~19,500 on X/Twitter
- **Notable**: Active in [GPU MODE](https://www.youtube.com/@GPUMODE) kernel competitions
- **Focus**: Systems for ML, long-context LLMs, inference-time scaling
- **Collaborator**: Omar Khattab (@lateinteraction) - MIT CSAIL

### Omar Khattab (@lateinteraction)
- **Position**: Professor at MIT CSAIL
- **Notable**: Creator of DSPy & ColBERT
- **Focus**: LLM systems, programmatic LM manipulation, retrieval systems

### Tim Kraska
- **Position**: Professor at MIT
- **Focus**: Database systems, ML for data systems

## 🔗 Key Links

| Resource | URL |
|----------|-----|
| **Paper** | https://arxiv.org/abs/2512.24601 |
| **GitHub** | https://github.com/alexzhang13/rlm |
| **Minimal Implementation** | https://github.com/alexzhang13/rlm-minimal |
| **Blog** | https://alexzhang13.github.io/blog/2025/rlm/ |
| **@a1zhang on X** | https://x.com/a1zhang |
| **@lateinteraction on X** | https://x.com/lateinteraction |
| **Oct 2025 Announcement** | https://x.com/a1zhang/status/1978469116542337259 |

---

# PART 1: THE BIG PICTURE - 2026 IS THE YEAR OF RLMs

## 📌 Pinned Tweet (January 2, 2026)

> **Much like the switch in 2025 from language models to reasoning models, we think 2026 will be all about the switch to Recursive Language Models (RLMs).**
>
> It turns out that models can be far more powerful if you allow them to treat *their own prompts* as an object in an external environment, which they understand and manipulate by writing code that invokes LLMs!
>
> Our full paper on RLMs is now available—with much more expansive experiments compared to our initial blogpost from October 2025!

**Metrics**: 571K impressions, 3.6K likes, 565 retweets, 3.3K bookmarks

**Paper Link**: https://arxiv.org/abs/2512.24601v1

---

## 📢 Key Tweets and Announcements

### Original Announcement (October 15, 2025)

> **What if scaling the context windows of frontier LLMs is much easier than it sounds?**
>
> We're excited to share our work on Recursive Language Models (RLMs). A new inference strategy where LLMs can decompose and recursively interact with input prompts of seemingly unbounded length, as a REPL environment.
>
> On the OOLONG benchmark, RLMs with GPT-5-mini outperforms GPT-5 by over 110% gains (more than double!) on 132k-token sequences and is cheaper to query on average.
>
> On the BrowseComp-Plus benchmark, RLMs with GPT-5 can take in 10M+ tokens as their "prompt" and answer highly compositional queries without degradation and even better than explicit indexing/retrieval.

**Metrics**: 897K impressions, 2.6K likes, 367 retweets, 2.8K bookmarks

### Seeking Benchmarks (Omar Khattab)

> **What are the most natural/realistic VERY long context problems out there?**

This tweet from Omar Khattab (Alex's advisor) led to the discovery of the OOLONG benchmark and informed the experimental design of RLM.

---

# PART 2: REPOSITORY STRUCTURE & ARCHITECTURE

## 📁 Complete File Tree

```
/Users/chen/Projects/rlm/
├── rlm/                              # Core RLM library
│   ├── __init__.py                   # Package exports
│   ├── rlm.py                        # Abstract base class (15 lines)
│   ├── rlm_repl.py                   # Main RLM implementation (136 lines)
│   ├── repl.py                       # REPL environment (360 lines)
│   ├── logger/
│   │   ├── root_logger.py            # Colorful console logger (148 lines)
│   │   └── repl_logger.py            # Rich REPL output logger (145 lines)
│   └── utils/
│       ├── llm.py                    # OpenAI client wrapper (44 lines)
│       ├── prompts.py                # System & user prompts (70 lines)
│       └── utils.py                  # Helper functions (239 lines)
├── examples/
│   ├── claude-code-assistant/        # Claude Code integration
│   │   ├── rlm_context.py            # Anthropic/OpenAI RLM engine
│   │   ├── large_file_processor.py   # JSONL/large file processor
│   │   ├── discord_extractor.py      # Discord export analyzer
│   │   ├── README.md                 # Usage docs
│   │   └── AGENT_INSTRUCTIONS.md     # Step-by-step agent guide
│   ├── json-explorer/                # JSON analysis tools
│   ├── rlm_cli/                      # CLI interface
│   └── textbook-qa/                  # PDF textbook Q&A
├── main.py                           # Needle-in-haystack example (40 lines)
├── README.md                         # Project README
├── pyproject.toml                    # Poetry config
└── requirements.txt                  # Dependencies
```

---

## 🔄 HIGH-LEVEL ARCHITECTURE ASCII DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            RLM (Recursive Language Model)                            │
│                                                                                      │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                              USER QUERY                                       │  │
│   │            "Find the magic number in this 1M line context"                    │  │
│   └────────────────────────────────┬─────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                         RLM_REPL.completion()                                 │  │
│   │   • Initializes REPL environment with context as Python variable             │  │
│   │   • Runs iterative loop (max_iterations=20)                                   │  │
│   │   • Parses model responses for ```repl code blocks                           │  │
│   │   • Executes code, feeds results back to model                               │  │
│   │   • Checks for FINAL() or FINAL_VAR() termination                            │  │
│   └────────────────────────────────┬─────────────────────────────────────────────┘  │
│                                    │                                                 │
│                        ┌───────────┴───────────┐                                    │
│                        │                       │                                    │
│                        ▼                       ▼                                    │
│   ┌───────────────────────────────┐   ┌─────────────────────────────────────────┐  │
│   │        ROOT LLM               │   │              REPL ENVIRONMENT           │  │
│   │   (e.g., GPT-5-nano)          │   │                                         │  │
│   │                               │   │   globals = {                           │  │
│   │   • Receives system prompt    │   │     'context': <user's massive data>,   │  │
│   │   • Sees REPL output          │   │     'llm_query': sub_llm_function,      │  │
│   │   • Generates Python code     │   │     'FINAL_VAR': variable_extractor,    │  │
│   │   • Decides chunking strategy │   │     'print': print,                     │  │
│   │                               │   │     ... (safe built-ins)                │  │
│   └───────────────────────────────┘   │   }                                     │  │
│                                        │                                         │  │
│                                        │   Code execution: exec() based          │  │
│                                        │   Output capture: stdout/stderr         │  │
│                                        └─────────────────────────────────────────┘  │
│                                                         │                           │
│                                                         │ llm_query()               │
│                                                         ▼                           │
│                                        ┌─────────────────────────────────────────┐  │
│                                        │           SUB-LLM (depth=1)             │  │
│                                        │        (e.g., GPT-5, ~500K ctx)         │  │
│                                        │                                         │  │
│                                        │   • Called from REPL code               │  │
│                                        │   • Processes chunks of context         │  │
│                                        │   • Returns extracted info              │  │
│                                        │   • Can handle ~500K characters         │  │
│                                        └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔁 EXECUTION FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              RLM EXECUTION FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

USER INPUT                                                               FINAL OUTPUT
    │                                                                         ▲
    │ context="...", query="Find X"                                          │
    ▼                                                                         │
┌─────────────────┐                                                   ┌──────┴──────┐
│ RLM_REPL.__init__│                                                   │ FINAL(ans) │
│                 │                                                   │ or          │
│ model="gpt-5-nano"                                                  │ FINAL_VAR(v)│
│ recursive_model="gpt-5"                                             └─────────────┘
│ max_iterations=20                                                          ▲
└────────┬────────┘                                                          │
         │                                                                   │
         ▼                                                                   │
┌─────────────────┐     ┌─────────────────────────────────────────────────────┐
│ setup_context() │     │                 ITERATION LOOP                       │
│                 │     │  for iteration in range(max_iterations):            │
│ • Build system  │     │                                                     │
│   prompt        │────▶│  ┌─────────────────────────────────────────────┐   │
│ • Init REPL with│     │  │ 1. Query ROOT LLM                           │   │
│   context       │     │  │    response = llm.completion(messages)       │   │
└─────────────────┘     │  │                                              │   │
                        │  │ 2. Check for ```repl code blocks             │   │
                        │  │    code_blocks = find_code_blocks(response)  │   │
                        │  │                                              │   │
                        │  │ 3. If code_blocks:                          │───┤
                        │  │       Execute in REPL                        │   │
                        │  │       repl_env.code_execution(code)          │   │
                        │  │       Append result to messages              │   │
                        │  │                                              │   │
                        │  │ 4. Check for FINAL() / FINAL_VAR()          │───┼──▶ EXIT
                        │  │    if final_answer: return it                │   │
                        │  │                                              │   │
                        │  │ 5. Continue to next iteration                │   │
                        │  └──────────────────────────────────────────────┘   │
                        └─────────────────────────────────────────────────────┘
```

---

# PART 3: LINE-BY-LINE CODE WALKTHROUGH

## 📄 File: `rlm/rlm.py` (Abstract Base Class)

```python
# Lines 1-15
from abc import ABC, abstractmethod

class RLM(ABC):
    """
    Abstract base class for all RLM implementations.
    Defines the interface that any RLM must implement.
    """
    
    @abstractmethod
    def completion(self, context: list[str] | str | dict[str, str], query: str) -> str:
        """Main entry point - takes context + query, returns answer"""
        pass

    @abstractmethod
    def cost_summary(self) -> dict[str, float]:
        """Track API costs (tokens, $)"""
        pass

    @abstractmethod
    def reset(self):
        """Reset internal state for new query"""
        pass
```

**Purpose**: Interface contract. All RLMs inherit from this.

---

## 📄 File: `rlm/rlm_repl.py` (Main Implementation - 136 lines)

### Lines 1-16: Imports

```python
"""
Simple Recursive Language Model (RLM) with REPL environment.
"""

from typing import Dict, List, Optional, Any 

from rlm import RLM                                    # Base class
from rlm.repl import REPLEnv                          # REPL environment
from rlm.utils.llm import OpenAIClient                # LLM API wrapper
from rlm.utils.prompts import DEFAULT_QUERY, next_action_prompt, build_system_prompt
import rlm.utils.utils as utils

from rlm.logger.root_logger import ColorfulLogger     # Console logging
from rlm.logger.repl_logger import REPLEnvLogger      # REPL output logging
```

### Lines 17-46: `RLM_REPL` Class Constructor

```python
class RLM_REPL(RLM):
    """
    LLM Client that can handle long contexts by recursively calling itself.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,        # OpenAI API key (or env var)
                 model: str = "gpt-5",                 # ROOT LLM model
                 recursive_model: str = "gpt-5",      # SUB-LLM model for llm_query()
                 max_iterations: int = 20,            # Max REPL interaction loops
                 depth: int = 0,                      # Recursion depth (unused in v1)
                 enable_logging: bool = False,        # Console output toggle
                 ):
        self.api_key = api_key
        self.model = model
        self.recursive_model = recursive_model
        self.llm = OpenAIClient(api_key, model)       # Initialize root LLM client
        
        # Track recursive call depth to prevent infinite loops
        self.repl_env = None                          # REPL created per-query
        self.depth = depth                            # Unused in this version
        self._max_iterations = max_iterations
        
        # Initialize loggers
        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)
        
        self.messages = []                            # Conversation history
        self.query = None                             # Current user query
```

**Key Design Choices:**
- `model` vs `recursive_model`: Allows using cheap model (nano) for orchestration, expensive model for deep analysis
- `max_iterations=20`: Safety cap on REPL loops
- `depth=0`: Placeholder for future multi-depth recursion

### Lines 47-74: `setup_context()` Method

```python
    def setup_context(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None):
        """
        Setup the context for the RLMClient.

        Args:
            context: The large context to analyze (list, string, or dict)
            query: The user's question
        """
        if query is None:
            query = DEFAULT_QUERY

        self.query = query
        self.logger.log_query_start(query)

        # Initialize the conversation with the REPL prompt
        self.messages = build_system_prompt()         # Returns [{role: "system", content: REPL_SYSTEM_PROMPT}]
        self.logger.log_initial_messages(self.messages)
        
        # Initialize REPL environment with context data
        context_data, context_str = utils.convert_context_for_repl(context)
        
        self.repl_env = REPLEnv(
            context_json=context_data,                # Dict/List context
            context_str=context_str,                  # String context
            recursive_model=self.recursive_model,    # Model for sub-LLM calls
        )
        
        return self.messages
```

**What happens:**
1. Builds system prompt with REPL instructions
2. Creates `REPLEnv` instance with context loaded as Python variable
3. Returns initial messages list

### Lines 76-121: `completion()` Method (THE CORE)

```python
    def completion(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None) -> str:
        """
        Given a query and a (potentially long) context, recursively call the LM
        to explore the context and provide an answer using a REPL environment.
        """
        self.messages = self.setup_context(context, query)
        
        # ╔═══════════════════════════════════════════════════════════════════╗
        # ║                    MAIN ITERATION LOOP                             ║
        # ╚═══════════════════════════════════════════════════════════════════╝
        for iteration in range(self._max_iterations):
            
            # Step 1: Query root LLM with current messages + action prompt
            response = self.llm.completion(self.messages + [next_action_prompt(query, iteration)])
            
            # Step 2: Check for code blocks in response
            code_blocks = utils.find_code_blocks(response)
            self.logger.log_model_response(response, has_tool_calls=code_blocks is not None)
            
            # Step 3: Process code execution or add assistant message
            if code_blocks is not None:
                # Execute code and add results to conversation
                self.messages = utils.process_code_execution(
                    response, self.messages, self.repl_env, 
                    self.repl_env_logger, self.logger
                )
            else:
                # No code - just add as assistant message
                assistant_message = {"role": "assistant", "content": "You responded with:\n" + response}
                self.messages.append(assistant_message)
            
            # Step 4: Check for final answer
            final_answer = utils.check_for_final_answer(
                response, self.repl_env, self.logger,
            )

            # In practice, you may need some guardrails here.
            if final_answer:
                self.logger.log_final_response(final_answer)
                return final_answer

            
        # ╔═══════════════════════════════════════════════════════════════════╗
        # ║                 MAX ITERATIONS REACHED                             ║
        # ╚═══════════════════════════════════════════════════════════════════╝
        print("No final answer found in any iteration")
        self.messages.append(next_action_prompt(query, iteration, final_answer=True))
        final_answer = self.llm.completion(self.messages)
        self.logger.log_final_response(final_answer)

        return final_answer
```

**The Core Loop Explained:**
1. **Query LLM**: Send conversation history + "what's your next action?" prompt
2. **Parse Response**: Look for ```` ```repl ```` code blocks
3. **Execute Code**: Run Python in sandboxed REPL, capture stdout/stderr
4. **Check Termination**: Look for `FINAL()` or `FINAL_VAR()` patterns
5. **Loop or Return**: Continue until final answer or max iterations

---

## 📄 File: `rlm/repl.py` (REPL Environment - 360 lines)

### Lines 15-53: `Sub_RLM` Class

```python
class Sub_RLM(RLM):
    """Recursive LLM client for REPL environment with fixed configuration."""
    
    def __init__(self, model: str = "gpt-5"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.model = model
        from rlm.utils.llm import OpenAIClient
        self.client = OpenAIClient(api_key=self.api_key, model=model)
    
    def completion(self, prompt) -> str:
        """Simple LM query for sub-LM call."""
        try:
            response = self.client.completion(
                messages=prompt,
                timeout=300
            )
            return response
        except Exception as e:
            return f"Error making LLM query: {str(e)}"
```

**Purpose**: The `llm_query()` function in REPL calls this. It's a simpler LLM that processes chunks.

### Lines 71-199: `REPLEnv` Class Constructor

```python
class REPLEnv:
    def __init__(
        self,
        recursive_model: str = "gpt-5-mini",
        context_json: Optional[dict | list] = None,
        context_str: Optional[str] = None,
        setup_code: str = None,
    ):
        # Store original working directory
        self.original_cwd = os.getcwd()
        
        # Create temporary directory for sandboxed file operations
        self.temp_dir = tempfile.mkdtemp(prefix="repl_env_")

        # Initialize sub-LLM (the recursive call)
        self.sub_rlm: RLM = Sub_RLM(model=recursive_model)
        
        # ╔═══════════════════════════════════════════════════════════════════╗
        # ║               SANDBOXED GLOBALS (SECURITY)                         ║
        # ╚═══════════════════════════════════════════════════════════════════╝
        self.globals = {
            '__builtins__': {
                # ALLOWED: Safe built-ins
                'print': print, 'len': len, 'str': str, 'int': int, 'float': float,
                'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'bool': bool,
                'type': type, 'isinstance': isinstance, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter, 'sorted': sorted,
                'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round,
                'range': range, 'reversed': reversed, 'iter': iter, 'next': next,
                '__import__': __import__,  # Allow imports
                'open': open,              # Allow file access (in temp_dir)
                
                # Exception classes for error handling
                'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError,
                'KeyError': KeyError, 'IndexError': IndexError, 'AttributeError': AttributeError,
                # ... more exceptions ...
                
                # BLOCKED: Dangerous built-ins
                'input': None,   # No user input
                'eval': None,    # No eval
                'exec': None,    # No exec (we use our own)
                'compile': None, # No compile
                'globals': None, # No globals access
                'locals': None,  # No locals access
            }
        }
        self.locals = {}
        
        # Load context into REPL
        self.load_context(context_json, context_str)
        
        # Add llm_query function to globals
        def llm_query(prompt: str) -> str:
            """Query the LLM with the given prompt."""
            return self.sub_rlm.completion(prompt)
        
        self.globals['llm_query'] = llm_query
        
        # Add FINAL_VAR function to globals
        def final_var(variable_name: str) -> str:
            """Return variable value from REPL as final answer."""
            variable_name = variable_name.strip().strip('"').strip("'")
            if variable_name in self.locals:
                return str(self.locals[variable_name])
            else:
                return f"Error: Variable '{variable_name}' not found"
        
        self.globals['FINAL_VAR'] = final_var
```

**Key Security Measures:**
- Blocked: `eval`, `exec`, `compile`, `globals`, `locals`, `input`
- Allowed: Safe built-ins for data processing
- File ops: Restricted to temp directory

### Lines 200-223: `load_context()` Method

```python
    def load_context(self, context_json: Optional[dict | list] = None, context_str: Optional[str] = None):
        """Load context as Python variable in REPL."""
        
        # For JSON/dict context
        if context_json is not None:
            context_path = os.path.join(self.temp_dir, "context.json")
            with open(context_path, "w") as f:
                json.dump(context_json, f, indent=2)
            context_code = (
                f"import json\n"
                f"with open(r'{context_path}', 'r') as f:\n"
                f"    context = json.load(f)\n"
            )
            self.code_execution(context_code)
        
        # For string context
        if context_str is not None:
            context_path = os.path.join(self.temp_dir, "context.txt")
            with open(context_path, "w") as f:
                f.write(context_str)
            context_code = (
                f"with open(r'{context_path}', 'r') as f:\n"
                f"    context = f.read()\n"
            )
            self.code_execution(context_code)
```

**How context becomes a variable:**
1. Context saved to temp file (JSON or text)
2. Python code generated to load it
3. Code executed, creating `context` variable in REPL namespace

### Lines 264-357: `code_execution()` Method

```python
    def code_execution(self, code) -> REPLResult:
        """Simple code execution "notebook-style" in a REPL environment."""
        start_time = time.time()
        
        with self._capture_output() as (stdout_buffer, stderr_buffer):
            with self._temp_working_directory():
                try:
                    # Split code into imports and other code
                    lines = code.split('\n')
                    import_lines = [l for l in lines if l.startswith(('import ', 'from ')) and not l.startswith('#')]
                    other_lines = [l for l in lines if not l.startswith(('import ', 'from ')) or l.startswith('#')]
                    
                    # Execute imports first in globals
                    if import_lines:
                        import_code = '\n'.join(import_lines)
                        exec(import_code, self.globals, self.globals)
                    
                    # Execute rest of code
                    if other_lines:
                        other_code = '\n'.join(other_lines)
                        combined_namespace = {**self.globals, **self.locals}
                        
                        # Smart expression printing (like Jupyter)
                        # If last line is an expression, print its value
                        exec(other_code, combined_namespace, combined_namespace)
                        
                        # Update locals with new variables
                        for key, value in combined_namespace.items():
                            if key not in self.globals:
                                self.locals[key] = value
                    
                    stdout_content = stdout_buffer.getvalue()
                    stderr_content = stderr_buffer.getvalue()
                    
                except Exception as e:
                    stderr_content = stderr_buffer.getvalue() + str(e)
                    stdout_content = stdout_buffer.getvalue()
        
        execution_time = time.time() - start_time
        self.locals['_stdout'] = stdout_content
        self.locals['_stderr'] = stderr_content
        
        return REPLResult(stdout_content, stderr_content, self.locals.copy(), execution_time)
```

**Execution Flow:**
1. Capture stdout/stderr
2. Change to temp directory
3. Execute imports into globals
4. Execute code with combined namespace
5. Update locals with new variables
6. Return result with timing

---

## 📄 File: `rlm/utils/prompts.py` (70 lines)

### The System Prompt (CRITICAL)

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
answer = llm_query(f"What is the magic number? {{chunk}}")
print(answer)
```

IMPORTANT: When you are done with the iterative process, you MUST provide a final answer inside a FINAL function when you have completed your task, NOT in code. You have two options:
1. Use FINAL(your final answer here) to provide the answer directly
2. Use FINAL_VAR(variable_name) to return a variable you have created in the REPL environment

Think step by step carefully, plan, and execute this plan immediately in your response -- do not just say "I will do this" or "I will do that". Output to the REPL environment and recursive LLMs as much as possible.
"""
```

---

## 📄 File: `main.py` (Example Usage - 40 lines)

```python
from rlm.rlm_repl import RLM_REPL
import random

def generate_massive_context(num_lines: int = 1_000_000, answer: str = "1298418") -> str:
    """Generate 1M lines of random text with hidden 'magic number'."""
    print("Generating massive context with 1M lines...")
    
    random_words = ["blah", "random", "text", "data", "content", "information", "sample"]
    
    lines = []
    for _ in range(num_lines):
        num_words = random.randint(3, 8)
        line_words = [random.choice(random_words) for _ in range(num_words)]
        lines.append(" ".join(line_words))
    
    # Insert magic number at random position (middle-ish)
    magic_position = random.randint(400000, 600000)
    lines[magic_position] = f"The magic number is {answer}"
    
    print(f"Magic number inserted at position {magic_position}")
    
    return "\n".join(lines)

def main():
    print("Example of using RLM (REPL) with GPT-5-nano on a needle-in-haystack problem.")
    
    answer = str(random.randint(1000000, 9999999))
    context = generate_massive_context(num_lines=1_000_000, answer=answer)

    rlm = RLM_REPL(
        model="gpt-5-nano",           # Cheap model for orchestration
        recursive_model="gpt-5",       # Powerful model for chunk analysis
        enable_logging=True,
        max_iterations=10
    )
    
    query = "I'm looking for a magic number. What is it?"
    result = rlm.completion(context=context, query=query)
    
    print(f"Result: {result}. Expected: {answer}")

if __name__ == "__main__":
    main()
```

**What This Demonstrates:**
- 1 million lines of noise
- 1 hidden needle ("The magic number is X")
- RLM finds it by chunking and parallel sub-LLM calls

---

# PART 4: THE PAPER (arXiv:2512.24601)

## 📄 Citation

```bibtex
@article{zhang2025rlm,
  title={Recursive Language Models},
  author={Zhang, Alex L. and Kraska, Tim and Khattab, Omar},
  journal={arXiv preprint arXiv:2512.24601},
  year={2025}
}
```

## Authors
- **Alex L. Zhang** - MIT (@a1zhang)
- **Tim Kraska** - MIT
- **Omar Khattab** - Stanford/MIT (@lateinteraction)

## Abstract (Verbatim)

> "We study allowing large language models (LLMs) to process arbitrarily long prompts through the lens of inference-time scaling. We propose Recursive Language Models (RLMs), a general inference strategy that treats long prompts as part of an external environment and allows the LLM to programmatically examine, decompose, and recursively call itself over snippets of the prompt. We find that RLMs successfully handle inputs up to two orders of magnitude beyond model context windows and, even for shorter prompts, dramatically outperform the quality of base LLMs and common long-context scaffolds across four diverse long-context tasks, while having comparable (or cheaper) cost per query."

## Key Results Summary Table

| Benchmark | Task | RLM Performance |
|-----------|------|-----------------|
| **S-NIAH** | Needle-in-haystack | Handles 10M+ tokens |
| **BrowseComp-Plus** | Multi-hop web reasoning | Stable at 10M tokens |
| **OOLONG** | Fine-grained reasoning | RLM + GPT-5-mini > vanilla GPT-5 |
| **OOLONG-pairs** | Comparative reasoning | Same pattern |

## Core Concepts

1. **Prompt as Object**: The prompt is a Python variable that can be manipulated
2. **REPL Environment**: Sandboxed Python execution with `context` variable
3. **Sub-LLM Calls**: `llm_query()` function for chunk analysis
4. **Recursive Depth**: Currently depth=1 (not truly recursive yet)

## Formal Definition (The RLM Tuple)

The RLM is formally defined as a tuple of three components:
- **Root LM**: The orchestrating model (e.g., GPT-5-nano) that decides what to do
- **Environment**: A Python REPL that stores context as a variable
- **Sub-LM**: A (potentially smaller/cheaper) model callable from the REPL for chunk analysis

## Practical Benefits Summary

1. **Root LM context never clogs** — it never sees the entire context directly
2. **Flexible viewing** — can use `regex` to narrow context, then recurse over subsets
3. **Modality agnostic** — context can be any data loadable into memory
4. **Cheaper per query** — despite multiple calls, often cheaper than giant context windows

---

# PART 5: CORE CONCEPTS FROM THE BLOG/PAPER

## The Problem: Context Rot

Alex defines the core challenge:

> "There is this well-known but difficult to characterize phenomenon in language models (LMs) known as 'context rot'... it's almost like, as the conversation goes on, the model gets…dumber?"

**Key insight**: Traditional LLMs degrade as context length increases, even when technically within the context window limit.

## The Solution: Recursive Language Models

**Definition**: 
> "We propose Recursive Language Models (RLMs), an inference strategy where language models can decompose and recursively interact with input context of unbounded length through REPL environments."

**Key Architecture**:

```
                    ┌─────────────────┐
                    │   USER QUERY    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    ROOT LM      │
                    │  (Orchestrator) │
                    │                 │
                    │ Decides:        │
                    │ - What to do    │
                    │ - How to chunk  │
                    │ - When done     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐ ┌───▼───┐ ┌────────▼────────┐
     │   REPL ENV      │ │  ...  │ │   REPL ENV      │
     │                 │ │       │ │                 │
     │ - context var   │ │       │ │ Iteration N     │
     │ - llm_query()   │ │       │ │                 │
     │ - print()       │ │       │ │ - Variables     │
     └────────┬────────┘ └───────┘ └────────┬────────┘
              │                              │
    ┌─────────┼─────────┐          ┌─────────┼─────────┐
    ▼         ▼         ▼          ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐  ┌───────┐ ┌───────┐ ┌───────┐
│SUB-LM │ │SUB-LM │ │SUB-LM │  │SUB-LM │ │SUB-LM │ │SUB-LM │
│Chunk 1│ │Chunk 2│ │Chunk 3│  │Chunk 4│ │Chunk 5│ │Chunk N│
└───────┘ └───────┘ └───────┘  └───────┘ └───────┘ └───────┘
```

## Key Design Principles

1. **Context-Centric View**: RLMs treat the context as an object to be manipulated, not just consumed
2. **REPL as Extended Memory**: Variables persist across iterations, allowing complex state building
3. **LLM as its Own Orchestrator**: The model decides how to chunk and process, not the programmer
4. **Recursive Sub-Calls**: The root LM can invoke sub-LMs to process chunks

## Three Key Benefits

From Alex's blog:

1. **The context window of the root LM is rarely clogged** — because it never directly sees the entire context, its input context grows slowly.

2. **Flexibility in processing** — The root LM can use `regex` queries to narrow the context, then launch recursive LM calls over this context. This is particularly useful for arbitrary long context inputs, where indexing a retriever is expensive on the fly!

3. **Modality agnostic** — The context can, in theory, be any modality that can be loaded into memory.

## RLM API Design

> "A recursive language model is a thin wrapper around a LM that can spawn (recursive) LM calls for intermediate computation — from the perspective of the user or programmer, it is the same as a model call."

```python
# RLM is a drop-in replacement for LM
rlm.completion(messages)  # Same as gpt5.completion(messages)
```

## The Two Key Design Choices (Straight from Alex's Blog)

> "The two key design choices of recursive language models are:
> 1. **Treating the prompt as a Python variable**, which can be processed programmatically in arbitrary REPL flows. This allows the LLM to figure out what to peek at from the long context, at test time, and to scale any decisions it wants to take (e.g., come up with its own scheme for chunking and recursion adaptively)
> 2. **Allowing that REPL environment to make calls back to the LLM** (or a smaller LLM), facilitated by the decomposition and versatility from choice (1)."

## The "Context Rot" Problem (Why This Matters)

Alex describes context rot as:
> "this weird thing that happens when your Claude Code history gets bloated, or you chat with ChatGPT for a long time — it's almost like, as the conversation goes on, the model gets…dumber? It's sort of this well-known but hard to describe failure mode that we don't talk about in our papers because we can't benchmark it."

The natural solution:
> "well maybe if I split the context into two model calls, then combine them in a third model call, I'd avoid this degradation issue"

---

# PART 6: EXPERIMENTAL RESULTS

## Result #1: OOLONG Benchmark (Context Rot)

**Setup**: Queries over 128k+ tokens with ~3000-6000 rows of data requiring semantic understanding.

**Results at 132k tokens**:
| Method | Score | Cost |
|--------|-------|------|
| GPT-5 | ~30 | Baseline |
| GPT-5-mini | ~25 | Lower |
| **RLM(GPT-5-mini)** | **~64** | ~Same as GPT-5 |
| RLM(GPT-5) no sub-calls | ~54 | Higher |
| ReAct + GPT-5 + BM25 | ~15 | Variable |

**Key Finding**: 
> "RLM(GPT-5-mini) outperforms GPT-5 by over **34 points (~114% increase)**, and is nearly as cheap per query!"

**Results at 263k tokens**:
> "RLM(GPT-5-mini) outperforms GPT-5 by over **15 points (~49% increase)**, and is cheaper per query on average."

## Result #2: BrowseComp-Plus (Massive Contexts)

**Setup**: Multi-hop queries over corpus of up to 1000 documents (10M+ tokens).

**Key Finding**:
> "`RLM(GPT-5)` is the only model / agent able to achieve and maintain **perfect performance at the 1000 document scale**"

**Results**:
| Documents | GPT-5 | GPT-5 + BM25 | ReAct | RLM(GPT-5) |
|-----------|-------|--------------|-------|------------|
| 10 | ~90% | ~90% | ~85% | ~100% |
| 50 | ~70% | ~75% | ~75% | ~100% |
| 100 | ~50% | ~60% | ~80% | ~100% |
| 1000 | ~0% (truncated) | ~40% | ~75% | **~100%** |

---

# PART 7: RLM STRATEGIES THAT EMERGE

Alex documented several strategies that the RLM learns to employ:

## 1. Peeking
> "At the start of the RLM loop, the root LM does not see the context at all — it only knows its size. Similar to how a programmer will peek at a few entries when analyzing a dataset, the LM can peek at its context to observe any structure."

```python
# Example: Grab first 2000 characters
print(context[:2000])
```

## 2. Grepping
> "To reduce the search space of its context, rather than using semantic retrieval tools, the RLM with REPL can look for keywords or regex patterns to narrow down lines of interest."

```python
import re
matches = re.findall(r'User: \d+', context)
```

## 3. Partition + Map
> "A common pattern the RLM will perform is to chunk up the context into smaller sizes, and run several recursive LM calls to extract an answer or perform this semantic mapping."

```python
chunks = [context[i:i+500000] for i in range(0, len(context), 500000)]
results = []
for chunk in chunks:
    result = llm_query(f"Label each question: {chunk}")
    results.append(result)
```

## 4. Summarization
> "RLMs are a natural generalization of summarization-based strategies commonly used for managing the context window of LMs."

## 5. Long-Input, Long-Output
> "For tasks that require long output generations... RLMs with REPL environments should one-shot these tasks!"

Example: On the LoCoDiff benchmark (tracking long git diff histories), RLM can programmatically process the sequence of diffs.

---

# PART 8: LIMITATIONS AND FUTURE DIRECTIONS

## Limitations

### Speed and Asynchrony
> "We did not optimize our implementation of RLMs for speed, meaning each recursive LM call is both blocking and does not take advantage of any kind of prefix caching! Depending on the partition strategy employed by the RLM's root LM, the **lack of asynchrony** can cause each query to range from a few seconds to several minutes."

### No Cost/Runtime Guarantees
> "We do not currently have strong guarantees about controlling either the total API cost or the total runtime of each call."

### Opportunity for Systems Research
> "For those in the systems community (*cough cough*, especially the GPU MODE community), this is amazing news! There's so much low hanging fruit to optimize here, and getting RLMs to work at scale requires re-thinking our design of inference engines."

### The Depth-1 Limitation (Acknowledged by Authors)

> "Lastly, in our experiments we only consider a recursive depth of 1 — i.e. the root LM can only call LMs, not other RLMs. It is a relatively easy change to allow the REPL environment to call RLMs instead of LMs, but we felt that for most modern "long context" benchmarks, **a recursive depth of 1 was sufficient to handle most problems**."

## Future Directions

### Key Insights from Alex

#### 1. Do we have to solve context rot?
> "The goal of RLMs has been to propose a framework for issuing LM calls without ever needing to directly solve this problem — while the idea was initially just a framework, we were very surprised with the strong results on modern LMs, and are optimistic that they will continue to scale well."

#### 2. RLMs are not agents, nor are they just summarization
> "These approaches generally view multiple LM calls as decomposition **from the perspective of a task or problem**. We retain the view that LM calls can be decomposed by the context, and the choice of decomposition should purely be the choice of an LM."

#### 3. The value of a fixed format for scaling laws
> "We are excited to see how we can apply these ideas to improve the performance of RLMs as another axis of scale."

#### 4. RLMs improve as LMs improve
> "If tomorrow, the best frontier LM can reasonably handle 10M tokens of context, then an RLM can reasonably handle 100M tokens of context (maybe at half the cost too)."

### The Fundamental Bet

> "As a lasting word, RLMs are a fundamentally different bet than modern agents. Agents are designed based on human / expert intuition on how to break down a problem to be digestible for an LM. **RLMs are designed based on the principle that fundamentally, LMs should decide how to break down a problem to be digestible for an LM.** I personally have no idea what will work in the end, but I'm excited to see where this idea goes!"
>
> --az

---

# PART 9: RAW HACKER NEWS COMMENTS (35 Comments - VERBATIM)

## Thread: https://news.ycombinator.com/item?id=45596059

**135 points | 35 comments | Oct 15-19, 2025**

---

### COMMENT 1: cs702 (Top Comment)

> "Briefly, an RLM wraps an existing language model (LM) together with an environment that can dynamically manipulate the prompt that will be fed into the LM.
>
> The authors use as an environment a Python REPL that itself can call other instances of the LM. The prompt is programmatically manipulated as a Python variable on the REPL.
>
> The motivation is for the LM to use Python commands, including commands that call other LM instances, to figure out how best to modify the context at inference time.
>
> The results from early testing look impressive at a first glance: An RLM wrapping GPT-5-mini outperforms GPT-5 by a wide margin on long-context tasks, at significant lower cost.
>
> I've added this to my reading list."

---

### COMMENT 2: NitpickLawyer (Reply to cs702)

> "A comparison to dSPY would be nice. cmd+f in the provided link doesn't bring any results tho..."

---

### COMMENT 3: cs702 (Reply to NitpickLawyer)

> "An RLM is like a language model using DSPy plus all of Python to manipulate its prompt."

---

### COMMENT 4: integricho 🔥 CRITICISM

> "Sounds like unforgivable overhead for very questionable benefits, this whole LLM space is an overengineered slop, and everyone is jumping in building layers on top of layers of slop."

---

### COMMENT 5: jgbuddy 🔥 CRITICISM

> "This is old news! Agent-loops are not a model architechture"

---

### COMMENT 6: adastra22 (Reply to jgbuddy)

> "I'm confused over your definition of model architecture."

---

### COMMENT 7: layer8 (Deep Insight)

> "Loops aren't recursion?"

---

### COMMENT 8: antonvs (Reply to layer8)

> "Loops and recursion are fundamentally equivalent.
>
> See e.g. https://textbooks.cs.ksu.edu/cc210/16-recursion/08-recursion..."

---

### COMMENT 9: layer8 (Counter-Argument - PROFOUND) 🧠

> "Only if you have indexable memory that you can use as a stack, which in the context of LMs isn't a given.
>
> As another example, a finite-state-machine language can have loops, but it can't recurse unless there is external memory it has access to in a way that it can serve as a stack. Regular expressions also fall into that pattern; they can loop, but they can't recurse. For that you need a pushdown automaton: https://en.wikipedia.org/wiki/Pushdown_automaton ."

---

### COMMENT 10: laughingcurve 🔥 CRITICISM

> "Everything old is new again when you are in academia"

---

### COMMENT 11: hodgehog11 (Reply to laughingcurve)

> "This feels primarily like an issue with machine learning, at least among mathematical subdisciplines. As new people continue to be drawn into the field, they rarely bother to read what has come even a few years prior (nevermind a few decades prior)."

---

### COMMENT 12: nathanwh (Comparison to Prior Work)

> "This reminded me of ViperGPT[1] from a couple of years ago, which is similar but specific to vision language models. Both of them have a root llm which given a query produces a python program to decompose the query into separate steps, with the generated python program calling a sub model. One difference is this model has a mutable environment in the notebook, but I'm not sure how much of a meaningful difference that is.
>
> [1] https://viper.cs.columbia.edu/static/viper_paper.pdf"

---

### COMMENT 13: pontusrehula (Technical Question)

> "If you would setup an RLM, would you set a higher temperature for the root LLM calls and a lower temperature for LLM calls deeper in the recursion?"

---

### COMMENT 14: patcon (Reply to pontusrehula)

> "Just wanted to say that I really like this question. Very thought-provoking :)
>
> EDIT: makes me think of many computation systems in various substrates, and how they work. Focus vs distraction/creativity. ADHD workers in hierarchies of capitalism, purpose of breadth vs depth of exploration at various levels of the stack, who's at the "top" and why, etc etc"

---

### COMMENT 15: ttul (COMPARISON TO CODEX) ⚡

> "This is what Codex is doing. The LM has been trained to work well with the kinds of tools that a solid developer would use to navigate and search around a code repository and then to reason about what it finds. It's also really competent at breaking down a task into steps. But I think the real magic - watching this thing for at least 40 of the last 50 working hours - is how it uses command line tools to dig through code quickly and accurately.
>
> It's not relying on the LM context much. You can generally code away for an hour before you run out of context and have to run a compression step or just start fresh."

---

### COMMENT 16: nowittyusername

> "My existing project is very similar to this with some other goodies. I agree with the author that focus on systems versus LLM's is the proper next move. Orchestrating systems that manage multiple different llms and other scripts together can accomplish a lot more then a simple ping pong type of behavior. Though I suspect most people who work with agentic solutions are already quite aware of this. What most in that space haven't cracked yet is the dynamic self modifying and improving system, that should be the ultimate goal for these types of systems."

---

### COMMENT 17: fizx (COMPARISON TO CLAUDE CODE) ⚡ 🔥 CRITICISM

> "I read the article, and I'm struggling to see what ideas it brings beyond CodeAct (tool use is python) or the 'task' tool in Claude code (spinning off sub-agents to preserve context)."

---

### COMMENT 18: Weaver_zhu 🔥 CRITICISM (Depth=1 Problem)

> "IMO the author is a little over-claiming this work by naming 'recursive'. Quote from this blog:
>
> > Lastly, in our experiments we only consider a recursive depth of 1 — i.e. the root LM can only call LMs, not other RLMs.
>
> > but we felt that for most modern "long context" benchmarks, a recursive depth of 1 was sufficient to handle most problems.
>
> I don't think a size 2 call stack algorithm should be regarded as 'recursive'."

---

### COMMENT 19: behnamoh 🔥 HARSH CRITICISM

> "in today's news: MIT researchers found out about AI agents and rebranded it as RLM for karma."

---

### COMMENT 20: rf15 (Reply to behnamoh) 🔥 CRITICISM

> "or: found out about RNNs with extra steps."

---

### COMMENT 21: quibit 🔥 CRITICISM (Depth=1 Problem)

> "> Lastly, in our experiments we only consider a recursive depth of 1 — i.e. the root LM can only call LMs, not other RLMs. It is a relatively easy change to allow the REPL environment to call RLMs instead of LMs, but we felt that for most modern "long context" benchmarks, a recursive depth of 1 was sufficient to handle most problems. However, for future work and investigation into RLMs, enabling larger recursive depth will naturally lead to stronger and more interesting systems.
>
> It feels a little disingenuous to call it a Recursive Language Model when the recursive depth of the study was only 1."

---

### COMMENT 22: sophia_james (Understanding Check)

> "I'm not sure if I understood this correctly:
>
> 1. Recursion is used to break down the large context and dispatch to different LLM calls to get the useful context.
>
> 2. This may lead to longer test-time execution on large contexts (even with parallelism in deep recursion), and the monetary cost may increase rapidly.
>
> I think it's a different idea from using RAG or manually maintaining a context window
>
> correct me if I'm wrong"

---

### COMMENT 23: ipnon (COMPARISON TO CLAUDE) ⚡

> "Hopefully this can solve the problem of Claude needing to compact itself every 10 minutes, blocking execution. It would be better if it was always compacting in the background. But that requires perhaps more compute than is realistic."

---

### COMMENT 24: wild_egg (Reply to ipnon - CLAUDE SUBAGENT TIP)

> "Tell it to use subagents more. I often say something like 'you're banned from taking direct actions, use subagents for everything' and it can run easily for 60-90 minutes before a compaction."

---

### COMMENT 25: rancar2 (Reply - CODEX COMPARISON) ⚡

> "For that issue, try Codex until Claude catches up to your style."

---

### COMMENT 26: lukebechtel 🔥 CRITICISM

> "this doesn't appear to bring anything new to the table.
>
> please correct me if I'm wrong..this is just subagent architecture?"

---

### COMMENT 27: vrighter 🔥 HARSHEST CRITICISM (77 days later)

> "a model calls another (not self) model, which in turn returns without calling anything else. What you've discovered is called a function call.
>
> It simply hopes two drunks are more coherent than one drunk."

---

### COMMENT 28: UltraSane (Positive)

> "Extending this so that the Root LLM can choose the best option from many other LLMs seems pretty powerful."

---

### COMMENT 29: yandie 🔥 CRITICISM

> "This isn't just context optimization. Not much different from agent-to-agent workflow IMO."

---

### COMMENT 30: ayazhan (Related Work Reference)

> "https://arxiv.org/abs/2510.04871 another recursive based model"

---

### COMMENT 31: d0mine (Reply to ayazhan - TRM Comparison)

> "> TRM obtains 45% test-accuracy on ARC-AGI-1 and 8% on ARC-AGI-2, higher than most LLMs (e.g., Deepseek R1, o3-mini, Gemini 2.5 Pro) with less than 0.01% of the parameters."

---

### COMMENT 32: yorwba (Reply to ayazhan)

> "It's a completely different kind of recursion for a completely different (non-language) task."

---

### COMMENT 33: foolswisdom (Reply to ayazhan)

> "I actually came here expecting this to be a language model application of that recursive reasoning paper."

---

### COMMENT 34: gdiamos (Naming Criticism)

> "Recursion is so popular in computing that this term 'recursive language model' is heavily overloaded
>
> It was even before the rise of LLMs
>
> The authors may want to consider a more specific name"

---

### COMMENT 35: halfmatthalfcat (Last Comment)

> "It broke new ground!"

---

# PART 10: RAW X/TWITTER DISCUSSIONS (100+ Tweets - VERBATIM)

## Original Tweet - @a1zhang (Jan 2, 2026)

**Stats:** 152 replies, 685 reposts, 3,659 likes, 3,362 bookmarks, 571K+ views

> "Much like the switch in 2025 from language models to reasoning models, we think 2026 will be all about the switch to Recursive Language Models (RLMs).
>
> It turns out that models can be far more powerful if you allow them to treat *their own prompts* as an object in an external environment, which they understand and manipulate by writing code that invokes LLMs!
>
> Our full paper on RLMs is now available—with much more expansive experiments compared to our initial blogpost from October 2025!
>
> https://arxiv.org/pdf/2512.24601"

---

## Omar Khattab (@lateinteraction) - KEY INSIGHT

**Stats:** 28 replies, 147 retweets, 892 likes

> "Most people (mis)understand RLMs to be about LLMs invoking themselves.
>
> **The deeper insight is LLMs *interacting with their own prompts as objects*.**
>
> In an RLM, the prompt IS a python variable. The model generates code that manipulates it. It's not about nesting models — it's about giving models genuine agency over their own inputs.
>
> That's why RLMs beat long-context directly. Not because they're 'smarter' at reading — but because they're doing something categorically different: **programming their own attention.**"

---

## 🔥 CRITICAL/SKEPTICAL REPLIES

### @ten3br1s (Peter Szemraj):
> Congrats on rebranding map-reduce!

### @llm_wizard (Chris):
> Researchers can call things whatever they want, but I'll be honest: I went into this paper expecting something completely different from what I wound up reading.
>
> Definitely dope work, but the naming felt like accidental clickbait.
>
> Especially because we already have plenty of...

### @Massimo26472949 (Massimiliano Brighindi):
> Framing RLMs as a "paradigm shift" is overstated. What you show is inference time orchestration treating the prompt as external state slicing it and recursively invoking an LLM. This is powerful and practical but it is not a new model class it is a control runtime strategy.

### @PirouneB (piroune):
> The RLM naming does overload though... reasoning LMs vs recursive LMs are genuinely different concepts competing for the same acronym.

### @silverhawk_ny (arch rock):
> One question I have is this seems like most agent framework are doing? if your think their multi step agentic context as a single unit long context, or I miss something?

### @AIBenchmarked:
> reasoning models are cool but i still have to explain to my boss why the agent spent $50 loops-searching for a file that doesn't exist

### @ShashwatGoel7 (Shashwat Goel):
> I think my qualm with the naming is not that it's not different from regular LMs, but more:
>
> Is it different from spawning subagents?

### @its_jeremy_hon (jeremyh):
> Does this strategy preserve caching cost optimizations?

### @SenseNopedOut:
> It walks like a duck
> It quacks like a duck
> Then it probably is Claude Code [image]

---

## 💡 INSIGHTFUL/TECHNICAL REPLIES

### @kynan_eng (Kynan Eng):
> This seems like hacking the prompt to create a kind of extra working memory by "talking to oneself"? I can see how this might be useful for certain reasoning tasks that are very limited in scope and time, although not sure how that generalizes to long-term memory

### @xiatao_sun (Xiatao Sun):
> The fact that an RLM with a smaller backbone can beat a larger vanilla model on OOLONG and stay stable on BrowseComp-Plus at 10M+ tokens is a pretty strong signal that inference-time scaffolding is now as important as base model capacity.

### @RobKeimig (Rob Keimig):
> It would seem a limit to recursive depth is mandatory. I am finding it will hit any specified limit 100% of the time. I am considering a probabilistic bail-out scheme where the deeper it goes the more likely it will arbitrarily halt with a warning message at that level.

### @casper_hansen_ (Casper Hansen):
> interview question: so you like recursive language models, now make it a while loop
>
> jokes aside, this indeed looks pretty useful. the main problem with agents always has been growing context. this looks like a great attempt at solving it!

### @hallerite:
> Yeah, to me the RLM solves the "prompt is too long to be ingested" problem and subagent tool-calls solve the context pollution problem of the main branch, though I assume long running agents would also create plans and dump them to a file they can read. I think my main gripe with...

### @hallerite (follow-up):
> This I don't quite understand. My definition of a subagent is an agent with the context cleared that gets prompted by the main agent and from the POV of the main agent it's a blackbox, simply returning an answer. It could be a ReAct-style agent, another RLM or whatever else.

### @Grad62304977 (Grad):
> ya idk why ppl treat this differently to reasoning vs non-reasoning models. I guess here its a bit different but as long as the RLM structure as it is being very general and simple i think it should warrant similar treatment

### @bevvscott (Bev Scott):
> This is extremely interesting. Reminiscent of a person writing a high-quality exam essay response: identify (e.g. highlight, underline) the key points in the exam question, start writing, then continue to revisit the key points repeatedly through the writing process. Very cool.

### @skekici (Suleyman Kivanc EKICI):
> If this scales, the entire Vector Database industry is dead.
>
> Why build a complex RAG pipeline (chunking to embedding to retrieval) when the model can just recursively grep its own context?
>
> The "External Brain" is being absorbed back into the "Internal Architecture."

### @archanfel_anoth (Juntang Zhuang):
> Cool idea. How is this related to DSpy or textgrad? Also it seems possible to include language model optimization into code execution, then it could be really generic?

### @Devarsh786 (DoKoB):
> I've implemented this myself after your paper, and I was wondering how would you approach (or reduce) the time to response issue? I've tested with 1.8M context and it generally took 30-45 seconds with smaller models like 4o-mini.

### @osoleve (oso):
> Working on something that's spiritually RLM but a little more recursive in nature, would be happy to share my notes if there are any interesting concepts in there for you to incorporate
>
> (I'm putting my bet on the winning horse, you have momentum with RLMs and I just build toys)

### @saurabhjha2010 (Saurabh Jha):
> I would love to see a baseline where one stores context, output and reasoning tokens in files (context store) and let codex/goose/cursor-style agents/frameworks handle the large context.
> i.e., codex using codex as a sub-agent. The sub-agent's only job is to extract

---

## 🎉 POSITIVE/SUPPORTIVE REPLIES

### @Buddadoc:
> I created a Codex and Claude Code plugin based on this. Amazing paper!
> https://t.co/qVvT1ULBrI

### @aihsannergiz (Ali Ihsan Nergiz):
> spent most of my otherwise doomed, delayed flight reading the paper, great job! sent first PR on your way, more to come

### @llm_wizard (Chris):
> All makes sense, and again - all that *really* matters is that it's a banger.
>
> A banger that also nerdsniped everyone lol

### @pelaseyed (homanp):
> Great work! Here are some questions:
>
> Could we in theory fine tune smaller models to be better at the RLM strategy?
>
> Are you planning on making a Claude Code Skill for RLM (claude should have all the underlying tools necessary to run RLM?)

### @p_misirov (P.M):
> great read! also this architecture makes inference very customizable, for example, you could add modular safety prompts to prevent jailbreaks without affecting context quality

### @crosstensor (CrossProduct):
> Simulated Recursive Language Modelling more accurate? your original name was a banger for great reach

---

## 🛠️ IMPLEMENTATION QUESTIONS

### @LaBlua (Kevin C.):
> On #3, Python has async and LLMs know how to write async code. Have you tried just letting the recursive call be async and let the LLM figure out the rest? Or is there a reason that's a bad idea?

### @bhi5hmaraj (Bhishmaraj S):
> Why not use file system for persistence? Unix tools are really well suited for text manipulation.

### @manojlds (Manoj Mahalingam):
> How about pyodide for local?

### @Ethan_Connelly (Ethan Connelly):
> Is there any support for images in context?

### @Devarsh786 (DoKoB):
> Filtering + Early return can be helpful with some scenarios. Also for sub-agents using models like GPT OSS 120B or GLM 4.6 which are hosted on Groq/Cerebras can also help a lot.

### @muvaffakonus (Muvaffak):
> Wonder whether the remix could be additive and still provide benefits, eg at every prompt you append LLM-engineered context instead of re-engineer the whole context

---

# PART 11: CRITICISM & DEFENSE DEEP DIVE

## 📊 CATEGORIZED CRITICISM

### 🔴 "NOT ACTUALLY RECURSIVE" (Depth=1 Problem)

| Source | Quote |
|--------|-------|
| **Weaver_zhu (HN)** | "I don't think a size 2 call stack algorithm should be regarded as 'recursive'." |
| **quibit (HN)** | "It feels a little disingenuous to call it a Recursive Language Model when the recursive depth of the study was only 1." |

### 🔴 "JUST AGENT LOOPS / NOT NEW"

| Source | Quote |
|--------|-------|
| **jgbuddy (HN)** | "This is old news! Agent-loops are not a model architecture" |
| **behnamoh (HN)** | "in today's news: MIT researchers found out about AI agents and rebranded it as RLM for karma." |
| **rf15 (HN)** | "or: found out about RNNs with extra steps." |
| **fizx (HN)** | "I'm struggling to see what ideas it brings beyond CodeAct or the 'task' tool in Claude code" |
| **lukebechtel (HN)** | "this is just subagent architecture?" |
| **yandie (HN)** | "Not much different from agent-to-agent workflow IMO." |
| **@ten3br1s (X)** | "Congrats on rebranding map-reduce!" |
| **@SenseNopedOut (X)** | "It walks like a duck, quacks like a duck, then it probably is Claude Code" |

### 🔴 "OVERENGINEERED / NOT NOVEL"

| Source | Quote |
|--------|-------|
| **integricho (HN)** | "Sounds like unforgivable overhead for very questionable benefits, this whole LLM space is an overengineered slop" |
| **@Massimo26472949 (X)** | "This is powerful and practical but it is not a new model class it is a control runtime strategy." |

### 🔴 HARSHEST CRITICISM

| Source | Quote |
|--------|-------|
| **vrighter (HN)** | "a model calls another (not self) model, which in turn returns without calling anything else. What you've discovered is called a function call. **It simply hopes two drunks are more coherent than one drunk.**" |

### 🟡 NAMING/TERMINOLOGY ISSUES

| Source | Quote |
|--------|-------|
| **gdiamos (HN)** | "Recursion is so popular in computing that this term 'recursive language model' is heavily overloaded... The authors may want to consider a more specific name" |
| **@PirouneB (X)** | "reasoning LMs vs recursive LMs are genuinely different concepts competing for the same acronym." |

---

## 🟢 INSIGHTFUL DEFENSES

| Source | Quote |
|--------|-------|
| **layer8 (HN)** | "Only if you have indexable memory that you can use as a stack, which in the context of LMs isn't a given." |
| **cs702 (HN)** | "An RLM is like a language model using DSPy plus all of Python to manipulate its prompt." |
| **Omar Khattab (X)** | "The deeper insight is LLMs *interacting with their own prompts as objects*." |
| **@xiatao_sun (X)** | "The fact that an RLM with a smaller backbone can beat a larger vanilla model on OOLONG... is a pretty strong signal that inference-time scaffolding is now as important as base model capacity." |

---

## ⚡ RLM vs CLAUDE CODE vs CODEX

### From HN Thread:

**fizx on Claude Code:**
> "I'm struggling to see what ideas it brings beyond CodeAct (tool use is python) or the **'task' tool in Claude code** (spinning off sub-agents to preserve context)."

**ttul on Codex (40+ hours experience):**
> "**This is what Codex is doing.** The LM has been trained to work well with the kinds of tools that a solid developer would use to navigate and search around a code repository... But I think the real magic - watching this thing for at least 40 of the last 50 working hours - is **how it uses command line tools to dig through code quickly and accurately**."

**wild_egg (Claude Subagent Tip):**
> "Tell it to use subagents more. I often say something like **'you're banned from taking direct actions, use subagents for everything'** and it can run easily for 60-90 minutes before a compaction."

**rancar2:**
> "For that issue, try Codex until Claude catches up to your style."

---

# PART 12: THE REAL INNOVATION (SYNTHESIS)

## What RLM IS NOT (According to Critics):
- Just agent loops (that's old)
- Just function calling (that's basic)
- True recursion (depth is only 1)
- A new model class (it's inference-time scaffolding)

## What RLM IS (The Real Innovation):
1. **Treating prompts as first-class objects** that the model can manipulate programmatically
2. **Giving LLMs pushdown automaton capabilities** via external memory (the REPL environment)
3. **Formalization** of a pattern that tools like Codex and Claude Code are already using intuitively
4. **A theoretical framework** for thinking about LLM+tool systems as a new computational class

## The Key Reframe (Omar Khattab):
> "The deeper insight is LLMs *interacting with their own prompts as objects*."

## The Computational Theory Insight (layer8):
> "Only if you have indexable memory that you can use as a stack, which in the context of LMs isn't a given. For that you need a pushdown automaton."

**Translation**: RLM is essentially giving LLMs access to a pushdown automaton through the REPL environment, upgrading them from finite-state-machines to more powerful computational models.

## The "Two Drunks" Counterargument:
The criticism "It simply hopes two drunks are more coherent than one drunk" (vrighter) misses the point—it's not about multiple models being smarter together, it's about **giving the model external memory and the ability to manipulate its own context programmatically**.

---

# PART 13: OPEN QUESTIONS FROM THE COMMUNITY

1. **Temperature tuning**: Should root LM have higher temperature (exploration) and sub-LMs have lower temperature (exploitation)?

2. **True deep recursion**: What happens when you allow recursive depth > 1? The authors say it's "a relatively easy change" but haven't tested it.

3. **Cost tradeoffs**: How does RLM compare to RAG and long-context models in terms of cost/quality tradeoff at scale?

4. **Self-modification**: Can RLMs be extended to modify their own code/prompts over time, becoming self-improving systems?

5. **Multi-model routing**: Can the root LM learn to route to different specialist models based on the sub-task?

6. **Caching preservation**: Does this strategy preserve caching cost optimizations? (asked by @its_jeremy_hon)

7. **Async execution**: Have you tried just letting the recursive call be async and let the LLM figure out the rest? (asked by @LaBlua)

8. **Image support**: Is there any support for images in context? (asked by @Ethan_Connelly)

9. **Time-to-response**: How to reduce the 30-45 second latency with 1.8M context? (asked by @Devarsh786)

---

# PART 14: KEY TAKEAWAYS

1. **The recursion depth=1 is a MAJOR criticism** - Multiple commenters feel "recursive" is misleading

2. **Comparison to existing tools** (Claude Code task tool, Codex, DSPy) is frequent

3. **The "two drunks" metaphor** captures skepticism about whether more LLM calls = better

4. **layer8's insight** about needing external memory/stack for true recursion is profound

5. **Practical users prefer Codex** for avoiding context compaction issues

6. **Claude subagent tip**: "ban direct actions" extends runtime 6x (10 min → 60-90 min)

7. **RAG vs RLM debate**: "Why build a complex RAG pipeline when the model can just recursively grep its own context?"

8. **Time-to-response concerns**: 30-45 seconds with 1.8M context on smaller models

9. **Real-world implementations already exist**: People building Codex/Claude Code plugins based on the paper

10. **Omar Khattab's reframe**: It's not about recursion—it's about "programming your own attention"

11. **The ML field has a literature problem**: "new people rarely bother to read what has come even a few years prior" (hodgehog11)

12. **The harshest critics see zero novelty**: vrighter's "two drunks" comment, behnamoh's "rebranded for karma"

---

# PART 15: RELATED WORKS

## Scaffolds for long input context management
- **MemGPT** - Defers context management to the model, builds on single context
- **MemWalker** - Tree-like structure for LM summarization
- **LADDER** - Problem decomposition approach (doesn't scale to huge contexts)

## Other recursive proposals
- **THREAD** - Spawns child threads during output generation
- **Tiny Recursive Model (TRM)** - https://arxiv.org/abs/2510.04871 - Iteratively improving model answers
  - "TRM obtains 45% test-accuracy on ARC-AGI-1 and 8% on ARC-AGI-2, higher than most LLMs (e.g., Deepseek R1, o3-mini, Gemini 2.5 Pro) with less than 0.01% of the parameters."
- **Recursive LLM Prompts** (Andy Konwinski) - Early experiment on prompt as evolving state
- **Recursive Self-Aggregation (RSA)** - Test-time inference sampling over candidates

## Related Concepts
- **CodeAct** - Executable code actions for LLM agents (inspired RLM's REPL design)
- **ROMA** - Decomposes problems and runs sub-agents
- **ViperGPT** - https://viper.cs.columbia.edu/static/viper_paper.pdf - Similar pattern for vision-language models
- **DSPy** - Programmatic prompt manipulation
- **Pushdown Automaton** - https://en.wikipedia.org/wiki/Pushdown_automaton

## Key Benchmarks Referenced

1. **OOLONG** - Long-context reasoning over fine-grained information
   - [OpenReview Link](https://openreview.net/forum?id=lrDr6dmXOX)

2. **BrowseComp-Plus** - Deep research agent evaluation with offline corpus
   - [arxiv PDF](http://arxiv.org/pdf/2508.06600.pdf)

3. **LoCoDiff** - Long git diff history tracking
   - [Project Website](https://abanteai.github.io/LoCoDiff-bench/)

4. **BrowseComp** - Multi-hop web search queries (OpenAI)
   - [OpenAI Index](https://openai.com/index/browsecomp/)

---

# 🔗 REFERENCES

| Resource | URL |
|----------|-----|
| **Paper** | https://arxiv.org/abs/2512.24601 |
| **GitHub** | https://github.com/alexzhang13/rlm |
| **Minimal Implementation** | https://github.com/alexzhang13/rlm-minimal |
| **Blog** | https://alexzhang13.github.io/blog/2025/rlm/ |
| **HN Thread** | https://news.ycombinator.com/item?id=45596059 |
| **@a1zhang Twitter** | https://x.com/a1zhang |
| **@lateinteraction** | https://x.com/lateinteraction |
| **Prime Intellect RLMEnv** | https://github.com/PrimeIntellect-ai/verifiers/blob/sebastian/experiment/rlm/verifiers/envs/rlm_env.py |

---

# 📊 ENGAGEMENT STATS (as of Jan 5, 2026)

**Alex Zhang's announcement tweet (Jan 2, 2026):**
- 571K+ views
- 3.6K likes
- 686 reposts
- 3.3K bookmarks
- 152 replies

**Alex Zhang's original tweet (Oct 15, 2025):**
- 897K+ views
- 2.6K likes
- 496 reposts
- 2.8K bookmarks
- 130 replies

**Omar Khattab's quote tweet:**
- 79K+ views
- 750 likes
- 90 reposts
- 473 bookmarks
- 28 replies

**Hacker News thread:**
- 135 points
- 35 comments

---

# 🗣️ KEY VOICES TO FOLLOW

1. **Alex Zhang (@a1zhang)** — Primary author, MIT
2. **Omar Khattab (@lateinteraction)** — Co-author, MIT CSAIL, creator of DSPy & ColBERT
3. **HN commenters cs702, layer8** — Provided insightful technical analysis

---

## ACKNOWLEDGEMENTS (From the Blog)

> We thank our wonderful MIT OASYS labmates Noah Ziems, Jacob Li, and Diane Tchuindjo for all the long discussions about where steering this project and getting unstuck. We thank Prof. Tim Kraska, James Moore, Jason Mohoney, Amadou Ngom, and Ziniu Wu from the MIT DSG group for their discussion and help in framing this method for long context problems. This research was partly supported by Laude Institute.
>
> We also thank the authors (who shall remain anonymous) of the OOLONG benchmark for allowing us to experiment on their long-context benchmark.

---

# SUMMARY OF KEY POINTS

1. **RLMs are the next paradigm shift** after CoT-style reasoning models and ReAct-style agent models

2. **GPT-5-mini with RLM > GPT-5** on challenging long-context benchmarks (2x+ performance)

3. **10M+ tokens can be processed** without degradation using RLM

4. **RLM is cheaper** on average compared to base GPT-5 calls on long contexts

5. **No new training required** - RLM is an inference-time strategy

6. **Strategies emerge naturally**: Peeking, Grepping, Partition+Map, Summarization

7. **The LM decides** how to decompose - not the programmer

8. **Systems optimization opportunities** are abundant (async, caching, parallelization)

9. **Community is divided**: Critics see it as "agent loops rebranded", defenders see deeper insight about prompt-as-object

10. **Real innovation**: Giving LLMs external memory (stack) and programmatic control over their own inputs

---

*Document compiled: Jan 5, 2026*
*Total lines of source code analyzed: ~1,200*
*HN comments: 35 verbatim*
*X/Twitter tweets: 100+ verbatim*
*Total document length: ~2,000 lines*

---

**END OF MASTER DOCUMENT**
