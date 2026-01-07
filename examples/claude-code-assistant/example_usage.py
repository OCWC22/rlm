#!/usr/bin/env python3
"""
Example: RLM Context Extension for Claude Code / Codex / Any CLI Agent

This demonstrates the RLM (Recursive Language Model) approach to extending
context windows beyond model limits. Based on:
- RLM Paper: https://arxiv.org/abs/2512.24601v1
- Prime Intellect RLMEnv: https://github.com/PrimeIntellect-ai/verifiers

Run with: python example_usage.py
"""

import os
import sys
from pathlib import Path

# Import from local module
from rlm_context import (
    RLMContextEngine,
    Session,
    auto_chunk,
    chunk_code_aware,
    create_client,
    process_codebase,
)


def test_chunking():
    """Test the chunking strategies."""
    print("=" * 60)
    print("Test 1: Chunking Strategies")
    print("=" * 60)

    # Sample code content
    code = """
# Module A

def function_a():
    '''Does A'''
    return "a"

def function_b():
    '''Does B'''
    return "b"

# Module B

class ServiceB:
    def method_1(self):
        pass

    def method_2(self):
        pass

# Module C

async def async_handler(request):
    return await process(request)
""" * 5  # Repeat to make larger

    print(f"Input: {len(code)} chars")

    # Auto-detect
    chunks = auto_chunk(code, chunk_size=500)
    print(f"\nAuto-detect: {len(chunks)} chunks")
    for c in chunks[:3]:
        print(f"  Chunk {c.index}: {c.size} chars")

    # Code-aware
    chunks = chunk_code_aware(code, chunk_size=500)
    print(f"\nCode-aware: {len(chunks)} chunks")
    for c in chunks[:3]:
        print(f"  Chunk {c.index}: {c.size} chars, metadata: {c.metadata}")

    print("\n✓ Chunking works!")
    return True


def test_session():
    """Test session persistence."""
    print("\n" + "=" * 60)
    print("Test 2: Session Persistence")
    print("=" * 60)

    # Create session
    session = Session("test-rlm-session")

    # Add messages
    session.add_message("user", "What is this code about?")
    session.add_message("assistant", "This is an RLM implementation...")

    # Add memory
    session.add_memory("architecture", "Uses recursive decomposition with sub-LLM calls")
    session.add_memory("key_function", "llm_batch() enables parallel sub-LLM queries")

    print(f"Session ID: {session.session_id}")
    print(f"Messages: {len(session.messages)}")
    print(f"Memories: {len(session.memories)}")

    # Search memories
    results = session.search_memories("how does recursion work")
    print(f"\nMemory search results: {len(results)}")
    for key, content in results:
        print(f"  [{key}]: {content[:50]}...")

    # Cleanup
    if session.path.exists():
        session.path.unlink()

    print("\n✓ Session persistence works!")
    return True


def test_rlm_engine_simple():
    """Test RLM engine with small context (no API needed)."""
    print("\n" + "=" * 60)
    print("Test 3: RLM Engine (Mock)")
    print("=" * 60)

    # Create a mock client for testing without API
    class MockClient:
        def get_context_limit(self):
            return 10_000  # Small for testing

        def query(self, prompt, system=None):
            from rlm_context import LLMResponse
            # Simulate response
            if "CHUNK" in prompt:
                return LLMResponse(
                    content="Found relevant information: This chunk discusses the architecture.",
                    model="mock",
                    tokens_in=100,
                    tokens_out=50,
                    elapsed_seconds=0.1,
                )
            else:
                return LLMResponse(
                    content="Based on analysis of multiple chunks: The system uses a modular architecture.",
                    model="mock",
                    tokens_in=200,
                    tokens_out=100,
                    elapsed_seconds=0.2,
                )

    # Create engine with mock
    engine = RLMContextEngine(MockClient(), chunk_size=1000, verbose=True)

    # Test with small context (single pass)
    small_context = "This is a small context that fits in the window."
    result = engine.process(small_context, "What is this about?")
    print(f"\nSmall context result: {result[:100]}...")

    # Test with large context (chunked)
    large_context = "This is a large context. " * 500
    result = engine.process(large_context, "Summarize this content")
    print(f"\nLarge context result: {result[:100]}...")

    # Check stats
    stats = engine.get_stats()
    print(f"\nStats: {stats}")

    print("\n✓ RLM Engine works!")
    return True


def test_with_real_api():
    """Test with real API (requires ANTHROPIC_API_KEY or OPENAI_API_KEY)."""
    print("\n" + "=" * 60)
    print("Test 4: Real API Test")
    print("=" * 60)

    # Check for API key
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    if not has_anthropic and not has_openai:
        print("⚠ Skipping: No API key found")
        print("  Set ANTHROPIC_API_KEY or OPENAI_API_KEY to run this test")
        return True

    provider = "anthropic" if has_anthropic else "openai"
    print(f"Using provider: {provider}")

    try:
        client = create_client(provider)
        engine = RLMContextEngine(client, verbose=True)

        # Test with the RLM module itself as context
        context = Path(__file__).parent / "rlm_context.py"
        if context.exists():
            content = context.read_text()
            print(f"Loaded {len(content)} chars from rlm_context.py")

            result = engine.process(
                content,
                "Explain the main classes and their purpose in this code.",
                chunking="code",
            )

            print(f"\nResult:\n{'-' * 40}")
            print(result[:500] + "..." if len(result) > 500 else result)

            print(f"\nStats: {engine.get_stats()}")
            print("\n✓ Real API test passed!")
        else:
            print("⚠ rlm_context.py not found")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_codebase_processing():
    """Test processing a codebase directory."""
    print("\n" + "=" * 60)
    print("Test 5: Codebase Processing")
    print("=" * 60)

    # Check for API
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("⚠ Skipping: No API key")
        return True

    # Process the parent rlm directory
    rlm_dir = Path(__file__).parent.parent.parent / "rlm"

    if not rlm_dir.exists():
        print(f"⚠ Directory not found: {rlm_dir}")
        return True

    try:
        provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
        result = process_codebase(
            rlm_dir,
            "What is the purpose of this codebase? Describe the main components.",
            provider=provider,
        )

        print(f"\nResult:\n{'-' * 40}")
        print(result[:500] + "..." if len(result) > 500 else result)
        print("\n✓ Codebase processing works!")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def demo_interactive():
    """Demo of interactive mode."""
    print("\n" + "=" * 60)
    print("Demo: Interactive Mode")
    print("=" * 60)

    print("""
To use interactive mode, run:

    python rlm_context.py --interactive --session my-project

Commands in interactive mode:
    /remember <key> <content>  - Store a memory
    /recall <query>            - Search memories
    exit                       - Quit

Example session:
    rlm> What is this codebase about?
    [RLM processes and responds]

    rlm> /remember architecture Uses recursive sub-LLM calls
    Stored: architecture

    rlm> /recall how does it work
    [architecture] Uses recursive sub-LLM calls...
""")


def demo_cli():
    """Demo of CLI usage."""
    print("\n" + "=" * 60)
    print("Demo: CLI Usage")
    print("=" * 60)

    print("""
CLI Examples:

# Analyze a single file
python rlm_context.py "Explain this code" --context ./src/main.py

# Analyze a directory
python rlm_context.py "Find security issues" --context ./src/

# With research augmentation
python rlm_context.py "Check for known vulnerabilities" --context ./src/ --research

# Use OpenAI instead of Anthropic
python rlm_context.py "Summarize" --context ./docs/ --provider openai

# Interactive session with persistence
python rlm_context.py --interactive --session my-analysis

# Quiet mode (no progress output)
python rlm_context.py "Quick summary" --context ./README.md --quiet
""")


def main():
    """Run all tests and demos."""
    print("\n" + "=" * 60)
    print("RLM Context Extension - Tests & Demos")
    print("=" * 60 + "\n")

    all_passed = True

    # Tests that don't need API
    all_passed &= test_chunking()
    all_passed &= test_session()
    all_passed &= test_rlm_engine_simple()

    # Tests that need API
    all_passed &= test_with_real_api()
    # all_passed &= test_codebase_processing()  # Uncomment to run

    # Demos
    demo_interactive()
    demo_cli()

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed ✗")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
