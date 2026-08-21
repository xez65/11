#!/usr/bin/env python3
"""Open the bundled UI review editor in the default browser."""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Open the bundled UI review editor.")
    parser.add_argument(
        "--print-path",
        action="store_true",
        help="Print the editor path instead of opening the browser.",
    )
    args = parser.parse_args()

    editor = Path(__file__).resolve().parents[1] / "assets" / "ui-review-editor.html"
    if not editor.is_file():
        print(f"editor not found: {editor}")
        return 1

    if args.print_path:
        print(editor)
        return 0

    opened = webbrowser.open(editor.as_uri())
    if not opened:
        print(f"could not open editor: {editor}")
        return 1
    print(f"opened UI review editor: {editor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
