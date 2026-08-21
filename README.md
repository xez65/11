# 霓虹茶舍 UI 编辑器插件

这是一个面向 Codex 的本地 UI 审核编辑器插件。它主要用于在视觉稿/HTML 界面切片审核阶段进行可视化编辑，并在审核通过后把修改结果导出，供 WebGAL 或部分主流游戏引擎项目使用。

## 仓库内容

- `plugins/neon-teahouse-ui-editor/`：完整插件目录，包含 Codex 插件清单、技能、脚本和编辑器页面。
- `plugins/neon-teahouse-ui-editor/assets/ui-review-editor.html`：自包含 UI 审核编辑器，可直接双击打开。
- `plugins/neon-teahouse-ui-editor/assets/ui-review-editor-source.html`：编辑器源码。
- `plugins/neon-teahouse-ui-editor/scripts/`：扫描、打开和应用审核结果的脚本。
- `plugins/neon-teahouse-ui-editor/skills/ui-review-editor/SKILL.md`：Codex 触发和审核流程说明。

详细说明见：[plugins/neon-teahouse-ui-editor/README.md](plugins/neon-teahouse-ui-editor/README.md)

## 功能

- 可视化编辑 HTML 界面切片。
- 内置对话、调茶、HUD、公告、回看、结局等页面切换。
- 支持编辑、撤销、校验、归档、导入、导出。
- 支持扫描 WebGAL 项目并生成 UI 映射。
- 支持把审核结果应用到 WebGAL 的文本型样式文件，并自动备份。
- 支持扫描 Unity、Godot、Cocos 等引擎项目，导出 AIToUGUI 兼容数据。

## 手动安装

1. 下载本仓库中的 `plugins/neon-teahouse-ui-editor` 目录。
2. 在目标 Codex 项目目录中创建插件目录：

   ```text
   <project>/plugins/neon-teahouse-ui-editor
   ```

3. 在 `<project>/.agents/plugins/marketplace.json` 中登记插件：

   ```json
   {
     "name": "neon-teahouse-team",
     "interface": {
       "displayName": "霓虹茶舍 Team"
     },
     "plugins": [
       {
         "name": "neon-teahouse-ui-editor",
         "source": {
           "source": "local",
           "path": "./plugins/neon-teahouse-ui-editor"
         },
         "policy": {
           "installation": "INSTALLED_BY_DEFAULT",
           "authentication": "ON_INSTALL"
         },
         "category": "Game Development"
       }
     ]
   }
   ```

4. 完全退出并重新启动 Codex，让插件的新技能和脚本被加载。

## 触发方式

在 Codex 对话中直接提到以下任意关键词即可触发：

- 使用 UI 编辑器
- UI 审核
- HTML 界面切片
- UI 资源编辑

## 使用流程

1. 在 Codex 中说“使用 UI 编辑器，帮我审核当前 HTML 界面切片”。
2. 打开编辑器，导入实际 HTML 切片。
3. 选择目标页面和元素，提出视觉修改意见。
4. 编辑、撤销、校验，直到画面满足要求。
5. 说“通过，导出审核 JSON”，导出通用审核结果。
6. 如需要，扫描 WebGAL 或主流引擎项目，并把审核结果应用到项目。

## WebGAL 应用

先扫描项目：

```powershell
python scripts/scan_webgal_project.py --project-root <webgal-project>
```

再应用审核结果：

```powershell
python scripts/apply_review_to_webgal.py --review-json <review.json> --project-root <webgal-project> --page-id <review-page-id>
```

应用前会显示 dry-run；只有使用者确认后才会实际写入，并生成 `.bak` 备份。

## 引擎项目支持

```powershell
python scripts/scan_game_engine_project.py --project-root <engine-project>
python scripts/apply_review_to_engine.py --review-json <review.json> --project-root <engine-project> --page-id <review-page-id>
```

当前可自动修改的文本型文件：

- Unity UI Toolkit `.uss`
- Godot `.tscn` / `.tres` / `.theme`
- Cocos Creator `.scene` / `.prefab`

Unreal `.uasset` 是二进制文件，扫描器会列出，但不会自动修改。

## 注意事项

- 审核阶段只生成导出文件，不直接修改原始 HTML 切片。
- 应用 WebGAL 前必须使用 dry-run 查看计划。
- 应用脚本只写入映射文件中声明过的文件，并拒绝写出游戏根目录之外。
- 应用脚本每次写入都会生成 `.bak` 备份。
- 不同 WebGAL 游戏项目应先运行扫描器，再分别配置映射。
- 插件不会自动声称 Unity 导入成功；只有使用者在 Unity 中实际验证后才可记录该结论。
- `assets/webgal_maps/` 是使用者的本机扫描结果，不应随插件包分发。
