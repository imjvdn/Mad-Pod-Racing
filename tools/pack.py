#!/usr/bin/env python3
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print a CodinGame submission file to stdout (simple concatenation helper)."
    )
    parser.add_argument("file", type=Path, help="Path to a single-file bot (e.g. bots/mad_pod_racing/bot.py)")
    args = parser.parse_args()

    src = args.file.read_text(encoding="utf-8")
    print(src, end="" if src.endswith("\n") else "\n")


if __name__ == "__main__":
    main()


