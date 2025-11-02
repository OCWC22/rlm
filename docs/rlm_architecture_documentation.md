# RLM Recursive Language Model Architecture Documentation

## Overview

The RLM (Recursive Language Model) is a sophisticated system that processes large contexts through a divide-and-conquer approach using a REPL (Read-Eval-Print Loop) environment. The architecture enables iterative processing of complex queries by orchestrating multiple language model interactions in a sandboxed execution environment.

## Core Architecture Flow

### 1. Main RLM Query Processing Loop

The system processes user queries through an iterative loop that coordinates between the root LM and REPL environment.

**Entry Point:**
```python
# File: main.py
query = "I'm looking for a magic number. What is it?"
result = rlm.completion(context=context, query=query)
```

**Core Processing Loop:**
```python
# File: rlm/rlm_repl.py (line 84)
for iteration in range(self._max_iterations):
    response = self.llm.completion(self.messages + [next_action_prompt(query, iteration)])
    if final_answer:
        # Terminate when final answer is found
```

**Key Components:**
- **Root LM Query**: Orchestrates iterative REPL interactions to process large contexts
- **Iterative Processing**: Continues until a final answer is found or max iterations reached
- **Termination Logic**: Checks for completion signals and extracts final answers

### 2. REPL Environment Context Initialization

The system sets up a sandboxed execution environment with context data and sub-LM access.

**Context Conversion:**
```python
# File: rlm/rlm_repl.py (line 66)
context_data, context_str = utils.convert_context_for_repl(context)
```

**Environment Creation:**
```python
# File: rlm/rlm_repl.py (line 68)
self.repl_env = REPLEnv(context_json=context_data, context_str=context_str, recursive_model=self.recursive_model)
```

**Context Loading:**
```python
# File: rlm/repl.py (line 200)
if context_json is not None:
    # Loads structured context into temporary file
```

**Sub-RLM Initialization:**
```python
# File: rlm/repl.py (line 87)
self.sub_rlm: RLM = Sub_RLM(model=recursive_model)
```

**Key Features:**
- **Sandboxed Environment**: Isolated execution space for code processing
- **Context Integration**: Converts and loads input context for REPL access
- **Sub-LM Access**: Creates recursive sub-LM for chunk processing

### 3. Code Execution and REPL Processing Pipeline

Extracts and executes Python code blocks from LM responses in the sandboxed environment.

**Code Block Detection:**
```python
# File: rlm/rlm_repl.py (line 90)
code_blocks = utils.find_code_blocks(response)
```

**REPL Block Pattern:**
```python
# File: rlm/utils/utils.py (line 13)
pattern = r'```repl\s*\n(.*?)\n```'
```

**Code Execution:**
```python
# File: rlm/utils/utils.py (line 174)
execution_result = execute_code(repl_env, code, repl_env_logger, logger)
```

**Main Executor:**
```python
# File: rlm/repl.py (line 264)
def code_execution(self, code) -> REPLResult:
    # Main sandboxed code execution method
```

**Result Integration:**
```python
# File: rlm/utils/utils.py (line 177)
messages = add_execution_result_to_messages(messages, code, execution_result)
```

**Key Capabilities:**
- **Code Extraction**: Identifies executable code blocks using regex patterns
- **Sandboxed Execution**: Runs code in isolated REPL environment
- **Result Integration**: Adds execution results back to conversation context

### 4. Recursive Sub-LM Integration for Context Chunking

Sub-LMs process large context chunks through recursive queries within the REPL environment.

**LLM Query Function:**
```python
# File: rlm/repl.py (line 169)
def llm_query(prompt: str) -> str:
    return self.sub_rlm.completion(prompt)
```

**Function Registration:**
```python
# File: rlm/repl.py (line 174)
self.globals['llm_query'] = llm_query
```

**Sub-LM API Call:**
```python
# File: rlm/repl.py (line 31)
response = self.client.completion(messages=prompt, timeout=300)
```

**Capability Documentation:**
```python
# File: rlm/utils/prompts.py (line 14)
A `llm_query` function that allows you to query an LLM (that can handle around 500K chars) inside your REPL environment.
```

**Key Features:**
- **Recursive Processing**: Sub-LMs can handle large context chunks (~500K characters)
- **REPL Integration**: `llm_query` function available within REPL environment
- **Hierarchical Architecture**: Root LM orchestrates, sub-LMs process chunks

### 5. Completion Detection and Answer Extraction

Identifies completion signals and extracts final answers from REPL variables.

**Final Answer Check:**
```python
# File: rlm/rlm_repl.py (line 105)
final_answer = utils.check_for_final_answer(response, self.repl_env, self.logger)
```

## System Components and Responsibilities

### Core Classes

#### RLM_REPL (Main Orchestrator)
- **Location**: `rlm/rlm_repl.py`
- **Purpose**: Main entry point for recursive processing
- **Key Methods**:
  - `completion(context, query)`: Main processing method
  - `setup_context(context)`: Initializes REPL environment
  - Iterative processing loop with termination logic

#### REPLEnv (Sandboxed Environment)
- **Location**: `rlm/repl.py`
- **Purpose**: Provides isolated execution environment
- **Key Methods**:
  - `code_execution(code)`: Executes code blocks
  - Context loading and management
  - Sub-LM integration

#### Sub_RLM (Recursive Processor)
- **Location**: `rlm/repl.py`
- **Purpose**: Handles large context chunk processing
- **Capabilities**: Processes ~500K character contexts

### Utility Modules

#### Utils (`rlm/utils/utils.py`)
- **Code Block Detection**: `find_code_blocks()` - Identifies executable code
- **Code Execution**: `execute_code()` - Runs code in sandbox
- **Message Management**: `add_execution_result_to_messages()`
- **Answer Detection**: `check_for_final_answer()`

#### Prompts (`rlm/utils/prompts.py`)
- **System Prompts**: Guides LM behavior and capabilities
- **Action Prompts**: `next_action_prompt()` - Guides iterative processing
- **Documentation**: Explains available functions and limits

#### LLM Interface (`rlm/utils/llm.py`)
- **Client Management**: Handles API communication
- **Timeout Management**: 300-second timeout for sub-LM calls
- **Message Processing**: Formats and sends requests to LLM

## Data Flow and Processing

### Input Processing
1. **Context Conversion**: Raw context → REPL-compatible format
2. **Environment Setup**: Create sandboxed REPL with context
3. **Initial Query**: Root LM receives user query and context

### Iterative Processing
1. **LM Query**: Root LM decides next action
2. **Code Extraction**: Identify and extract REPL code blocks
3. **Execution**: Run code in sandboxed environment
4. **Result Integration**: Add execution results to conversation
5. **Termination Check**: Evaluate if final answer is achieved

### Recursive Processing
1. **Chunk Detection**: Large contexts identified for sub-LM processing
2. **Sub-LM Calls**: `llm_query()` function invoked within REPL
3. **Chunk Processing**: Sub-LM processes ~500K character chunks
4. **Result Aggregation**: Combine sub-LM results with main processing

### Output Generation
1. **Final Answer Detection**: Identify completion signals
2. **Answer Extraction**: Extract results from REPL variables
3. **Response Formatting**: Format and return final answer

## Key Design Decisions and Trade-offs

### Architectural Choices

#### REPL-Based Processing
- **Decision**: Use sandboxed REPL environment for code execution
- **Rationale**: Provides isolation, flexibility, and dynamic code execution
- **Trade-off**: Adds complexity but enables powerful processing capabilities

#### Recursive Architecture
- **Decision**: Hierarchical LM structure with root and sub-LMs
- **Rationale**: Enables processing of contexts larger than single LM limits
- **Trade-off**: Increased coordination overhead vs. linear scaling

#### Iterative Processing
- **Decision**: Loop-based approach with termination conditions
- **Rationale**: Allows adaptive processing based on query complexity
- **Trade-off**: Potential for infinite loops (mitigated by max iterations)

### Security and Safety

#### Sandbox Isolation
- **Implementation**: Separate execution environment for code
- **Protection**: Prevents malicious code from affecting main system
- **Limitations**: Resource constraints and timeout mechanisms

#### Input Validation
- **Code Block Detection**: Regex-based identification of executable code
- **Context Sanitization**: Conversion and validation of input contexts
- **Timeout Management**: 300-second limits on LLM calls

## Performance Characteristics

### Scalability
- **Context Handling**: ~500K characters per sub-LM call
- **Parallel Processing**: Potential for concurrent sub-LM execution
- **Memory Management**: Chunked processing to handle large contexts

### Reliability
- **Error Handling**: Comprehensive error catching and logging
- **Timeout Protection**: Prevents hanging on long-running operations
- **Graceful Degradation**: Fallback mechanisms for failed operations

### Extensibility
- **Modular Design**: Clear separation of concerns
- **Plugin Architecture**: Easy addition of new processing capabilities
- **Configuration**: Adjustable parameters for different use cases

## Usage Examples

### Basic Usage
```python
from rlm import RLM

# Initialize RLM with model configuration
rlm = RLM(model="your-model-name")

# Process query with context
context = {"data": "your context data"}
query = "What insights can you derive from this data?"
result = rlm.completion(context=context, query=query)
```

### Advanced Usage with Custom Processing
```python
# The system automatically handles:
# - Large context chunking
# - Code execution in sandbox
# - Recursive processing
# - Result aggregation

# Users can include REPL code blocks in their prompts:
prompt = """
```repl
# Process the data chunk
result = llm_query("Analyze this data: " + str(data_chunk))
print(result)
```
"""
```

## File Structure and Locations

```
rlm/
├── main.py                    # Entry point and usage examples
├── rlm/
│   ├── __init__.py           # Package initialization
│   ├── rlm_repl.py           # Main RLM orchestrator class
│   ├── repl.py               # REPL environment and sub-LM
│   ├── logger/               # Logging utilities
│   │   ├── __init__.py
│   │   ├── repl_logger.py
│   │   └── root_logger.py
│   └── utils/                # Utility modules
│       ├── __init__.py
│       ├── llm.py           # LLM client interface
│       ├── prompts.py       # System and action prompts
│       └── utils.py         # Code execution and processing utilities
└── docs/                     # Documentation (this file)
    └── rlm_architecture_documentation.md
```

## Dependencies and Requirements

### Core Dependencies
- **Language Model Client**: For API communication with LLM services
- **Python Execution Environment**: For REPL sandbox functionality
- **JSON Processing**: For context data handling
- **Regex Processing**: For code block detection

### System Requirements
- **Memory**: Sufficient for large context processing (~500K chars per sub-LM)
- **Network**: Access to LLM API endpoints
- **Storage**: Temporary files for context and execution data

## Future Enhancements and Extensibility

### Potential Improvements
1. **Parallel Sub-LM Execution**: Concurrent processing of multiple chunks
2. **Enhanced Security**: More sophisticated sandboxing mechanisms
3. **Performance Optimization**: Caching and memoization strategies
4. **Monitoring**: Detailed metrics and performance tracking
5. **Custom Executors**: Support for different execution environments

### Extension Points
1. **Custom Prompt Templates**: Domain-specific prompt engineering
2. **Alternative LLM Backends**: Support for different model providers
3. **Advanced Code Execution**: Support for multiple programming languages
4. **Context Preprocessing**: Custom context transformation pipelines

This architecture provides a robust, scalable foundation for processing complex queries through recursive language model interactions while maintaining security, reliability, and extensibility.
