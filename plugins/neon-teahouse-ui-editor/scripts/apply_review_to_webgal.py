#!/usr/bin/env python3
"""Apply a UI review JSON to WebGAL in-game UI styles.

The script is intentionally conservative: it only edits files listed in the
mapping file. Run it without --apply to review the planned changes first.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def value_to_css(value: object, field: str) -> str:
    if value is None:
        return ""
    if field in {"xPercent", "yPercent", "widthPercent", "heightPercent"}:
        return f"{float(value):.2f}%"
    if field == "fontSizePx":
        return f"{float(value):.2f}px"
    return str(value)


def find_block(text: str, selector: str) -> tuple[int, int] | None:
    match = re.search(re.escape(selector) + r"\s*\{", text)
    if not match:
        return None
    start = match.end() - 1
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    return None


def update_block(text: str, selector: str, declarations: dict[str, str]) -> str | None:
    block = find_block(text, selector)
    if block is None:
        new_block = f"{selector} {{\n" + "".join(
            f"  {prop}: {value};\n" for prop, value in declarations.items()
        ) + "}\n"
        if not text.strip():
            return new_block
        return text.rstrip() + "\n\n" + new_block
    start, end = block
    body = text[start:end]
    for prop, value in declarations.items():
        pattern = re.compile(
            rf"(^|\n)(\s*){re.escape(prop)}\s*:\s*[^;]+;",
            re.IGNORECASE,
        )
        replacement = rf"\1\2{prop}: {value};"
        if pattern.search(body):
            body = pattern.sub(replacement, body)
        else:
            insertion = "\n  " if body.rstrip().endswith("}") else "  "
            body = body[:-1] + f"{insertion}{prop}: {value};\n}}"
    return text[:start] + body + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-json", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument(
        "--mapping",
        type=Path,
        default=None,
        help="Optional per-game mapping file. Auto-detected when omitted.",
    )
    parser.add_argument("--page-id", help="Only apply elements from this review page id.")
    parser.add_argument("--apply", action="store_true", help="Write changes to the WebGAL game root.")
    args = parser.parse_args()

    review = load_json(args.review_json)
    if args.mapping is None:
        plugin_root = Path(__file__).resolve().parents[1]
        game_root_posix = args.game_root.resolve().as_posix()
        index_path = plugin_root / "assets" / "webgal_maps" / "index.json"
        if index_path.is_file():
            index = load_json(index_path)
            for record in index.get("games", []):
                if record.get("gameRoot") == game_root_posix:
                    args.mapping = plugin_root / "assets" / "webgal_maps" / record.get("mappingFile", "")
                    break
        if args.mapping is None:
            game_key = ""
            config_path = args.game_root / "game" / "config.txt"
            if config_path.is_file():
                match = re.search(r"Game_key:([^;]+);", config_path.read_text(encoding="utf-8-sig"))
                game_key = match.group(1).strip() if match else ""
            per_game = plugin_root / "assets" / "webgal_maps" / f"{game_key}.json"
            args.mapping = per_game if per_game.is_file() else plugin_root / "assets" / "webgal_ui_map.json"
        print(f"[mapping] using {args.mapping.name}")
    mapping = load_json(args.mapping)
    elements = mapping.get("elements", {})
    if not isinstance(elements, dict):
        print("mapping file must contain an elements object")
        return 2

    review_elements: list[dict] = []
    pages = review.get("pages", [])
    if isinstance(pages, list):
        for page in pages:
            if args.page_id and page.get("pageId") != args.page_id:
                continue
            if isinstance(page, dict) and isinstance(page.get("elements"), list):
                review_elements.extend(page["elements"])

    planned: list[str] = []
    updates: dict[Path, str] = {}
    for item in review_elements:
        element_id = item.get("id", "")
        u_name = item.get("uName", "")
        target = elements.get(element_id) or elements.get(u_name)
        if not target:
            continue
        relative_file = target.get("file")
        selector = target.get("selector")
        property_map = target.get("properties", {})
        if not relative_file or not selector or not isinstance(property_map, dict):
            planned.append(f"skip {element_id}: invalid mapping entry")
            continue

        target_path = (args.game_root / relative_file).resolve()
        if not str(target_path).startswith(str(args.game_root.resolve())):
            print(f"refusing to write outside game root: {target_path}")
            return 1
        original = updates.get(target_path)
        if original is None:
            original = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
        declarations: dict[str, str] = {}
        layout = item.get("layout") or {}
        style = item.get("style") or {}
        source = {**layout, **style}
        for editor_field, css_property in property_map.items():
            value = source.get(editor_field)
            css_value = value_to_css(value, editor_field)
            if css_value:
                declarations[css_property] = css_value
        if not declarations:
            planned.append(f"skip {element_id}: no mapped values present")
            continue
        updated = update_block(original, selector, declarations)
        if updated is None:
            planned.append(f"skip {element_id}: selector {selector} not found and file is non-empty")
            continue
        planned.append(
            f"update {relative_file} {selector}: "
            + ", ".join(f"{prop}: {value}" for prop, value in declarations.items())
        )
        updates[target_path] = updated

    print("\n".join(planned) if planned else "no mapped changes")
    if not args.apply:
        print("\n[dry-run] no files were changed. Add --apply to write.")
        return 0

    for target_path, updated in updates.items():
        backup = target_path.with_suffix(target_path.suffix + ".bak")
        shutil.copy2(target_path, backup) if target_path.exists() else None
        target_path.write_text(updated, encoding="utf-8")
    print(f"[applied] {len(updates)} file(s) updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
