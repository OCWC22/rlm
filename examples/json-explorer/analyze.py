#!/usr/bin/env python3
"""
JSON Explorer Analysis CLI
===========================

Modular analysis tool for JSON data (Discord exports, logs, API dumps, etc.)

USAGE:
    # Marketing analysis
    python analyze.py data.json --analyzer marketing

    # Product + Support analysis
    python analyze.py data.json --analyzer product support
    
    # All built-in analyzers
    python analyze.py data.json --all
    
    # Custom analyzer from YAML
    python analyze.py data.json --custom my_analysis.yaml
    
    # Quick single query
    python analyze.py data.json --query "What are people saying about pricing?"
    
    # Analyze specific topic
    python analyze.py data.json --topic "Kling 2.6"

ANALYZERS:
    marketing   - Product sentiment, competitors, feature requests
    product     - Feature usage, bugs, user journey
    support     - FAQs, documentation gaps, troubleshooting
    research    - Themes, behaviors, mental models
    sentiment   - Overall sentiment, influencers, NPS signals

OUTPUT:
    ./reports/
    ├── SUMMARY.md
    ├── marketing.md
    ├── product.md
    └── ...
"""

import os
import sys
from pathlib import Path
from typing import Optional
import argparse

# Add parent to path for development
sys.path.insert(0, str(Path(__file__).parent))

from json_explorer import JsonExplorer, ExplorerConfig, TraceLevel
from json_explorer.config import AdapterType
from json_explorer.analysis import (
    AnalysisPipeline,
    MarketingAnalyzer,
    ProductAnalyzer,
    SupportAnalyzer,
    ResearchAnalyzer,
    SentimentAnalyzer,
    CustomAnalyzer,
    # Specialized
    CompetitorAnalyzer,
    TrendAnalyzer,
    InfluencerAnalyzer,
    PricingAnalyzer,
    BugAnalyzer,
    OnboardingDeepDive,
)
from json_explorer.analysis.marketing import CampaignAnalyzer
from json_explorer.analysis.research import TopicAnalyzer
from json_explorer.analysis.product import ReleaseAnalyzer
from json_explorer.analysis.custom import QuickAnalyzer, create_analyzer_template


# ============================================================================
# ANALYZER REGISTRY
# ============================================================================

ANALYZERS = {
    # Core analyzers
    "marketing": MarketingAnalyzer,
    "product": ProductAnalyzer,
    "support": SupportAnalyzer,
    "research": ResearchAnalyzer,
    "sentiment": SentimentAnalyzer,
    # Specialized analyzers
    "competitors": CompetitorAnalyzer,
    "trends": TrendAnalyzer,
    "influencers": InfluencerAnalyzer,
    "pricing": PricingAnalyzer,
    "bugs": BugAnalyzer,
    "onboarding": OnboardingDeepDive,
}

ANALYZER_DESCRIPTIONS = {
    # Core
    "marketing": "Product sentiment, competitors, feature requests, pricing",
    "product": "Feature usage, bugs, user journey, integrations",
    "support": "FAQs, documentation gaps, troubleshooting, self-service",
    "research": "Themes, behaviors, mental models, terminology",
    "sentiment": "Overall sentiment, influencers, trust signals, NPS",
    # Specialized
    "competitors": "Competitor mentions, comparisons, switching reasons",
    "trends": "Emerging topics, growing concerns, sentiment shifts",
    "influencers": "Key contributors, thought leaders, advocates",
    "pricing": "Price perception, value, willingness to pay",
    "bugs": "Bug reports, reproduction steps, workarounds",
    "onboarding": "First impressions, setup friction, time to value",
}


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def create_explorer(model: str = "glm-4.7") -> JsonExplorer:
    """Create configured JsonExplorer instance."""
    
    # Check for API keys
    if os.getenv("Z_AI_API_KEY"):
        print(f"🔑 Using Z.AI with {model}")
        config = ExplorerConfig(
            model=model,
            adapter_type=AdapterType.ZAI,
            base_url="https://api.z.ai/api/anthropic",
            trace_level=TraceLevel.FULL,
        )
    elif os.getenv("ANTHROPIC_API_KEY"):
        print("🔑 Using Anthropic API")
        model = "claude-3-haiku-20240307" if model.startswith("glm") else model
        config = ExplorerConfig(
            model=model,
            adapter_type=AdapterType.ANTHROPIC,
            trace_level=TraceLevel.FULL,
        )
    else:
        print("❌ No API key found!")
        print("   Set one of:")
        print("   - Z_AI_API_KEY (recommended)")
        print("   - ANTHROPIC_API_KEY")
        sys.exit(1)
    
    return JsonExplorer(config=config)


def progress_callback(analyzer_name: str, question_id: str, current: int, total: int):
    """Print progress updates."""
    print(f"   [{current}/{total}] {question_id}")


def run_analysis(
    data_path: str,
    analyzer_names: list[str],
    output_dir: str = "./reports",
    model: str = "glm-4.7",
    save_traces: bool = True,
):
    """Run specified analyzers on data."""
    
    # Create explorer and load data
    explorer = create_explorer(model)
    
    print(f"\n📂 Loading: {data_path}")
    try:
        schema = explorer.load(data_path)
        print(f"   ✅ Loaded {schema.total_records:,} records")
        print(f"   📋 Format: {schema.format.value}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        sys.exit(1)
    
    # Create pipeline
    pipeline = AnalysisPipeline(explorer)
    
    # Add requested analyzers
    for name in analyzer_names:
        if name not in ANALYZERS:
            print(f"   ⚠️  Unknown analyzer: {name}")
            continue
        
        analyzer = ANALYZERS[name]()
        pipeline.add_analyzer(analyzer)
        print(f"   ➕ Added: {name}")
    
    # Run pipeline
    print(f"\n{'='*60}")
    print("🚀 RUNNING ANALYSIS")
    print('='*60)
    
    reports = pipeline.run(
        save_traces=save_traces,
        trace_dir=str(Path(output_dir) / "traces"),
        progress_callback=progress_callback,
    )
    
    # Save reports
    pipeline.save_reports(output_dir)
    
    # Summary
    print(f"\n{'='*60}")
    print("✅ ANALYSIS COMPLETE")
    print('='*60)
    
    total_citations = sum(r.total_citations for r in reports)
    total_tokens = sum(r.total_tokens for r in reports)
    
    print(f"   📁 Reports: {output_dir}")
    print(f"   📊 Citations: {total_citations:,}")
    print(f"   🔢 Tokens: {total_tokens:,}")
    print(f"\n   📄 Open {output_dir}/SUMMARY.md to view results")


def run_topic_analysis(
    data_path: str,
    topic: str,
    output_dir: str = "./reports",
    model: str = "glm-4.7",
):
    """Run deep analysis on a specific topic."""
    
    explorer = create_explorer(model)
    
    print(f"\n📂 Loading: {data_path}")
    schema = explorer.load(data_path)
    print(f"   ✅ Loaded {schema.total_records:,} records")
    
    print(f"\n🔍 Analyzing topic: {topic}")
    print('='*60)
    
    # Create topic analyzer
    analyzer = TopicAnalyzer(topic=topic)
    
    report = analyzer.run(
        explorer,
        save_traces=True,
        trace_dir=str(Path(output_dir) / "traces"),
        progress_callback=lambda q, c, t: print(f"   [{c}/{t}] {q}"),
    )
    
    # Save report
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    report_file = output_path / f"topic_{topic.replace(' ', '_').lower()}.md"
    with open(report_file, 'w') as f:
        f.write(report.to_markdown())
    
    print(f"\n✅ Analysis complete!")
    print(f"   📄 Report: {report_file}")
    print(f"   📊 Citations: {report.total_citations}")


def run_quick_query(
    data_path: str,
    question: str,
    model: str = "glm-4.7",
):
    """Run a single quick query."""
    
    explorer = create_explorer(model)
    
    print(f"\n📂 Loading: {data_path}")
    schema = explorer.load(data_path)
    print(f"   ✅ Loaded {schema.total_records:,} records")
    
    print(f"\n❓ Query: {question[:60]}...")
    print('='*60)
    
    result = explorer.query(question)
    
    print(f"\n💡 ANSWER:")
    print('-'*60)
    print(result.answer)
    print('-'*60)
    
    if result.verification:
        print(f"\n📊 Stats:")
        print(f"   Citations: {result.verification.citations_found}")
        print(f"   Authors: {result.verification.unique_authors}")
        print(f"   Sentiment: +{result.verification.positive_mentions} / -{result.verification.negative_mentions}")


def run_custom_analyzer(
    data_path: str,
    config_path: str,
    output_dir: str = "./reports",
    model: str = "glm-4.7",
):
    """Run custom analyzer from YAML/JSON config."""
    
    explorer = create_explorer(model)
    
    print(f"\n📂 Loading: {data_path}")
    schema = explorer.load(data_path)
    print(f"   ✅ Loaded {schema.total_records:,} records")
    
    print(f"\n📋 Loading analyzer: {config_path}")
    
    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
        analyzer = CustomAnalyzer.from_yaml(config_path)
    else:
        analyzer = CustomAnalyzer.from_json(config_path)
    
    print(f"   ✅ Loaded: {analyzer.name} ({len(analyzer.questions)} questions)")
    
    print(f"\n🚀 Running analysis...")
    print('='*60)
    
    report = analyzer.run(
        explorer,
        save_traces=True,
        trace_dir=str(Path(output_dir) / "traces"),
        progress_callback=lambda q, c, t: print(f"   [{c}/{t}] {q}"),
    )
    
    # Save report
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    report_file = output_path / f"{analyzer.name}.md"
    with open(report_file, 'w') as f:
        f.write(report.to_markdown())
    
    print(f"\n✅ Analysis complete!")
    print(f"   📄 Report: {report_file}")
    print(f"   📊 Citations: {report.total_citations}")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze JSON data with modular analyzers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Marketing analysis
  python analyze.py export.json --analyzer marketing

  # Multiple analyzers
  python analyze.py export.json --analyzer marketing product support

  # All analyzers
  python analyze.py export.json --all

  # Analyze specific topic
  python analyze.py export.json --topic "Kling 2.6 video generation"

  # Quick single query
  python analyze.py export.json --query "What are people saying about pricing?"

  # Custom analyzer from YAML
  python analyze.py export.json --custom my_analysis.yaml

  # Create custom analyzer template
  python analyze.py --create-template my_analysis.yaml
        """
    )
    
    parser.add_argument("data_path", nargs="?", help="Path to JSON data file")
    parser.add_argument("--analyzer", "-a", nargs="+", choices=list(ANALYZERS.keys()),
                        help="Analyzer(s) to run")
    parser.add_argument("--all", action="store_true",
                        help="Run all built-in analyzers")
    parser.add_argument("--topic", "-t", help="Analyze a specific topic in depth")
    parser.add_argument("--query", "-q", help="Run a single quick query")
    parser.add_argument("--custom", "-c", help="Path to custom analyzer YAML/JSON")
    parser.add_argument("--output", "-o", default="./reports",
                        help="Output directory for reports")
    parser.add_argument("--model", "-m", default="glm-4.7",
                        help="LLM model to use")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List available analyzers")
    parser.add_argument("--create-template", metavar="PATH",
                        help="Create a template for custom analyzer")
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║               JSON Explorer Analysis CLI                      ║
║               Powered by RLM + Z.AI                           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # List analyzers
    if args.list:
        print("Available analyzers:\n")
        for name, desc in ANALYZER_DESCRIPTIONS.items():
            print(f"  {name:12} - {desc}")
        return
    
    # Create template
    if args.create_template:
        path = create_analyzer_template(args.create_template)
        print(f"✅ Created template: {path}")
        print(f"   Edit this file, then run: python analyze.py data.json --custom {path}")
        return
    
    # Require data path for analysis
    if not args.data_path:
        parser.print_help()
        return
    
    # Quick query
    if args.query:
        run_quick_query(args.data_path, args.query, args.model)
        return
    
    # Topic analysis
    if args.topic:
        run_topic_analysis(args.data_path, args.topic, args.output, args.model)
        return
    
    # Custom analyzer
    if args.custom:
        run_custom_analyzer(args.data_path, args.custom, args.output, args.model)
        return
    
    # Standard analysis
    if args.all:
        analyzer_names = list(ANALYZERS.keys())
    elif args.analyzer:
        analyzer_names = args.analyzer
    else:
        # Default to marketing
        print("No analyzer specified, defaulting to 'marketing'")
        print("Use --list to see all analyzers, --all to run all\n")
        analyzer_names = ["marketing"]
    
    run_analysis(
        data_path=args.data_path,
        analyzer_names=analyzer_names,
        output_dir=args.output,
        model=args.model,
    )


if __name__ == "__main__":
    main()

