#!/usr/bin/env python3
"""
Cleanup script to:
1. Map trace files to conversation files
2. Rename trace files with correct conversation numbers
3. Update cross-references
4. Regenerate index
"""

import os
import re
import json
from pathlib import Path

CONV_DIR = Path(__file__).parent / "sessions" / "2026-01-03_introductiontoalgorithmsfourthedition"

# Manual mapping based on question analysis
TRACE_MAPPING = {
    "TRACE-01-20260103-191829-what-is-quicksort-gi.md": {
        "conv_num": 13,
        "question": "What is quicksort? Give me the pseudocode from the textbook with page numbers.",
        "conv_file": "13-2026-01-03-quicksort-give-pseudocode-from-textbook-.md"
    },
    "TRACE-01-20260103-193302-what-is-merge-sort-g.md": {
        "conv_num": 14,
        "question": "What is merge sort? Give the pseudocode from page 40 with page numbers.",
        "conv_file": "14-2026-01-03-merge-sort-give-pseudocode-from-page-40-.md"
    },
    "TRACE-01-20260103-193939-what-is-binary-searc.md": {
        "conv_num": 15,
        "question": "What is binary search? Give the pseudocode with page number.",
        "conv_file": "15-2026-01-03-binary-search-give-pseudocode-with-page-.md"
    },
    "TRACE-01-20260103-194407-what-is-a-red-black-.md": {
        "conv_num": 16,
        "question": "What is a red-black tree? Give the 5 properties from page 442.",
        "conv_file": "16-2026-01-03-redblack-tree-give-5-properties-from-pag.md"
    },
    "TRACE-01-20260103-194949-what-is-a-hash-table.md": {
        "conv_num": 17,
        "question": "What is a hash table and how does it work?",
        "conv_file": "17-2026-01-03-hash-table-and-it-work.md"
    },
    "TRACE-01-20260103-195849-explain-binary-searc.md": {
        "conv_num": 18,
        "question": "explain binary search trees",
        "conv_file": "18-2026-01-03-binary-search-trees.md"
    },
    "TRACE-buildmaxheap-walkthrough.md": {
        "conv_num": 10,
        "question": "BUILD-MAX-HEAP algorithm",
        "conv_file": "10-2026-01-03-buildmaxheap-algorithm-extract-pseudocod.md"
    }
}


def rename_trace_files():
    """Rename trace files to match conversation numbers."""
    print("=" * 60)
    print("STEP 1: Renaming Trace Files")
    print("=" * 60)
    
    for old_name, info in TRACE_MAPPING.items():
        old_path = CONV_DIR / old_name
        if not old_path.exists():
            print(f"  ⚠️  Not found: {old_name}")
            continue
        
        # Create new trace filename
        conv_num = info["conv_num"]
        timestamp = re.search(r'20260103-\d{6}', old_name)
        timestamp_str = timestamp.group() if timestamp else "20260103-000000"
        
        # Extract topic from old filename
        topic_match = re.search(r'\d{6}-(.+)\.md$', old_name)
        topic = topic_match.group(1) if topic_match else "trace"
        
        new_name = f"TRACE-{conv_num:02d}-{timestamp_str}-{topic}.md"
        new_path = CONV_DIR / new_name
        
        print(f"  📝 {old_name}")
        print(f"     → {new_name}")
        
        # Read and update content
        content = old_path.read_text()
        
        # Update "Query #1" to "Query #N"
        content = re.sub(
            r'Query #\d+',
            f'Query #{conv_num}',
            content
        )
        
        # Update the "For the clean answer, see:" reference
        content = re.sub(
            r'For the clean answer, see: `\d+-',
            f'For the clean answer, see: `{conv_num:02d}-',
            content
        )
        
        # Write updated content to new file
        new_path.write_text(content)
        
        # Remove old file if different
        if old_path != new_path:
            old_path.unlink()
        
        print(f"     ✅ Done")
    
    print()


def update_conversation_files():
    """Add trace file references to conversation files."""
    print("=" * 60)
    print("STEP 2: Updating Conversation Files")
    print("=" * 60)
    
    for old_trace, info in TRACE_MAPPING.items():
        conv_file = CONV_DIR / info["conv_file"]
        if not conv_file.exists():
            print(f"  ⚠️  Not found: {info['conv_file']}")
            continue
        
        conv_num = info["conv_num"]
        timestamp = re.search(r'20260103-\d{6}', old_trace)
        timestamp_str = timestamp.group() if timestamp else "20260103-000000"
        topic_match = re.search(r'\d{6}-(.+)\.md$', old_trace)
        topic = topic_match.group(1) if topic_match else "trace"
        
        new_trace_name = f"TRACE-{conv_num:02d}-{timestamp_str}-{topic}.md"
        
        content = conv_file.read_text()
        
        # Check if trace link already exists
        if "## 📋 Execution Trace" in content or "TRACE-" in content:
            print(f"  ℹ️  {info['conv_file']} - already has trace reference")
            continue
        
        # Add trace link before Performance Metrics section
        trace_section = f"""
---

## 📋 Execution Trace

> 🔍 For detailed execution log, see: [`{new_trace_name}`]({new_trace_name})

"""
        
        # Insert before Performance Metrics or at end
        if "## 📊 Performance Metrics" in content:
            content = content.replace(
                "## 📊 Performance Metrics",
                trace_section + "## 📊 Performance Metrics"
            )
        else:
            content += trace_section
        
        conv_file.write_text(content)
        print(f"  ✅ {info['conv_file']} - added trace reference")
    
    print()


def regenerate_index():
    """Regenerate the 00-index.md with trace links."""
    print("=" * 60)
    print("STEP 3: Regenerating Index")
    print("=" * 60)
    
    # Find all conversation files
    conv_files = sorted([
        f for f in CONV_DIR.iterdir()
        if f.name.startswith(tuple(f"{i:02d}-" for i in range(1, 100)))
        and f.suffix == ".md"
    ])
    
    # Find all trace files
    trace_files = sorted([
        f for f in CONV_DIR.iterdir()
        if f.name.startswith("TRACE-") and f.suffix == ".md"
    ])
    
    # Build index content
    index_content = """# 📚 Conversation Index

> **Session:** 2026-01-03 | Introduction to Algorithms (4th Edition)  
> **Total Entries:** {num_entries}

---

## 📖 Q&A Entries

| # | Question | Answer | Trace |
|---|----------|--------|-------|
""".format(num_entries=len(conv_files))
    
    for conv_file in conv_files:
        # Extract number
        match = re.match(r'(\d+)-', conv_file.name)
        if not match:
            continue
        num = int(match.group(1))
        
        # Read file to get question
        content = conv_file.read_text()
        q_match = re.search(r'## ❓ Question\s+(.+?)(?:\n\n|\n---)', content, re.DOTALL)
        question = q_match.group(1).strip()[:60] + "..." if q_match and len(q_match.group(1).strip()) > 60 else (q_match.group(1).strip() if q_match else "N/A")
        
        # Find matching trace
        trace_link = "-"
        for trace_file in trace_files:
            if trace_file.name.startswith(f"TRACE-{num:02d}-"):
                trace_link = f"[📋]({trace_file.name})"
                break
        
        index_content += f"| {num:02d} | {question} | [View]({conv_file.name}) | {trace_link} |\n"
    
    index_content += """
---

## 📊 Legend

- **Answer**: Link to clean, formatted answer
- **Trace**: Link to full execution trace (for debugging/auditing)

---

*Generated by RLM Textbook Q&A*
"""
    
    # Write index
    index_path = CONV_DIR / "00-index.md"
    index_path.write_text(index_content)
    print(f"  ✅ 00-index.md regenerated with {len(conv_files)} entries")
    print()


def main():
    print("\n" + "=" * 60)
    print("🧹 TRACE FILE CLEANUP & ORGANIZATION")
    print("=" * 60 + "\n")
    
    rename_trace_files()
    update_conversation_files()
    regenerate_index()
    
    print("=" * 60)
    print("✅ CLEANUP COMPLETE")
    print("=" * 60)
    print("""
Files updated:
- Trace files renamed to match conversation numbers (TRACE-NN-...)
- Conversation files updated with trace references
- Index regenerated with trace links
""")


if __name__ == "__main__":
    main()

