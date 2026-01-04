# 📚 Textbook Q&A with RLM

**A self-contained, intelligent textbook question-answering system** powered by **Recursive Language Models (RLM)**.

This package includes everything you need to run textbook Q&A independently - no external dependencies on the parent RLM repo.

Ask any question about your textbook, and the RLM will:
1. **Search** the entire PDF to find relevant content
2. **Extract** verbatim quotes with page numbers  
3. **Recreate** diagrams using ASCII art
4. **Explain** concepts simply and clearly
5. **Trace** every step for full auditability

---

## 🚀 Quick Start

```bash
# Navigate to this folder
cd examples/textbook-qa

# Install dependencies (if not using parent venv)
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run with a PDF
python textbook_qa.py "books/YourTextbook.pdf" -q "Your question here"
```

---

## 📁 Folder Structure

```
textbook-qa/                          # Self-contained package
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── textbook_qa.py                    # Main Q&A script
├── rlm/                              # Modified RLM core (included)
│   ├── rlm_repl.py                   # RLM REPL engine
│   ├── repl.py                       # REPL environment
│   ├── rlm.py                        # Core RLM
│   ├── logger/                       # Logging utilities
│   └── utils/
│       ├── llm.py                    # Anthropic client + cost tracking
│       ├── prompts.py                # Custom prompts for textbooks
│       └── utils.py                  # Utilities
├── books/                            # Put your PDF textbooks here
│   └── IntroductiontoAlgorithmsFourthEdition.pdf
└── sessions/                         # Conversation history (auto-generated)
    └── YYYY-MM-DD_booktitle/
        ├── 00-index.md               # Index of all Q&A entries
        ├── NN-YYYY-MM-DD-topic.md    # Clean answers
        ├── TRACE-NN-topic.md         # Full execution traces
        └── session.json              # Metadata
```

---

## 💡 Usage Examples

### Basic Question
```bash
python textbook_qa.py "books/algorithms.pdf" -q "What is quicksort?"
```

### With More Iterations (for complex questions)
```bash
python textbook_qa.py "books/algorithms.pdf" -q "Explain binary search trees" --max-iterations 10
```

### With Budget Limit
```bash
python textbook_qa.py "books/algorithms.pdf" -q "What is dynamic programming?" --budget 0.50
```

### Interactive Mode
```bash
python textbook_qa.py "books/algorithms.pdf"
# Then type questions interactively
```

---

## ⚙️ Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `pdf_path` | *required* | Path to the PDF textbook |
| `-q, --query` | *interactive* | Question to ask (skips interactive mode) |
| `--model` | `claude-sonnet-4-5-20250929` | Model to use |
| `--max-iterations` | `10` | Max RLM iterations |
| `--budget` | `1.00` | Max cost in USD |
| `--history-dir` | `sessions/` | Where to save history |
| `--no-history` | `False` | Disable history saving |
| `--no-logging` | `False` | Disable iteration logging |

---

## 📊 Output Files

### Answer Files (`NN-YYYY-MM-DD-topic.md`)

Clean, human-readable answers with:
- 📖 Verbatim quotes from the textbook
- 📄 Clickable page links (file:// URLs)
- 📊 ASCII diagrams recreating figures
- 🧠 Simple explanations
- ✅ Verification checklist

### Trace Files (`TRACE-NN-topic.md`)

Full execution traces for auditing:
- 🤔 RLM's thinking process
- 🔍 Search strategies used
- 📋 Decisions made at each step
- ⚠️ Issues encountered
- 📊 Token usage and cost

---

## 🔗 How Page Links Work

Each answer includes clickable links like:
```markdown
📄 [View Page 420](file:///path/to/book.pdf#page=420)
```

Click to open the PDF at that exact page and verify the quote.

---

## 🧪 How It Works

1. **PDF Loading**: Extracts all text from the PDF
2. **Context Building**: Creates searchable index of all pages
3. **RLM Iteration**: Recursively searches and extracts content
4. **Sub-LLM Calls**: Uses specialized sub-queries for extraction
5. **Verification**: Checks for page numbers and citations
6. **Output**: Generates clean answer + detailed trace

---

## 📈 Cost Tracking

Every query shows:
- Token usage (input/output)
- Number of API calls (root + sub-LLMs)
- Total cost in USD

The `--budget` flag limits spending per query.

---

## 🛠️ Requirements

```bash
# Install dependencies
pip install anthropic pymupdf python-dotenv rich

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"
```

---

## 📝 Example Session

```
📚 Textbook Q&A System
════════════════════════════════════════════════════════════
📖 Book: Introduction to Algorithms (4th Ed)
📄 Pages: 1,677
💰 Budget: $1.00 per query
🔄 Max Iterations: 10

Ask> What is a binary search tree?

[Iteration 1/10] 💰 $0.0512 | 🔄 API: 1 (root: 1)
[Iteration 2/10] 💰 $0.1024 | 🔄 API: 2 (root: 2)
...

════════════════════════════════════════════════════════════
📖 Answer:
...verbatim quotes, diagrams, explanations...
════════════════════════════════════════════════════════════
💾 Saved: 01-2026-01-03-binary-search-tree.md
📋 Trace saved: TRACE-01-binary-search-tree.md
```

---

## 🔍 Supported Models

| Model | Cost (input/output per 1M tokens) |
|-------|-----------------------------------|
| `claude-sonnet-4-5-20250929` | $3.00 / $15.00 |
| `claude-haiku-4-5-20251001` | $0.80 / $4.00 |
| `claude-opus-4-5-20251101` | $15.00 / $75.00 |

---

*Part of the [RLM (Recursive Language Models)](../../README.md) project.*

