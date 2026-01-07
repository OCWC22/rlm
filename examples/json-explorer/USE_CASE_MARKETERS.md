# 📊 JSON Explorer for Marketers: Discord Community Intelligence

> **Use Case**: Analyze Discord community exports to extract marketing insights, customer sentiment, and product feedback - without technical expertise.

## The Problem

Marketers managing Discord communities face a common challenge:

- **Data overload**: Thousands of messages across dozens of channels
- **Manual analysis is slow**: Reading every message is impossible
- **Missing insights**: Important feedback gets buried
- **No citation trail**: Hard to reference specific conversations

**Traditional solutions fail because:**
- ChatGPT/Claude can't handle 500MB+ exports
- Searching keywords misses context and nuance
- Summarization loses important details

## The RLM Solution

JSON Explorer uses **Recursive Language Model** techniques to:

1. **Inspect** the data structure automatically
2. **Decompose** into manageable chunks
3. **Summarize** each chunk with citations
4. **Recurse** to find every relevant mention

**Result**: Find EVERY mention of a topic with full context and citations.

---

## 🎯 Marketer Use Cases

### 1. Product Sentiment Analysis

> "What are people saying about our new feature X?"

```python
result = explorer.query("What are people saying about the dashboard redesign?")
```

**Output includes:**
- All positive feedback with usernames
- All complaints with context
- Feature requests mentioned
- Comparison to competitors
- Reference IDs to find original messages

### 2. Competitive Intelligence

> "What are community members saying about competitor products?"

```python
result = explorer.query("What are people saying about Competitor XYZ vs our product?")
```

### 3. Customer Pain Points

> "What problems are users reporting?"

```python
result = explorer.query("What bugs, issues, or frustrations are users mentioning?")
```

### 4. Feature Requests

> "What features are users asking for?"

```python
result = explorer.query("What features or improvements are people requesting?")
```

### 5. Influencer/Champion Identification

> "Who are our most engaged community advocates?"

```python
result = explorer.query("Who are the most helpful users answering questions?")
```

### 6. Campaign Feedback

> "How did the community react to our launch?"

```python
result = explorer.query("What are people saying about the product launch announcement?")
```

---

## 🚀 Quick Start for Marketers

### Step 1: Export Discord Data

1. Go to Discord → User Settings → Privacy & Safety
2. Request your data (or use a community export tool)
3. Download the JSON export

### Step 2: Set Up JSON Explorer

```bash
# Install
pip install json-explorer[all]

# Set API key (get from z.ai for best results)
export Z_AI_API_KEY="your_key_here"
```

### Step 3: Analyze Your Community

```python
from json_explorer import JsonExplorer
from json_explorer.config import get_preset

# Use GLM 4.7 for best analysis
explorer = JsonExplorer(config=get_preset("zai_thorough"))

# Load your Discord export
explorer.load("/path/to/discord_export.json")

# Ask marketing questions
result = explorer.query(
    "What are people saying about our pricing?",
    save_trace=True,  # Save full audit trail
)

# Get results
print(result.answer)

# Check how many mentions were found
print(f"Found {result.verification.citations_found} mentions")
print(f"From {result.verification.unique_authors} unique users")
```

---

## 📋 Sample Marketing Analysis Session

```python
#!/usr/bin/env python3
"""
Discord Community Analysis for Marketing
========================================

Analyze a Discord export to extract marketing intelligence.
"""

from json_explorer import JsonExplorer
from json_explorer.config import get_preset
import json
from pathlib import Path

def analyze_discord_community(export_path: str, output_dir: str = "./reports"):
    """
    Complete marketing analysis of a Discord community.
    
    Args:
        export_path: Path to Discord JSON export
        output_dir: Where to save reports
    """
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize explorer with thorough analysis
    explorer = JsonExplorer(config=get_preset("zai_thorough"))
    
    # Load the Discord export
    print(f"📂 Loading: {export_path}")
    schema = explorer.load(export_path)
    
    print(f"📊 Loaded {schema.total_records:,} messages")
    print(f"📋 Schema: {explorer.analyze_schema()[:500]}")
    
    # Marketing analysis questions
    analyses = {
        "product_sentiment": "What are people saying about our product? Include both positive and negative feedback.",
        "feature_requests": "What features or improvements are users requesting?",
        "pain_points": "What problems, bugs, or frustrations are users mentioning?",
        "competitor_mentions": "What are people saying about competitors or alternative products?",
        "success_stories": "What success stories or positive outcomes are users sharing?",
        "pricing_feedback": "What are people saying about pricing, cost, or value?",
        "onboarding_experience": "What are people saying about getting started or onboarding?",
        "support_issues": "What support issues or questions come up frequently?",
    }
    
    results = {}
    
    for name, question in analyses.items():
        print(f"\n🔍 Analyzing: {name}")
        print("-" * 40)
        
        result = explorer.query(question, save_trace=True, trace_dir=output_dir)
        results[name] = result
        
        print(f"   ✅ Found {result.verification.citations_found if result.verification else 0} mentions")
        print(f"   📊 {result.total_tokens:,} tokens used")
        
        # Save individual report
        report_path = Path(output_dir) / f"{name}.md"
        with open(report_path, 'w') as f:
            f.write(f"# {name.replace('_', ' ').title()}\n\n")
            f.write(f"**Question:** {question}\n\n")
            f.write("---\n\n")
            f.write(result.answer)
            
            if result.citation_report:
                f.write("\n\n---\n\n")
                f.write("## All Citations\n\n")
                f.write(result.citation_report.to_markdown())
    
    # Generate executive summary
    print("\n📝 Generating executive summary...")
    generate_executive_summary(results, output_dir)
    
    print(f"\n✅ Analysis complete! Reports saved to: {output_dir}")
    return results


def generate_executive_summary(results: dict, output_dir: str):
    """Generate an executive summary from all analyses."""
    
    summary_path = Path(output_dir) / "EXECUTIVE_SUMMARY.md"
    
    with open(summary_path, 'w') as f:
        f.write("# 📊 Discord Community Intelligence Report\n\n")
        f.write(f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("---\n\n")
        
        f.write("## 📈 Overview\n\n")
        f.write("| Analysis | Citations Found | Unique Authors | Sentiment |\n")
        f.write("|----------|-----------------|----------------|----------|\n")
        
        for name, result in results.items():
            if result.verification:
                v = result.verification
                sentiment = "🟢" if v.positive_mentions > v.negative_mentions else "🔴" if v.negative_mentions > v.positive_mentions else "🟡"
                f.write(f"| {name.replace('_', ' ').title()} | {v.citations_found} | {v.unique_authors} | {sentiment} |\n")
        
        f.write("\n---\n\n")
        
        f.write("## 🔑 Key Findings\n\n")
        for name, result in results.items():
            f.write(f"### {name.replace('_', ' ').title()}\n\n")
            # First 500 chars of answer
            preview = result.answer[:500] + "..." if len(result.answer) > 500 else result.answer
            f.write(f"{preview}\n\n")
            f.write(f"[📄 Full Report](./{name}.md)\n\n")
        
        f.write("---\n\n")
        f.write("*Generated by JSON Explorer - RLM-powered community intelligence*\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python discord_marketing_analysis.py /path/to/discord_export.json")
        print("\nThis will analyze your Discord export and generate marketing reports.")
        sys.exit(1)
    
    analyze_discord_community(sys.argv[1])
```

---

## 💡 Real-World Example: Kling 2.6 Analysis

**Scenario**: A video tools company wants to understand community discussion about competitor "Kling 2.6"

**Query**:
```python
result = explorer.query(
    "What are people saying about Kling 2.6 for video generation?"
)
```

**Sample Output**:

```markdown
## 📊 Summary Statistics
- Total mentions found: 8
- Unique contributors: 5
- Sentiment breakdown: Positive 5, Negative 1, Neutral 2

## 🔍 All Citations (Chronological)

### Citation 1
> "Just tried Kling 2.6 for the first time. The motion quality is incredible!"

**Source:** @video_creator | 2025-01-02T09:00:00 | #ai-video
**Ref:** `0.0`
**Sentiment:** Positive
**Key Point:** First impressions are very positive regarding motion quality

---

### Citation 2
> "Kling 2.6 really improved the temporal consistency. Much better than 2.5."

**Source:** @ai_researcher | 2025-01-02T09:15:00 | #ai-video
**Ref:** `0.1`
**Sentiment:** Positive
**Key Point:** Version upgrade shows measurable improvement

---

### Citation 3
> "I'm not convinced. Runway Gen-3 still produces better results for me."

**Source:** @skeptic_sam | 2025-01-02T09:30:00 | #ai-video
**Ref:** `0.2`
**Sentiment:** Negative
**Key Point:** Some users prefer competitor (Runway Gen-3)

[... more citations ...]

## 📈 Analysis

### Common Themes
1. **Motion Quality** - Consistently praised (3 mentions)
2. **Speed** - Fast generation times noted (2 mentions)
3. **Comparison to Runway** - Mixed opinions (2 mentions)
4. **Pricing** - Pro tier limitations mentioned (1 mention)

### Notable Opinions
- @video_creator is an influential voice (3 mentions)
- @ai_researcher provides technical perspective

### Contradictions or Debates
- Quality vs Speed tradeoff (Kling faster, Sora higher quality)
- Some prefer Runway Gen-3, others prefer Kling
```

---

## 🔧 Configuration Options for Marketers

### Speed vs Thoroughness

```python
# Quick insights (cheaper, faster)
explorer = JsonExplorer(config=get_preset("zai_fast"))

# Deep analysis (thorough, more expensive)
explorer = JsonExplorer(config=get_preset("zai_thorough"))
```

### Budget Control

```python
from json_explorer.config import ExplorerConfig

config = ExplorerConfig(
    model="glm-4.5-air",  # Cheaper model
    max_tokens_budget=50_000,  # Cap spending
    max_chunks_per_query=50,  # Limit data scanned
)
```

### Enterprise Features

```python
config = ExplorerConfig(
    model="glm-4.7",
    use_neon=True,  # Cache results in Neon PostgreSQL
    use_r2=True,  # Store large exports in Cloudflare R2
    trace_level=TraceLevel.FULL,  # Full audit trail
)
```

---

## 📱 MCP Integration for Non-Technical Users

### Use with Claude Code (No coding required!)

Add JSON Explorer to Claude Code:

```bash
# Install globally
pip install json-explorer

# Run as MCP server
json-explorer --mode mcp
```

Then in Claude Code:
> "Load the Discord export at /path/to/export.json and tell me what people are saying about our pricing"

### Web/iOS Integration

Deploy as HTTP server:

```bash
json-explorer --mode http --port 8080
```

API calls:
```bash
# Load file
curl -X POST http://localhost:8080/load -d '{"path": "/data/export.json"}'

# Query
curl -X POST http://localhost:8080/query -d '{"query": "What features are users requesting?"}'
```

---

## ✅ Why Marketers Love This

| Feature | Benefit |
|---------|---------|
| **Exhaustive search** | Never miss a mention |
| **Citations** | Quote users with confidence |
| **Sentiment analysis** | Know if feedback is positive/negative |
| **No coding required** | Use via Claude Code or web interface |
| **Full audit trail** | Verify every insight independently |
| **Cost effective** | GLM 4.7 via Z.AI is affordable |
| **Fast results** | Analyze thousands of messages in minutes |

---

## 🎯 Getting Started Checklist

- [ ] Export Discord data (JSON format)
- [ ] Get Z.AI API key from https://z.ai
- [ ] Install: `pip install json-explorer[all]`
- [ ] Set env var: `export Z_AI_API_KEY="your_key"`
- [ ] Run: `python discord_marketing_analysis.py /path/to/export.json`
- [ ] Review reports in `./reports/` directory

---

## 📞 Support

- **Documentation**: See `README.md`
- **Examples**: See `example_usage.py`
- **Issues**: Open a GitHub issue

---

*Built with ❤️ using RLM (Recursive Language Models)*

