#!/usr/bin/env python3
"""Apply a UI review JSON to a mainstream game engine project."""

from __future__ import annotations

import argparse
import json
import re
import shutil
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


def update_css(text: str, selector: str, declarations: dict[str, str]) -> str:
    block = find_block(text, selector)
    new_block = f"{selector} {{\n" + "".join(
        f"  {prop}: {value};\n" for prop, value in declarations.items()
    ) + "}\n"
    if block is None:
        return new_block if not text.strip() else text.rstrip() + "\n\n" + new_block
    start, end = block
    body = text[start:end]
    for prop, value in declarations.items():
        pattern = re.compile(rf"(^|\n)(\s*){re.escape(prop)}\s*:\s*[^;]+;", re.IGNORECASE)
        replacement = rf"\1\2{prop}: {value};"
        if pattern.search(body):
            body = pattern.sub(replacement, body)
        else:
            body = body[:-1] + f"  {prop}: {value};\n}}"
    return text[:start] + body + text[end:]


def update_json(text: str, json_path: str, value: object) -> str:
    data = json.loads(text)
    parts = json_path.split(".")
    cursor = data
    for part in parts[:-1]:
        if isinstance(cursor, list):
            cursor = cursor[int(part)]
        else:
            cursor = cursor.setdefault(part, {})
    last = parts[-1]
    if isinstance(cursor, list):
        cursor[int(last)] = value
    else:
        cursor[last] = value
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def update_godot(text: str, key: str, formatted: str) -> str:
    pattern = re.compile(rf"(?m)^(\s*{re.escape(key)}\s*=\s*).*$")
    if pattern.search(text):
        return pattern.sub(lambda match: f"{match.group(1)}{formatted}", text)
    return text.rstrip() + f"\n{key} = {formatted}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-json", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--mapping", type=Path, default=None)
    parser.add_argument("--page-id", help="Only apply elements from this review page id.")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    if args.mapping is None:
        plugin_root = Path(__file__).resolve().parents[1]
        index_path = plugin_root / "assets" / "engine_maps" / "index.json"
        if index_path.is_file():
            index = load_json(index_path)
            for record in index.get("projects", []):
                if record.get("projectRoot") == project_root.as_posix():
                    args.mapping = plugin_root / "assets" / "engine_maps" / record.get("mappingFile", "")
                    break
        if args.mapping is None:
            print("no engine mapping found. Run scan_game_engine_project.py first.")
            return 1
        print(f"[mapping] using {args.mapping.name}")

    mapping = load_json(args.mapping)
    if mapping.get("unsupported"):
        print(f"engine mapping is unsupported: {mapping.get('note', '')}")
        return 0

    review = load_json(args.review_json)
    elements = mapping.get("elements", {})
    review_elements: list[dict] = []
    for page in review.get("pages", []):
        if args.page_id and page.get("pageId") != args.page_id:
            continue
        review_elements.extend(page.get("elements", []))

    updates: dict[Path, str] = {}
    planned: list[str] = []
    for item in review_elements:
        element_id = item.get("id", "")
        u_name = item.get("uName", "")
        target = elements.get(element_id) or elements.get(u_name)
        if not target:
            continue
        relative_file = target.get("file")
        kind = target.get("kind", "css")
        if not relative_file:
            continue
        target_path = (project_root / relative_file).resolve()
        if not str(target_path).startswith(str(project_root)):
            print(f"refusing to write outside project root: {target_path}")
            return 1
        original = updates.get(target_path)
        if original is None:
            original = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

        layout = item.get("layout") or {}
        style = item.get("style") or {}
        source = {**layout, **style}
        property_map = target.get("properties", {})
        values = {target_field: source.get(editor_field) for editor_field, target_field in property_map.items()}

        if kind == "css":
            declarations = {
                css_prop: value_to_css(value, editor_field)
                for editor_field, css_prop in property_map.items()
                for value in [source.get(editor_field)]
                if value_to_css(value, editor_field)
            }
            updated = update_css(original, target.get("selector", ""), declarations)
            planned.append(f"update {relative_file} {target.get('selector')}: {declarations}")
        elif kind == "json":
            json_path = target.get("jsonPath")
            values.pop("fontSizePx", None)
            value = values
            updated = update_json(original, json_path, value)
            planned.append(f"update {relative_file} {json_path}: {value}")
        elif kind == "godot":
            format_template = target.get("format", "{value}")
            formatted = format_template.format_map({k: (v if v is not None else 0) for k, v in values.items()})
            updated = update_godot(original, target.get("key", ""), formatted)
            planned.append(f"update {relative_file} {target.get('key')}: {formatted}")
        else:
            continue
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
