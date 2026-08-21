---
name: ui-review-editor
description: Use the bundled UI review editor when the user mentions UI编辑器、UI审核、界面切片、HTML 切片、UI 资源编辑，or when a UI asset task reaches its review stage and needs actual HTML slice editing.
---

# UI 审核编辑器

This skill brings the bundled `ui-review-editor.html` into the conversation and keeps it as the
review surface for UI HTML slices.

## When to use

- The user says they want to use the UI editor, UI 审核器, or HTML 界面切片编辑.
- A UI task has reached the review stage and needs a person to inspect or adjust an HTML slice.
- The conversation is about Unity UGUI/AIToUGUI UI assets and needs a review JSON or bundle.

## Automatic startup

When invoked:

1. Resolve the editor path:

   - From this skill file: `../../assets/ui-review-editor.html`.
   - From the plugin root: `assets/ui-review-editor.html`.

2. Open it:

   - Run `python ../../scripts/open_ui_editor.py` when a shell is available.
   - Or print/click the editor path and tell the user to open it.

3. Tell the user the editor is ready and briefly list the six built-in pages plus the
   "导入 HTML 切片" entry.

## Review-stage workflow

When a UI resource is ready for review:

1. Ask the user for the actual HTML slice file to review.
2. Open the editor and ask them to click "导入 HTML 切片", then select that HTML file.
3. The editor converts elements with `data-u-type` and `data-u-name` into a new "HTML 切片" page.
4. The user can edit copy, layout, size, colors, and visibility, then validate.
5. Export one or both artifacts:

   - `导出 JSON`: generic review data under `neon-teahouse-ui-review/v2`.
   - `导出 AIToUGUI`: Lite bundle JSON for Unity preview.

6. Do not modify the original HTML file during review. Treat the exports as review artifacts until
   the user explicitly approves applying changes.

## WebGAL application stage

After the user approves a reviewed result and asks to apply it to a WebGAL project:

1. Ask for the WebGAL project root if the user has not provided it.
2. Scan the WebGAL root to generate per-game mapping templates:

```powershell
python ../../scripts/scan_webgal_project.py --webgal-root <WebGAL-root>
```

This writes `assets/webgal_maps/<game-key>.json` and `index.json`. Each mapping file includes
the game name, game key, root path, discovered selectors, and a copy of the default element map.
3. Configure the generated per-game mapping by editing the `elements` object when the target game
   uses different selector names. Do not edit other games' mapping files unless asked.
4. Apply the reviewed page:

```powershell
python ../../scripts/apply_review_to_webgal.py `
  --review-json <review.json> `
  --game-root <WebGAL-game-folder> `
  --page-id <review-page-id>
```

Run without `--apply` first. After the user confirms the dry-run plan, rerun with `--apply`.
The script creates `.bak` files and refuses to write outside the given game root.

## Mainstream engine application stage

The same review-and-apply loop works for Unity, Godot, Cocos Creator, and Unreal projects:

1. Ask for the project root if not provided.
2. Scan and generate an engine mapping:

```powershell
python ../../scripts/scan_game_engine_project.py --project-root <project-root>
```

3. Configure `assets/engine_maps/<engine>-<project>.json` if the generated `elements` need
   project-specific file paths or selectors.
4. Apply the reviewed page:

```powershell
python ../../scripts/apply_review_to_engine.py `
  --review-json <review.json> `
  --project-root <project-root> `
  --page-id <review-page-id>
```

Supported text-based file kinds:

- Unity UI Toolkit `.uss` via CSS selector updates.
- Cocos Creator `.scene` / `.prefab` JSON via dotted `jsonPath`.
- Godot `.tscn` / `.tres` / `.theme` via `key = value` updates.

Unreal `.uasset` files are binary and are listed by the scanner but not auto-patched.

Run without `--apply` first. After the user confirms the dry-run plan, rerun with `--apply`.
The script creates `.bak` files and refuses to write outside the given project root.

## Constraints

- Never claim Unity import passed unless the user actually runs Lite Studio and reports success.
- Keep the original HTML slice unchanged until the user approves a change.
- For WebGAL application, never modify files outside the user-provided project root.
- Preserve the editor's undo, validation, archive, snapshot, and annotation features.
