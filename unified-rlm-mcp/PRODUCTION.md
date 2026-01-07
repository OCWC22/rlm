# Production Setup Guide

## Quick Start

```bash
# Install dependencies
pnpm install

# Build
pnpm build

# Start server
pnpm start
```

## Testing

### Prerequisites

1. **Install Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

2. **Pull models:**
```bash
# LFM2.5 (NEW Jan 2026!)
ollama pull lfm2.5:1.2b
ollama pull lfm2.5-audio
ollama pull lfm2.5-vl:1.6b

# Qwen 3
ollama pull qwen3:0.6b
ollama pull qwen3:1.7b
ollama pull qwen3:4b
```

3. **Start Ollama:**
```bash
ollama serve
```

### Run Tests

```bash
# Test LFM2.5
pnpm test:lfm

# Test Qwen 3
pnpm test:qwen

# Test all
pnpm test:all
```

## MCP Configuration

### For Cursor

Add to `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "unified-rlm": {
      "command": "node",
      "args": ["/Users/chen/Projects/rlm/unified-rlm-mcp/dist/index.js"],
      "env": {
        "RLM_PROVIDER": "ollama",
        "RLM_MODEL_LOCAL": "ollama/lfm2.5:1.2b",
        "RLM_MODEL_TINY": "ollama/lfm2.5:1.2b",
        "RLM_DEBUG": "false"
      }
    }
  }
}
```

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "unified-rlm": {
      "command": "node",
      "args": ["/Users/chen/Projects/rlm/unified-rlm-mcp/dist/index.js"],
      "env": {
        "RLM_PROVIDER": "ollama",
        "RLM_MODEL_LOCAL": "ollama/qwen3:1.7b"
      }
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RLM_PROVIDER` | `openai` | Provider: `ollama`, `openai`, `anthropic`, etc. |
| `RLM_MODEL_LOCAL` | `ollama/lfm2.5:1.2b` | Default local model |
| `RLM_MODEL_CHEAP` | `deepseek-v3.2` | Cheap API model |
| `RLM_MODEL` | `minimax-m2.1` | Standard model |
| `RLM_MODEL_TINY` | `ollama/lfm2.5:1.2b` | Tiny/edge model |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `RLM_DEBUG` | `false` | Enable debug logging |
| `RLM_MAX_TOKENS` | `500000` | Token budget |
| `RLM_MAX_COST` | `10.00` | Cost budget ($) |

## Production Checklist

- [x] TypeScript compilation
- [x] Proper .gitignore
- [x] Test scripts
- [x] Production build
- [x] MCP configuration examples
- [x] Environment variable documentation
- [x] Error handling
- [x] Budget tracking
- [x] Multi-provider support

## Deployment

### Local Development
```bash
pnpm dev
```

### Production
```bash
pnpm build
pnpm start
```

### Docker (Future)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --prod
COPY dist ./dist
CMD ["node", "dist/index.js"]
```

## Troubleshooting

### Ollama not running
```bash
# Check if running
curl http://localhost:11434/api/tags

# Start if not
ollama serve
```

### Model not found
```bash
# List available models
ollama list

# Pull missing model
ollama pull lfm2.5:1.2b
```

### Port conflicts
```bash
# Change Ollama port
export OLLAMA_URL=http://localhost:11435
```

## Performance Tips

1. **Use LFM2.5 for speed** - 2x faster than competitors
2. **Use Qwen 3 for quality** - Best open-source quality/size ratio
3. **Set tight budgets** - Prevents runaway costs
4. **Use local models** - Zero API costs, full privacy

