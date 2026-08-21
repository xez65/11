#!/usr/bin/env python3
"""Scan a mainstream game engine project and generate a UI mapping template."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def detect_engine(root: Path) -> str | None:
    if (root / "ProjectSettings" / "ProjectVersion.txt").is_file():
        return "unity"
    if (root / "project.godot").is_file() or list(root.rglob("project.godot"))[:1]:
        return "godot"
    if list(root.rglob("*.uproject"))[:1]:
        return "unreal"
    project_json = root / "project.json"
    if project_json.is_file():
        try:
            data = read_json(project_json)
        except json.JSONDecodeError:
            data = {}
        text = json.dumps(data).lower()
        if "creator" in text or "cocos" in text:
            return "cocos"
    return None


def scan_files(root: Path, patterns: list[str]) -> list[str]:
    files: set[str] = set()
    for pattern in patterns:
        for match in root.glob(pattern):
            if match.is_file():
                files.add(match.resolve().relative_to(root.resolve()).as_posix())
    return sorted(files)


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
    return value or "project"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "engine_maps",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    engine = detect_engine(root)
    if not engine:
        print(f"engine not detected under {root}")
        return 1

    default_map_path = (
        Path(__file__).resolve().parents[1] / "assets" / "engine_ui_map" / f"{engine}.json"
    )
    default_map = read_json(default_map_path) if default_map_path.is_file() else {}
    patterns = default_map.get("uiFilePatterns", [])
    ui_files = scan_files(root, patterns)

    mapping = {
        "engine": engine,
        "projectRoot": root.as_posix(),
        "uiFiles": ui_files,
        "unsupported": bool(default_map.get("unsupported", False)),
        "note": default_map.get("note", ""),
        "elements": default_map.get("elements", {}),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{engine}-{slugify(root.name)}"
    output = args.output_dir / f"{stem}.json"
    output.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index_path = args.output_dir / "index.json"
    index: dict = {"projects": []}
    if index_path.is_file():
        index = read_json(index_path)
    projects = index.get("projects", [])
    projects = [item for item in projects if item.get("projectRoot") != root.as_posix()]
    projects.append({"projectRoot": root.as_posix(), "engine": engine, "mappingFile": output.name})
    index["projects"] = projects
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"generated {output.name}: engine={engine}, "
        f"uiFiles={len(ui_files)}, unsupported={bool(mapping['unsupported'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
