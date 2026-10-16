"""Run the local-only FASTER-13 JSON framing baseline.

Usage: python scripts/benchmark_mcp_fastpath.py --repetitions 200
No network I/O, host services, provider keys or external work.
"""
from __future__ import annotations

import argparse
import json

from runner_mcp.fastpath_benchmark import benchmark_synthetic_framing


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic local MCP JSON baseline")
    parser.add_argument("--repetitions", type=int, default=200)
    args = parser.parse_args()
    print(json.dumps(benchmark_synthetic_framing(repetitions=args.repetitions), indent=2))


if __name__ == "__main__":
    main()
