#!/usr/bin/env python3
"""Scan WebGAL game projects and generate per-project UI mapping templates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SELECTOR_RE = re.compile(r"(?m)^[.#][A-Za-z0-9_-]+")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def config_value(game_root: Path, key: str) -> str:
    config = game_root / "game" / "config.txt"
    if not config.is_file():
        return ""
    text = read_text(config)
    match = re.search(rf"{re.escape(key)}:([^;]+);", text)
    return match.group(1).strip() if match else ""


def find_game_roots(webgal_root: Path) -> list[Path]:
    roots: list[Path] = []
    public_games = webgal_root / "public" / "games"
    if public_games.is_dir():
        for config in public_games.rglob("game/config.txt"):
            game_root = config.parent.parent
            if game_root not in roots:
                roots.append(game_root)
    else:
        for candidate in webgal_root.rglob("config.txt"):
            if candidate.parent.name == "game":
                game_root = candidate.parent.parent
                if game_root not in roots:
                    roots.append(game_root)
    return roots


def collect_selectors(game_root: Path) -> dict[str, list[str]]:
    files: dict[str, list[str]] = {}
    template = game_root / "game" / "template"
    if template.is_dir():
        for scss in template.rglob("*.scss"):
            relative = scss.relative_to(game_root).as_posix()
            selectors = SELECTOR_RE.findall(read_text(scss))
            if selectors:
                files[relative] = sorted(set(selectors))
    css = game_root / "game" / "userStyleSheet.css"
    if css.is_file():
        selectors = SELECTOR_RE.findall(read_text(css))
        if selectors:
            files[css.relative_to(game_root).as_posix()] = sorted(set(selectors))
    return files


def build_mapping(
    game_root: Path,
    game_key: str,
    game_name: str,
    selectors_by_file: dict[str, list[str]],
) -> dict[str, object]:
    default_map = Path(__file__).resolve().parents[1] / "assets" / "webgal_ui_map.json"
    base = json.loads(default_map.read_text(encoding="utf-8")) if default_map.is_file() else {}
    elements = base.get("elements", {}) if isinstance(base.get("elements"), dict) else {}
    all_selectors = sorted({selector for selectors in selectors_by_file.values() for selector in selectors})
    return {
        "gameName": game_name or game_root.name,
        "gameKey": game_key or game_root.name,
        "gameRoot": game_root.as_posix(),
        "elements": elements,
        "_selectorsByFile": selectors_by_file,
        "_selectors": all_selectors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--webgal-root", required=True, type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "webgal_maps",
    )
    args = parser.parse_args()

    roots = find_game_roots(args.webgal_root)
    if not roots:
        print("no WebGAL game roots found")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    records: list[dict[str, str]] = []
    used_names: set[str] = set()
    for game_root in roots:
        game_key = config_value(game_root, "Game_key") or game_root.name
        game_name = config_value(game_root, "Game_name") or game_root.name
        selectors_by_file = collect_selectors(game_root)
        mapping = build_mapping(game_root, game_key, game_name, selectors_by_file)
        stem = re.sub(r"[^A-Za-z0-9_-]+", "-", game_key).strip("-") or "game"
        if stem in used_names:
            index = 2
            while f"{stem}-{index}" in used_names:
                index += 1
            stem = f"{stem}-{index}"
        used_names.add(stem)
        output = args.output_dir / f"{stem}.json"
        output.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(output)
        records.append({
            "gameRoot": game_root.resolve().as_posix(),
            "mappingFile": output.name,
        })
        print(
            f"generated {output.name}: game={game_name}, "
            f"selectors={len(mapping['_selectors'])}"
        )

    index_path = args.output_dir / "index.json"
    index_path.write_text(
        json.dumps({"games": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[scanned] {len(written)} game mapping file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
