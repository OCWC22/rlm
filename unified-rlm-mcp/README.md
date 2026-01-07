# Unified RLM MCP v2.1

> **Infinite context + infinite reasoning for ANY model**
> 
> Focused on **SMALL models (1B-8B)** for on-device + cheap API options

## 🎯 Target: Small Models That Work

This MCP server is optimized for:
- **On-device models**: 350M to 8B parameters via Ollama
- **Cheap API models**: DeepSeek V3.2 at $0.027/1M tokens
- **Budget-aware**: Auto-switches to cheaper models when budget is low

## Supported Models (January 2026)

### 📱 LOCAL via Ollama (FREE)

| Model Family | Sizes | Context | Best For |
|--------------|-------|---------|----------|
| **Qwen 3** | 0.6B, 1.7B, 4B, 8B | 32K | General reasoning |
| **Qwen 2.5 Coder** | 3B, 7B | 32K | Coding |
| **DeepSeek R1** | 1.5B, 7B, 8B | 128K | Reasoning |
| **LFM2** | 350M, 700M, 1.2B, 2.6B, 8B | 32-125K | **FASTEST on-device** |
| **Nemotron 3 Nano** | ~4B | 32K | Agentic tasks |
| **Phi-4** | 3.8B, 14B | 16K | Reasoning |
| **Gemma 3** | 1B, 4B, 270M | 8K | Function calling |
| **Llama 3.3** | 3B, 8B | 128K | General |
| **SmolLM2** | 135M, 360M, 1.7B | 8K | Edge devices |

### 💰 CHEAP APIs

| Model | Input | Output | Context | Notes |
|-------|-------|--------|---------|-------|
| **DeepSeek V3.2** | $0.027/1M | $0.11/1M | 64K | **CHEAPEST!** |
| **DeepSeek V3** | $0.14/1M | $0.28/1M | 64K | Great value |
| **MiniMax M2.1** | $0.12/1M | $0.48/1M | 196K | 10B active, coding |
| **GLM-4.7** | $0.50/1M | $2.00/1M | 200K | $3/mo plan, coding |
| **GPT-4o-mini** | $0.15/1M | $0.60/1M | 128K | OpenAI ecosystem |
| **Claude Haiku 4.5** | $0.25/1M | $1.25/1M | 200K | Anthropic |
| **Gemini 2.5 Flash** | $0.15/1M | $0.60/1M | 1M | Huge context |

## Quick Start

```bash
cd unified-rlm-mcp
pnpm install
pnpm build
```

### For LOCAL (FREE - No API!)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull small models
ollama pull qwen3:4b          # Best quality/size
ollama pull lfm2:1.2b         # Fastest on-device
ollama pull deepseek-r1:1.5b  # Reasoning
ollama pull smollm2:360m      # Tiny edge devices
```

MCP Config:
```json
{
  "mcpServers": {
    "rlm": {
      "command": "node",
      "args": ["/path/to/unified-rlm-mcp/dist/index.js"],
      "env": {
        "RLM_PROVIDER": "ollama",
        "RLM_MODEL_LOCAL": "ollama/qwen3:4b",
        "RLM_MODEL_TINY": "ollama/lfm2:1.2b",
        "RLM_DEBUG": "true"
      }
    }
  }
}
```

### For Cheap APIs

```json
{
  "mcpServers": {
    "rlm": {
      "command": "node",
      "args": ["/path/to/unified-rlm-mcp/dist/index.js"],
      "env": {
        "DEEPSEEK_API_KEY": "sk-...",
        "MINIMAX_API_KEY": "...",
        "ZHIPU_API_KEY": "...",
        "RLM_MODEL_CHEAP": "deepseek-v3.2",
        "RLM_MODEL": "minimax-m2.1",
        "RLM_DEBUG": "true"
      }
    }
  }
}
```

## Just 2 Tools

### `rlm` - Process Anything

| Mode | Description |
|------|-------------|
| `ingest` | Store data externally |
| `chunk` | Split large data |
| `process` | Recursive LLM call |
| `search` | Find in data |
| `synthesize` | Combine results |
| `think` | Structured reasoning |
| `models` | List all models + pricing |

### `state` - Persistent Memory

| Op | Description |
|----|-------------|
| `get/set` | Key-value storage |
| `list` | List keys |
| `budget` | Check/set limits |
| `reset` | Clear session |

## Model Tiers

The server automatically selects models based on budget:

| Tier | Default | When Used |
|------|---------|-----------|
| `cheap` | deepseek-v3.2 | Bulk processing |
| `standard` | minimax-m2.1 | Normal tasks |
| `premium` | claude-sonnet-4.5 | Synthesis |
| `local` | ollama/qwen3:4b | On-device |
| `tiny` | ollama/lfm2:1.2b | Edge devices |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI |
| `ANTHROPIC_API_KEY` | - | Anthropic |
| `GOOGLE_API_KEY` | - | Google |
| `DEEPSEEK_API_KEY` | - | DeepSeek |
| `ZHIPU_API_KEY` / `ZAI_API_KEY` | - | Z.AI GLM |
| `MINIMAX_API_KEY` | - | MiniMax |
| `XAI_API_KEY` | - | xAI Grok |
| `RLM_PROVIDER` | `openai` | Default provider |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server |
| `RLM_MODEL` | `minimax-m2.1` | Standard model |
| `RLM_MODEL_CHEAP` | `deepseek-v3.2` | Cheap model |
| `RLM_MODEL_LOCAL` | `ollama/qwen3:4b` | Local model |
| `RLM_MODEL_TINY` | `ollama/lfm2:1.2b` | Tiny model |
| `RLM_MAX_TOKENS` | `500000` | Token budget |
| `RLM_MAX_COST` | `10.00` | Cost budget ($) |

## Example: Process 50MB with $1 Budget

```
# 1. Set tight budget
state(op: "budget", budget: { maxCost: 1.0 })

# 2. Ingest large file
rlm(mode: "ingest", data: <json>, name: "discord")

# 3. Chunk it
rlm(mode: "chunk", inputPath: "...", chunkSize: 10000)

# 4. Process with cheapest model
for each chunk:
  rlm(mode: "process", 
      prompt: "Extract key points",
      contextPaths: [chunk],
      model: "deepseek-v3.2")  # $0.027/1M!

# 5. Synthesize
rlm(mode: "synthesize",
    task: "Create summary",
    resultPaths: [...],
    model: "minimax-m2.1")

# 6. Check budget
state(op: "budget")
→ { used: { cost: "$0.45" }, ok: true }
```

## On-Device Recommendations

### For MacBook (M1/M2/M3)
- **Best quality**: `ollama/qwen3:8b` or `ollama/llama3.3:8b`
- **Best speed**: `ollama/lfm2:2.6b` (2x faster than others)
- **Best reasoning**: `ollama/deepseek-r1:8b`

### For Edge/Mobile
- **Tiny**: `ollama/smollm2:360m` (200MB)
- **Small**: `ollama/lfm2:1.2b` (800MB)
- **Balanced**: `ollama/qwen3:1.7b` (1GB)

### For Raspberry Pi / Low-End
- **Minimum**: `ollama/smollm2:135m` (100MB)
- **Better**: `ollama/functiongemma` (270M, function calling)

## Why These Models?

### Qwen 3 (Alibaba)
- Best open-source quality for size
- Hybrid thinking/non-thinking modes
- 0.6B to 235B parameter range

### LFM2 (Liquid AI)
- **2x faster** prefill/decode than competitors
- Optimized for on-device with hybrid architecture
- 350M to 8B MoE (1.5B active)

### DeepSeek R1
- Reasoning model with chain-of-thought
- Distilled versions run locally
- 1.5B to 671B

### GLM-4.7 (Z.AI)
- 355B params, 32B active (MoE)
- Preserved thinking across conversations
- $3/month coding plan!

### MiniMax M2.1
- 10B active parameters
- Excellent for agentic coding
- $0.12/1M input tokens

## License

MIT
