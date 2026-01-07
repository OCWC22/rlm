# JSON Explorer

Query massive JSON files with small LLMs using RLM-style recursive exploration.

## Features

- **🔍 RLM-Style Exploration**: Inspect → Decompose → Summarize → Recurse
- **📑 Exhaustive Extraction**: Find EVERY mention with citations (like textbook-qa)
- **📦 Smart Chunking**: Intelligent splitting based on data structure
- **🔗 Multi-Backend Support**: Anthropic, Z.AI (GLM 4.7), OpenAI, Claude Code CLI, Codex CLI
- **💾 Production Storage**: Neon PostgreSQL + Cloudflare R2
- **🔌 MCP Server**: Use as an MCP tool for iOS/web integration
- **📊 Full Tracing**: Deterministic execution traces for debugging
- **✅ Verification**: All answers traceable to source records

## Quick Start

```bash
# Install with storage backends
pip install json-explorer[storage]

# Or install everything
pip install json-explorer[all]
```

### Basic Usage

```python
from json_explorer import JsonExplorer

explorer = JsonExplorer(model="claude-3-haiku-20240307")
explorer.load("/path/to/discord_export.json")

result = explorer.query("What were the main topics discussed?")
print(result.answer)
print(f"Cost: {result.total_tokens} tokens")
```

### Exhaustive Queries with Citations

Find **EVERY** mention of a topic with full citations (like textbook-qa's page references):

```python
from json_explorer import JsonExplorer
from json_explorer.config import ExplorerConfig, TraceLevel

explorer = JsonExplorer(config=ExplorerConfig(
    model="claude-3-haiku-20240307",
    trace_level=TraceLevel.FULL,
))
explorer.load("/path/to/discord_export.json")

# This query triggers EXHAUSTIVE extraction
result = explorer.query(
    "What are people saying about Kling 2.6 for video generation?",
    save_trace=True,
    trace_dir="./traces",
)

# Access the full answer with citations
print(result.answer)

# Check verification (like textbook-qa)
if result.verification:
    print(f"✅ Citations found: {result.verification.citations_found}")
    print(f"✅ Unique authors: {result.verification.unique_authors}")
    print(f"✅ Positive: {result.verification.positive_mentions}")
    print(f"❌ Negative: {result.verification.negative_mentions}")

# Get reference IDs for independent verification
print("Reference IDs:", result.get_reference_ids())

# Get full citation report
if result.citation_report:
    print(result.citation_report.to_markdown())
```

**Exhaustive queries automatically trigger when you ask:**
- "What are people saying about X?"
- "Everything about X"
- "All mentions of X"
- "Every single instance of X"
- "Comprehensive analysis of X"

Each citation includes:
- **Exact quote** from the source
- **Author** (username/name)
- **Timestamp**
- **Channel/thread** (if applicable)
- **Reference ID** for verification (e.g., `3.15` = chunk 3, record 15)
- **Sentiment** (positive/negative/neutral)
- **Context** (what was discussed before/after)

## LLM Backends

### 1. Anthropic API (Default)

```python
from json_explorer import JsonExplorer

explorer = JsonExplorer(
    model="claude-3-haiku-20240307",
    # Uses ANTHROPIC_API_KEY env var
)
```

### 2. Z.AI (GLM 4.7 - Recommended)

Use [Z.AI](https://z.ai) for access to GLM 4.7 through an Anthropic-compatible API:

```bash
export Z_AI_API_KEY="your_zai_key"
```

```python
from json_explorer import JsonExplorer
from json_explorer.config import ExplorerConfig, AdapterType

config = ExplorerConfig(
    adapter_type=AdapterType.ZAI,
    model="glm-4.7",  # Best model for thorough analysis
    # model="glm-4.5-air",  # Fast model for quick queries
)
explorer = JsonExplorer(config=config)
```

**Available Z.AI Models:**
| Model | Use Case |
|-------|----------|
| `glm-4.7` | Best quality - thorough analysis, exhaustive extraction |
| `glm-4.5-air` | Fast - high volume queries, quick summaries |

Or use presets:

```python
from json_explorer.config import get_preset

# Fast queries with GLM-4.5-Air
explorer = JsonExplorer(config=get_preset("zai_fast"))

# Thorough analysis with GLM-4.7
explorer = JsonExplorer(config=get_preset("zai_thorough"))
```

**For Claude Code integration:**

```bash
# Configure Claude Code to use Z.AI
export ANTHROPIC_AUTH_TOKEN="your_zai_key"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export API_TIMEOUT_MS="3000000"

# Add Zread MCP for citations from open-source repos
claude mcp add -s user -t http zread https://api.z.ai/api/mcp/zread/mcp --header "Authorization: Bearer your_zai_key"
```

### 3. Claude Code CLI

Use [Claude Code](https://docs.anthropic.com/en/docs/claude-code/) CLI:

```bash
npm install -g @anthropic-ai/claude-code
```

```python
from json_explorer.adapters import ClaudeCodeAdapter, AdapterConfig, AdapterType

config = AdapterConfig(
    adapter_type=AdapterType.CLAUDE_CODE,
    working_dir="/path/to/project",
)
adapter = ClaudeCodeAdapter(config)
result = adapter.complete("Analyze this JSON structure")
```

### 4. OpenAI Codex CLI

Use [Codex CLI](https://developers.openai.com/codex) with GPT-5, o3, o3-mini:

```bash
npm install -g @openai/codex
codex login
```

```python
from json_explorer.adapters import CodexAdapter, AdapterConfig, AdapterType

config = AdapterConfig(
    adapter_type=AdapterType.CODEX,
    model="gpt-5",
    sandbox_mode="read-only",
)
adapter = CodexAdapter(config)
result = adapter.complete("What does this function do?")
```

### 5. Generic MCP Server

Connect to any MCP server:

```python
from json_explorer.adapters import MCPAdapter, AdapterConfig, AdapterType

config = AdapterConfig(
    adapter_type=AdapterType.MCP,
    mcp_server_url="https://api.example.com/mcp",
    mcp_headers={"Authorization": "Bearer your_key"},
)
adapter = MCPAdapter(config)
```

## Storage Backends

### Neon PostgreSQL (Caching)

Use [Neon](https://neon.tech) for serverless PostgreSQL caching:

```bash
export NEON_DATABASE_URL="postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/db?sslmode=require"
```

```python
from json_explorer.storage import NeonStorage

async with NeonStorage() as storage:
    # Cache query results
    await storage.cache_set(
        key="query_hash",
        value="result",
        file_hash="file_sha256",
        ttl=3600,  # 1 hour
    )
    
    # Get cached result
    result = await storage.cache_get("query_hash")
    
    # Save execution trace
    await storage.trace_save(
        trace_id="trace_001",
        session_id="session_001",
        query="What topics were discussed?",
        trace_json={"events": [...]},
        tokens_used=1500,
    )
```

### Cloudflare R2 (File Storage)

Use [Cloudflare R2](https://developers.cloudflare.com/r2/) for file storage:

```bash
export CLOUDFLARE_R2_ACCOUNT_ID="your_account_id"
export CLOUDFLARE_R2_ACCESS_KEY_ID="your_access_key"
export CLOUDFLARE_R2_SECRET_ACCESS_KEY="your_secret_key"
export CLOUDFLARE_R2_BUCKET_NAME="your_bucket"
```

```python
from json_explorer.storage import R2Storage

storage = R2Storage()

# Upload file
key = storage.upload_file(
    "/path/to/large_export.json",
    content_addressable=True,  # Use content hash as key
)

# Stream download (memory efficient)
for chunk in storage.download_stream(key):
    process(chunk)

# Generate presigned URL for external access
url = storage.generate_presigned_url(key, expires_in=3600)
```

### Production Configuration

```python
from json_explorer.config import get_preset

# Use production preset with Neon + R2
config = get_preset("production")
explorer = JsonExplorer(config=config)
```

## MCP Server

Run JSON Explorer as an MCP server for iOS/web:

```bash
# MCP mode (stdio)
json-explorer --mode mcp

# HTTP mode (REST API)
json-explorer --mode http --port 8080
```

### Claude Code MCP Configuration

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "json-explorer": {
      "type": "stdio",
      "command": "json-explorer",
      "args": ["--mode", "mcp"]
    }
  }
}
```

### Available MCP Tools

- `load_json` - Load a JSON file
- `analyze_schema` - Get schema information
- `query` - Ask a question about the data
- `get_sample` - Get sample records
- `get_trace` - Get execution trace

## Presets

| Preset | Description |
|--------|-------------|
| `fast` | Claude Haiku, minimal tracing, 8 parallel chunks |
| `balanced` | Claude Haiku, summary tracing, 4 parallel chunks |
| `thorough` | Claude Sonnet, full tracing, 2 parallel chunks |
| `budget` | Limited tokens and chunks for cost control |
| `zai_fast` | Z.AI GLM-4.5-Air, minimal tracing |
| `zai_thorough` | Z.AI GLM-4.7, full tracing |
| `production` | Neon + R2, 24hr cache, full tracing |
| `claude_code` | Claude Code CLI adapter |
| `codex` | Codex CLI with GPT-5 |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `Z_AI_API_KEY` | Z.AI API key |
| `OPENAI_API_KEY` | OpenAI API key (for Codex) |
| `NEON_DATABASE_URL` | Neon PostgreSQL connection string |
| `CLOUDFLARE_R2_ACCOUNT_ID` | Cloudflare account ID |
| `CLOUDFLARE_R2_ACCESS_KEY_ID` | R2 access key |
| `CLOUDFLARE_R2_SECRET_ACCESS_KEY` | R2 secret key |
| `CLOUDFLARE_R2_BUCKET_NAME` | R2 bucket name |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     JSON Explorer                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Schema  │→ │  Query    │→ │ Executor │→ │ Aggregator │  │
│  │Analyzer │  │  Planner  │  │ (Chunks) │  │  (Reduce)  │  │
│  └─────────┘  └───────────┘  └──────────┘  └────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                       Adapters                               │
│  ┌──────────┐ ┌─────┐ ┌────────────┐ ┌───────┐ ┌─────────┐ │
│  │Anthropic │ │Z.AI │ │Claude Code │ │Codex  │ │   MCP   │ │
│  └──────────┘ └─────┘ └────────────┘ └───────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│                       Storage                                │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │  Neon PostgreSQL    │  │     Cloudflare R2           │  │
│  │  (Cache + Sessions) │  │     (File Storage)          │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Modular Analysis Framework

The analysis framework provides **pluggable analyzers** for different domains. Use built-in analyzers or create your own.

### CLI Usage

```bash
# Marketing analysis
python analyze.py export.json --analyzer marketing

# Multiple analyzers
python analyze.py export.json --analyzer marketing product support

# All built-in analyzers
python analyze.py export.json --all

# Analyze specific topic
python analyze.py export.json --topic "Kling 2.6 video generation"

# Quick single query
python analyze.py export.json --query "What are people saying about pricing?"

# Custom analyzer from YAML
python analyze.py export.json --custom my_analysis.yaml

# Create template for custom analyzer
python analyze.py --create-template my_analysis.yaml
```

### Built-in Analyzers

| Analyzer | Description |
|----------|-------------|
| `marketing` | Product sentiment, competitors, feature requests, pricing |
| `product` | Feature usage, bugs, user journey, integrations |
| `support` | FAQs, documentation gaps, troubleshooting, self-service |
| `research` | Themes, behaviors, mental models, terminology |
| `sentiment` | Overall sentiment, influencers, trust signals, NPS |

### Python API

```python
from json_explorer import (
    JsonExplorer, ExplorerConfig,
    AnalysisPipeline,
    MarketingAnalyzer,
    ProductAnalyzer,
    SupportAnalyzer,
)

# Create explorer and load data
explorer = JsonExplorer()
explorer.load("/path/to/discord_export.json")

# Create pipeline with multiple analyzers
pipeline = AnalysisPipeline(explorer)
pipeline.add_analyzer(MarketingAnalyzer())
pipeline.add_analyzer(ProductAnalyzer())
pipeline.add_analyzer(SupportAnalyzer())

# Run analysis
reports = pipeline.run()

# Save reports
pipeline.save_reports("./reports")
# Creates:
#   ./reports/SUMMARY.md
#   ./reports/marketing.md
#   ./reports/product.md
#   ./reports/support.md
```

### Topic-Specific Analysis

Analyze any topic in depth:

```python
from json_explorer.analysis.research import TopicAnalyzer

# Analyze a specific topic
analyzer = TopicAnalyzer(topic="Kling 2.6 video generation")
report = analyzer.run(explorer)

print(report.to_markdown())
```

### Custom Analyzers

#### Option 1: YAML Configuration

Create `my_analysis.yaml`:

```yaml
name: my_custom_analysis
description: My Custom Analysis

questions:
  - id: main_themes
    question: What are the main themes discussed?
    description: Theme Discovery
    category: discovery
    priority: 1

  - id: sentiment
    question: What is the overall sentiment?
    description: Sentiment Analysis
    category: sentiment
    priority: 2
```

Run it:

```bash
python analyze.py export.json --custom my_analysis.yaml
```

#### Option 2: Python Code

```python
from json_explorer.analysis import (
    BaseAnalyzer,
    AnalysisQuestion,
    AnalysisCategory,
)

class MyAnalyzer(BaseAnalyzer):
    name = "my_analyzer"
    description = "My Custom Analysis"
    
    questions = [
        AnalysisQuestion(
            id="patterns",
            question="What patterns exist in this data?",
            description="Pattern Discovery",
            category=AnalysisCategory.DISCOVERY,
            priority=1,
        ),
        AnalysisQuestion(
            id="issues",
            question="What problems are people having?",
            description="Issue Analysis",
            category=AnalysisCategory.SENTIMENT,
            priority=2,
        ),
    ]

# Use it
analyzer = MyAnalyzer()
report = analyzer.run(explorer)
```

### Analysis Categories

| Category | Purpose |
|----------|---------|
| `SENTIMENT` | Opinion, emotion, tone |
| `DISCOVERY` | Finding patterns, themes |
| `QUANTITATIVE` | Counting, measuring |
| `QUALITATIVE` | Deep understanding |
| `COMPARISON` | Comparing things |
| `TEMPORAL` | Time-based analysis |
| `CUSTOM` | Everything else |

### Quick Single Query

For one-off questions:

```python
from json_explorer.analysis.custom import QuickAnalyzer

analyzer = QuickAnalyzer(
    question="What are people saying about the new pricing model?"
)
report = analyzer.run(explorer)
print(report.results[0].answer)
```

### Output Structure

After running `pipeline.save_reports("./reports")`:

```
./reports/
├── SUMMARY.md          # Executive summary with key findings
├── marketing.md        # Full marketing analysis
├── marketing.json      # Machine-readable format
├── product.md          # Product analysis
├── product.json
├── support.md
├── support.json
└── traces/             # Execution traces for debugging
    ├── marketing_product_sentiment.trace.json
    └── ...
```

## 📱 Use Case Examples

- **Marketing Teams**: Sentiment analysis, competitor monitoring, feature requests
- **Product Teams**: Bug triage, feature prioritization, user journey analysis
- **Support Teams**: FAQ generation, documentation gaps, common issues
- **Research Teams**: Theme extraction, behavior analysis, terminology
- **Anyone**: Custom analyses via YAML or Python

See [USE_CASE_MARKETERS.md](USE_CASE_MARKETERS.md) for a detailed marketing use case.

## License

MIT
