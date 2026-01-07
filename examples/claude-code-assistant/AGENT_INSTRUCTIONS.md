# RLM Large File Processing - Agent Instructions

Step-by-step guide for any AI coding agent to process large files using the Recursive Language Model approach.

---

## Overview

**Goal**: Process files too large for LLM context windows (>200K tokens) by chunking, parallel sub-LLM calls, and aggregation.

**Key Files**:
```
examples/claude-code-assistant/
├── deep_rlm_extractor.py     # Recursive extractor with max depth
├── large_file_processor.py   # Generic JSONL/text processor
├── smart_extractor.py        # Two-pass conversation extractor
├── discord_extractor.py      # Discord export processor
├── rlm_context.py            # Core RLM environment
├── HOW_IT_WORKS.md           # Detailed explanation with diagrams
└── README.md                 # Setup guide
```

---

## Step 1: Environment Setup

```bash
# Navigate to project
cd examples/claude-code-assistant

# Set API key (required)
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Verify
echo $ANTHROPIC_API_KEY | head -c 20
```

**Dependencies**:
```bash
pip install anthropic
```

---

## Step 2: Access Cloud Storage (Optional)

If using Cloudflare R2 or S3-compatible storage:

```bash
# Add to ~/.aws/credentials
[r2]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

**List bucket contents**:
```bash
aws s3 ls s3://your-bucket/ \
  --endpoint-url https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com \
  --profile r2 --recursive
```

**Download file**:
```bash
aws s3 cp "s3://your-bucket/path/to/file.json" ./file.json \
  --endpoint-url https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com \
  --profile r2
```

---

## Step 3: Process Large Files

### Option A: Deep RLM Extraction (Recommended)

```bash
python deep_rlm_extractor.py \
    path/to/large-file.json \
    --max-recursion 50 \
    --messages-per-chunk 500 \
    --max-chunks 10 \
    --output report.md
```

**Parameters**:
- `--max-recursion`: Maximum recursion depth (default: 50)
- `--messages-per-chunk`: Messages per chunk (default: 500)
- `--max-chunks`: Limit chunks to process (None = all)
- `--rate-limit`: Seconds between API calls (default: 0.2)
- `--output`: Save report to file

### Option B: Discord Exports (JSON with messages array)

```bash
python discord_extractor.py \
    path/to/discord-export.json \
    --messages-per-chunk 300 \
    --max-chunks 10 \
    --output report.md
```

### Option C: JSONL Files (one JSON per line)

```bash
python large_file_processor.py \
    path/to/file.jsonl \
    "Your query here - what to extract/analyze" \
    --lines-per-chunk 50 \
    --max-chunks 20 \
    --sample 5  # Sample every 5th line
```

### Option D: Two-Pass Smart Extraction

```bash
python smart_extractor.py \
    path/to/conversations.jsonl \
    --max-convs 30 \
    --deep-top-n 10 \
    --output report.md
```

---

## Step 4: Understanding the RLM Flow

```
LARGE FILE (40MB)
       │
       ▼
┌──────────────────┐
│  CHUNK MESSAGES  │  Split into N-message chunks
│  (streaming)     │  Never load full file into memory
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  PARALLEL LLM    │  Send each chunk to Claude Haiku (cheap)
│  CALLS           │  Extract: topics, tools, problems, solutions
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  RECURSIVE       │  Sub-LLMs can call more sub-LLMs
│  DECOMPOSITION   │  Up to max_recursion depth
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  AGGREGATE       │  Combine all chunk results
│  RESULTS         │  Use Claude Sonnet for synthesis
└────────┬─────────┘
         │
         ▼
    FINAL REPORT
```

---

## Step 5: Cost Estimation

| Model | Price | Usage |
|-------|-------|-------|
| Claude 4.5 Haiku | $1/M input, $5/M output | Chunk scanning & recursion |
| Claude Sonnet | $3/M input, $15/M output | Final synthesis |

**Typical costs**:
- 10 chunks (5,000 messages): ~$0.10
- 50 chunks with recursion: ~$0.50
- Full 30K message analysis: ~$0.15

---

## Step 6: Customizing Extractors

### Add new extraction fields

Edit `discord_extractor.py` line ~95, modify the prompt:

```python
prompt = f"""Analyze this chunk of Discord messages...

Extract the following in JSON format:
{{
  "topics": ["topic1", "topic2"],
  "workflows_mentioned": ["workflow1"],
  "YOUR_NEW_FIELD": ["item1", "item2"],  # Add here
}}
"""
```

### Change chunking strategy

Edit `_chunk_messages()` method to chunk by:
- Time periods (daily/weekly)
- Author
- Thread/conversation
- Keyword presence

### Add new file formats

Create new processor based on `discord_extractor.py`:
1. Parse file format in `process_export()`
2. Implement `_format_messages()` for LLM consumption
3. Define extraction schema in `analyze_chunk()`

---

## Step 7: Testing

```bash
# Quick test (2 chunks)
python deep_rlm_extractor.py input.json --max-chunks 2

# Full recursive analysis
python deep_rlm_extractor.py input.json --max-recursion 50 --output full_report.md

# Specific query on JSONL
python large_file_processor.py data.jsonl "Find all error messages" --max-chunks 10
```

---

## Key References

- **RLM Paper**: https://arxiv.org/abs/2512.24601v1
- **Original Repo**: https://github.com/alexzhang13/rlm
- **Prime Intellect RLMEnv**: https://github.com/PrimeIntellect-ai/verifiers/blob/sebastian/experiment/rlm/verifiers/envs/rlm_env.py
- **Documentation**: See `HOW_IT_WORKS.md` for detailed ASCII diagrams

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `ANTHROPIC_API_KEY not set` | `export ANTHROPIC_API_KEY="your-key"` |
| `File too large` | Use chunking with `--max-chunks` |
| `Rate limit exceeded` | Increase `--rate-limit` to 0.5 or higher |
| `JSON parse error` | Check file format, may need different processor |
| `Max tokens exceeded` | Model-specific limits apply (Haiku: 4096) |

---

## Quick Start

```bash
# Setup
cd examples/claude-code-assistant
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Run deep extraction
python deep_rlm_extractor.py your-file.json --max-chunks 10 --output analysis.md

# View results
cat analysis.md
```
