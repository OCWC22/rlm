#!/usr/bin/env python3
"""
Example: Using JSON Explorer to query large JSON files.

This script demonstrates:
1. Loading a JSON file and analyzing its schema
2. Querying the data with natural language
3. EXHAUSTIVE queries with citations (find EVERY mention)
4. Examining execution traces with source verification
5. Using Z.AI with GLM 4.7

To run:
    python example_usage.py

For a real Discord export:
    python example_usage.py /path/to/discord_export.json

With Z.AI:
    export Z_AI_API_KEY='your_key'
    python example_usage.py --zai /path/to/export.json
"""

import os
import sys
import json
from pathlib import Path

# Ensure we can import from parent
sys.path.insert(0, str(Path(__file__).parent))

from json_explorer import (
    JsonExplorer, 
    ExplorerConfig, 
    TraceLevel,
    QueryIntent,
)


# ============================================================================
# Sample Data: Simulated Discord Export
# ============================================================================

SAMPLE_DISCORD_EXPORT = [
    {
        "id": "1234567890",
        "channel_id": "general",
        "author": {"name": "alice", "id": "1001"},
        "content": "Hey everyone! Has anyone tried the new product launch?",
        "timestamp": "2025-01-01T10:00:00.000Z"
    },
    {
        "id": "1234567891",
        "channel_id": "general",
        "author": {"name": "bob", "id": "1002"},
        "content": "Yes! The product launch went really well. Sales are up 50%!",
        "timestamp": "2025-01-01T10:05:00.000Z"
    },
    {
        "id": "1234567892",
        "channel_id": "general",
        "author": {"name": "charlie", "id": "1003"},
        "content": "The marketing campaign was key. Great work by the team.",
        "timestamp": "2025-01-01T10:10:00.000Z"
    },
    {
        "id": "1234567893",
        "channel_id": "product",
        "author": {"name": "alice", "id": "1001"},
        "content": "We need to fix the bug in the checkout flow ASAP.",
        "timestamp": "2025-01-01T11:00:00.000Z"
    },
    {
        "id": "1234567894",
        "channel_id": "product",
        "author": {"name": "dave", "id": "1004"},
        "content": "I'm on it. Should have a fix by EOD.",
        "timestamp": "2025-01-01T11:15:00.000Z"
    },
    {
        "id": "1234567895",
        "channel_id": "product",
        "author": {"name": "alice", "id": "1001"},
        "content": "Thanks Dave! The product launch success depends on this.",
        "timestamp": "2025-01-01T11:20:00.000Z"
    },
    {
        "id": "1234567896",
        "channel_id": "random",
        "author": {"name": "bob", "id": "1002"},
        "content": "Anyone want to grab lunch? Celebrating the product launch!",
        "timestamp": "2025-01-01T12:00:00.000Z"
    },
    {
        "id": "1234567897",
        "channel_id": "general",
        "author": {"name": "charlie", "id": "1003"},
        "content": "The product launch metrics are impressive. 10k signups in first hour!",
        "timestamp": "2025-01-01T14:00:00.000Z"
    },
    {
        "id": "1234567898",
        "channel_id": "general",
        "author": {"name": "alice", "id": "1001"},
        "content": "Amazing! Let's discuss next steps in tomorrow's standup.",
        "timestamp": "2025-01-01T14:30:00.000Z"
    },
    {
        "id": "1234567899",
        "channel_id": "product",
        "author": {"name": "dave", "id": "1004"},
        "content": "Bug fix is deployed. Checkout flow is working now.",
        "timestamp": "2025-01-01T17:00:00.000Z"
    },
]


# Sample data with video generation tool discussions (Kling 2.6 example)
SAMPLE_KLING_DISCUSSION = [
    {
        "id": "5001",
        "channel_id": "ai-video",
        "author": {"name": "video_creator", "id": "2001"},
        "content": "Just tried Kling 2.6 for the first time. The motion quality is incredible!",
        "timestamp": "2025-01-02T09:00:00.000Z"
    },
    {
        "id": "5002",
        "channel_id": "ai-video",
        "author": {"name": "ai_researcher", "id": "2002"},
        "content": "Kling 2.6 really improved the temporal consistency. Much better than 2.5.",
        "timestamp": "2025-01-02T09:15:00.000Z"
    },
    {
        "id": "5003",
        "channel_id": "ai-video",
        "author": {"name": "skeptic_sam", "id": "2003"},
        "content": "I'm not convinced. Runway Gen-3 still produces better results for me.",
        "timestamp": "2025-01-02T09:30:00.000Z"
    },
    {
        "id": "5004",
        "channel_id": "general",
        "author": {"name": "casual_user", "id": "2004"},
        "content": "Has anyone used Kling for music videos? Looking for recommendations.",
        "timestamp": "2025-01-02T10:00:00.000Z"
    },
    {
        "id": "5005",
        "channel_id": "ai-video",
        "author": {"name": "video_creator", "id": "2001"},
        "content": "The Kling 2.6 camera controls are game-changing. You can specify exact movements.",
        "timestamp": "2025-01-02T10:30:00.000Z"
    },
    {
        "id": "5006",
        "channel_id": "ai-video",
        "author": {"name": "pro_editor", "id": "2005"},
        "content": "Kling 2.6 video generation is fast but the 1080p export is limited to Pro users.",
        "timestamp": "2025-01-02T11:00:00.000Z"
    },
    {
        "id": "5007",
        "channel_id": "ai-video",
        "author": {"name": "ai_researcher", "id": "2002"},
        "content": "The paper behind Kling 2.6 shows they're using a novel diffusion approach.",
        "timestamp": "2025-01-02T11:30:00.000Z"
    },
    {
        "id": "5008",
        "channel_id": "general",
        "author": {"name": "video_creator", "id": "2001"},
        "content": "For anyone asking about Kling - it's now my go-to for product demos.",
        "timestamp": "2025-01-02T12:00:00.000Z"
    },
    {
        "id": "5009",
        "channel_id": "ai-video",
        "author": {"name": "skeptic_sam", "id": "2003"},
        "content": "Tried Kling 2.6 again with better prompts. Actually getting decent results now.",
        "timestamp": "2025-01-02T14:00:00.000Z"
    },
    {
        "id": "5010",
        "channel_id": "ai-video",
        "author": {"name": "pro_editor", "id": "2005"},
        "content": "Just compared Kling 2.6 vs Sora for same prompt. Kling wins on speed, Sora on quality.",
        "timestamp": "2025-01-02T15:00:00.000Z"
    },
]


def example_basic_usage():
    """Basic usage: Load data and query."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Create explorer with a small model
    explorer = JsonExplorer(
        model="claude-3-haiku-20240307",
        provider="anthropic",
    )
    
    # Load sample data
    schema = explorer.load_data(SAMPLE_DISCORD_EXPORT, name="sample_discord")
    
    print("\n📋 Schema Analysis:")
    print("-" * 40)
    print(explorer.analyze_schema())
    
    # Query the data
    print("\n❓ Query: What was discussed about the product launch?")
    print("-" * 40)
    
    result = explorer.query("What was discussed about the product launch?")
    
    print(f"\n💡 Answer:\n{result.answer}")
    print(f"\n📊 Stats: {result.chunks_processed} chunks, {result.total_tokens} tokens, {result.duration_ms:.0f}ms")


def example_with_trace():
    """Example with full execution trace."""
    print("\n" + "=" * 60)
    print("Example 2: Query with Execution Trace")
    print("=" * 60)
    
    config = ExplorerConfig(
        model="claude-3-haiku-20240307",
        trace_level=TraceLevel.FULL,
    )
    
    explorer = JsonExplorer(config=config)
    explorer.load_data(SAMPLE_DISCORD_EXPORT, name="sample_discord")
    
    # Query with trace
    result = explorer.query("Who fixed the checkout bug?", save_trace=False)
    
    print(f"\n💡 Answer:\n{result.answer}")
    
    # Show trace summary
    if result.trace:
        print("\n📋 Execution Trace (Summary):")
        print("-" * 40)
        print(result.trace.to_markdown(TraceLevel.SUMMARY))


def example_streaming():
    """Example with streaming output."""
    print("\n" + "=" * 60)
    print("Example 3: Streaming Query")
    print("=" * 60)
    
    explorer = JsonExplorer(model="claude-3-haiku-20240307")
    explorer.load_data(SAMPLE_DISCORD_EXPORT, name="sample_discord")
    
    print("\n❓ Query: What are the main topics discussed?")
    print("-" * 40)
    
    for update in explorer.stream_query("What are the main topics discussed?"):
        print(update, end="", flush=True)


def example_filtered_search():
    """Example with keyword filtering."""
    print("\n" + "=" * 60)
    print("Example 4: Filtered Search")
    print("=" * 60)
    
    explorer = JsonExplorer(model="claude-3-haiku-20240307")
    explorer.load_data(SAMPLE_DISCORD_EXPORT, name="sample_discord")
    
    # Search for specific keyword
    result = explorer.query('Find all messages mentioning "bug"')
    
    print(f"\n💡 Answer:\n{result.answer}")
    print(f"\n📊 Chunks processed: {result.chunks_processed}")
    print(f"📊 Chunks filtered: {result.chunks_filtered}")


def example_exhaustive_with_citations():
    """
    EXHAUSTIVE query: Find EVERY mention with citations.
    
    This is like textbook-qa's page reference system but for JSON records.
    Use this when you need to capture everything said about a topic.
    """
    print("\n" + "=" * 60)
    print("Example 5: Exhaustive Query with Citations")
    print("=" * 60)
    print("(Like textbook-qa - captures EVERY mention with source citations)")
    
    config = ExplorerConfig(
        model="claude-3-haiku-20240307",
        trace_level=TraceLevel.FULL,
    )
    
    explorer = JsonExplorer(config=config)
    explorer.load_data(SAMPLE_KLING_DISCUSSION, name="kling_discussion")
    
    # This query triggers EXHAUSTIVE extraction
    query = "What are people saying about Kling 2.6 for video generation?"
    
    print(f"\n❓ Query: {query}")
    print("-" * 40)
    
    result = explorer.query(query, save_trace=True, trace_dir="./traces")
    
    print(f"\n💡 Answer:\n{result.answer}")
    
    # Show verification summary (like textbook-qa)
    if result.verification:
        print("\n" + "=" * 40)
        print("✅ VERIFICATION SUMMARY")
        print("=" * 40)
        print(f"| Citations found | {result.verification.citations_found} |")
        print(f"| Unique authors  | {result.verification.unique_authors} |")
        print(f"| ✅ Positive     | {result.verification.positive_mentions} |")
        print(f"| ❌ Negative     | {result.verification.negative_mentions} |")
        print(f"| ➖ Neutral      | {result.verification.neutral_mentions} |")
        
        if result.verification.issues:
            print("\n⚠️ Issues:")
            for issue in result.verification.issues:
                print(f"  - {issue}")
        
        # Show reference IDs for verification
        if result.verification.reference_ids:
            print(f"\n🔗 Reference IDs for verification:")
            for ref in result.verification.reference_ids[:5]:
                print(f"  - {ref}")
            if len(result.verification.reference_ids) > 5:
                print(f"  ... and {len(result.verification.reference_ids) - 5} more")
    
    # Show citation report location
    if result.citation_report:
        print(f"\n📄 Full citation report saved to: ./traces/")
    
    print(f"\n📊 Stats: {result.chunks_processed} chunks, {result.total_tokens} tokens, {result.duration_ms:.0f}ms")


def example_zai_glm():
    """Example using Z.AI with GLM 4.7."""
    print("\n" + "=" * 60)
    print("Example 6: Using Z.AI with GLM 4.7")
    print("=" * 60)
    
    # Check for Z.AI API key
    if not os.getenv("Z_AI_API_KEY"):
        print("⚠️  Z_AI_API_KEY not set")
        print("   Get your key at https://z.ai/manage-apikey/apikey-list")
        print("\n   To use with Claude Code:")
        print('   export ANTHROPIC_AUTH_TOKEN="your_zai_key"')
        print('   export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"')
        return
    
    config = ExplorerConfig(
        model="glm-4.7",  # Z.AI's best model
        provider="zai",
        trace_level=TraceLevel.SUMMARY,
    )
    
    explorer = JsonExplorer(config=config)
    explorer.load_data(SAMPLE_KLING_DISCUSSION, name="kling_discussion")
    
    # Exhaustive query with GLM 4.7
    result = explorer.query("What are all the opinions about Kling 2.6?")
    
    print(f"\n💡 Answer:\n{result.answer}")
    print(f"\n📊 Stats: {result.total_tokens} tokens, {result.duration_ms:.0f}ms")


def example_from_file(file_path: str):
    """Example loading from actual file."""
    print("=" * 60)
    print(f"Loading: {file_path}")
    print("=" * 60)
    
    explorer = JsonExplorer(
        model="claude-3-haiku-20240307",
        provider="anthropic",
    )
    
    try:
        schema = explorer.load(file_path)
        
        print("\n📋 Schema Analysis:")
        print("-" * 40)
        print(explorer.analyze_schema())
        
        print("\n📦 Sample Records:")
        print("-" * 40)
        samples = explorer.get_sample(3)
        print(json.dumps(samples, indent=2, ensure_ascii=False)[:1000])
        
        # Interactive query
        print("\n" + "=" * 60)
        print("Interactive Mode - Type 'quit' to exit")
        print("=" * 60)
        
        while True:
            try:
                question = input("\n❓ Your question: ").strip()
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                if not question:
                    continue
                
                print("\n⏳ Processing...")
                result = explorer.query(question)
                
                print(f"\n💡 Answer:\n{result.answer}")
                print(f"\n📊 Stats: {result.chunks_processed} chunks, {result.total_tokens} tokens, {result.duration_ms:.0f}ms")
                
            except KeyboardInterrupt:
                break
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples."""
    print("\n🔍 JSON Explorer Examples")
    print("=" * 60)
    
    # Check for API key
    api_key_available = os.getenv("ANTHROPIC_API_KEY") or os.getenv("Z_AI_API_KEY")
    
    if not api_key_available:
        print("⚠️  No API key found")
        print("   Option 1 (Anthropic): export ANTHROPIC_API_KEY='sk-ant-...'")
        print("   Option 2 (Z.AI):      export Z_AI_API_KEY='your_key'")
        print("\n   Using sample responses for demo...\n")
        
        # Show what would happen without actually calling API
        print("Example flow (dry run):")
        print("1. Load JSON file → Analyze schema")
        print("2. User asks: 'What are people saying about Kling 2.6?'")
        print("3. System chunks data and scans ALL chunks (exhaustive)")
        print("4. For each chunk: Extract EVERY mention with citations")
        print("5. Aggregate with full source verification")
        print("6. Return answer with:")
        print("   - All citations (author, timestamp, channel)")
        print("   - Reference IDs for verification")
        print("   - Sentiment breakdown")
        print("   - Full execution trace")
        return
    
    # Check if file path provided
    use_zai = "--zai" in sys.argv
    file_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    
    if file_args:
        example_from_file(file_args[0])
    else:
        # Run sample examples
        try:
            example_basic_usage()
            example_with_trace()
            example_streaming()
            example_filtered_search()
            
            # New: Exhaustive query with citations
            example_exhaustive_with_citations()
            
            # Z.AI example (if key available)
            if os.getenv("Z_AI_API_KEY"):
                example_zai_glm()
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

