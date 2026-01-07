# Test Suite

## Prerequisites

1. Ollama installed and running
2. Models pulled (see below)

## Setup

```bash
# Start Ollama
ollama serve

# Pull required models
ollama pull lfm2.5:1.2b
ollama pull qwen3:1.7b
```

## Run Tests

```bash
# Individual tests
pnpm test:lfm    # Test LFM2.5
pnpm test:qwen   # Test Qwen 3

# All tests
pnpm test:all
```

## What Tests Cover

- ✅ Model listing
- ✅ Data ingestion
- ✅ LLM processing
- ✅ Search functionality
- ✅ Reasoning/thinking
- ✅ Budget tracking
- ✅ State management

## Expected Output

Tests should show:
- Model discovery
- Successful data ingestion
- LLM responses
- Budget tracking (should be $0 for local models)
- No errors

