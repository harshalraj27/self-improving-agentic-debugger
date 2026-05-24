from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent.agent import Agent


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Autonomous debugger for Python and C++ source files.",
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the target source file to debug.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        dest="max_retries",
        help="Maximum number of fix attempts before halting (default: 5).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target = Path(args.file_path)

    if not target.is_file():
        print(f"Error: target file does not exist: {target}", file=sys.stderr)
        return 1

    resolved = target.resolve()
    print(f"[agent] Initializing debugger | file={resolved} | max_retries={args.max_retries}")

    agent = Agent(str(resolved), max_retries=args.max_retries)

    try:
        success = agent.run()
    except KeyboardInterrupt:
        print("\n[agent] Interrupted by user.", file=sys.stderr)
        return 130

    if success:
        print("[agent] SUCCESS — target file executes cleanly (exit code 0).")
        return 0

    print(
        "[agent] FAILURE — debugging halted: retry budget exhausted, "
        "execution timeout, or invalid LLM patch formatting.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())