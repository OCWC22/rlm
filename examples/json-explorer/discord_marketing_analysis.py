#!/usr/bin/env python3
"""
Discord Marketing Analysis (Legacy Wrapper)
============================================

This is a convenience wrapper around the modular analysis framework.
For the full framework, see `analyze.py` or use the Python API.

USAGE:
    python discord_marketing_analysis.py /path/to/discord_export.json

EQUIVALENT TO:
    python analyze.py discord_export.json --analyzer marketing sentiment
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from analyze import run_analysis


def main():
    if len(sys.argv) < 2:
        print("""
Discord Marketing Analysis
--------------------------

Usage: python discord_marketing_analysis.py <discord_export.json>

This runs marketing + sentiment analysis on your Discord export.

For more options, use the modular CLI:
    python analyze.py export.json --analyzer marketing product support
    python analyze.py export.json --all
    python analyze.py export.json --topic "your topic"
        """)
        sys.exit(1)
    
    data_path = sys.argv[1]
    output_dir = f"./reports/discord_{Path(data_path).stem}"
    
    print("🎯 Running Marketing + Sentiment Analysis\n")
    print(f"   For full options: python analyze.py {data_path} --help\n")
    
    run_analysis(
        data_path=data_path,
        analyzer_names=["marketing", "sentiment"],
        output_dir=output_dir,
        model="glm-4.7",
    )


if __name__ == "__main__":
    main()
