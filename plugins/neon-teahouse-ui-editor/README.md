# 霓虹茶舍 UI 编辑器插件使用说明

这份说明面向最终使用者，涵盖插件触发方式、UI 审核流程、WebGAL 应用流程和注意事项。

## 一、使用说明

### 1. 安装

1. 解压 `neon-teahouse-ui-editor-0.1.0-*.zip`。
2. 将解压得到的 `neon-teahouse-ui-editor` 文件夹放入 Codex 插件目录。
3. 重新打开 Codex 对话，使新插件被加载。

### 2. 触发插件

在对话中直接提到以下任意关键词，Codex 会自动加载 UI 编辑器技能：

- 使用 UI 编辑器
- UI 审核
- HTML 界面切片
- UI 资源编辑

### 3. 内置入口

插件包含：

- `assets/ui-review-editor.html`：自包含编辑器，可直接双击打开。
- `assets/ui-review-editor-source.html`：可修改源码。
- `assets/webgal_ui_map.json`：默认 WebGAL UI 映射。
- `scripts/open_ui_editor.py`：启动编辑器。
- `scripts/scan_webgal_project.py`：扫描 WebGAL 工程并生成项目映射。
- `scripts/apply_review_to_webgal.py`：把审核结果应用到 WebGAL 工程。

## 二、注意事项

1. 审核阶段只生成导出文件，不要修改原始 HTML 切片。
2. 应用 WebGAL 前必须使用 dry-run 查看计划。
3. 应用脚本只会写入映射文件中声明过的文件，且拒绝写出游戏根目录之外。
4. 应用脚本每次写入都会生成 `.bak` 备份文件。
5. 不同 WebGAL 游戏项目应先运行扫描器，再分别配置映射。
6. 插件不会自动声称 Unity 导入成功；只有使用者实际在 Unity Lite Studio 中验证后，才可记录该结论。
7. `assets/webgal_maps/` 是使用者的本机扫描结果，不应随插件包分发。

## 三、使用流程实例

### 1. 输入：打开 UI 编辑器

使用者输入：

```text
使用 UI 编辑器，帮我审核当前 HTML 界面切片。
```

Codex 输出：

```text
已打开霓虹茶舍 UI 审核编辑器。
内置页面：对话、调茶、HUD、公告、回看、结局。
请点击“导入 HTML 切片”并选择实际 HTML 文件。
```

### 2. 输入：导入切片

使用者选择文件：

```text
D:\邦邦二创\newwebgal\public\games\新的游戏\game\template\Stage\TextBox\参考切片.html
```

编辑器输出：

```text
已导入 HTML 切片。
当前页面：HTML 切片
可编辑元素数：20
```

### 3. 输入：给出修改意见

使用者输入：

```text
把根面板改成背景 #102030、文字 #f5e9d0、位置 20/8/68/30。
```

编辑器输出：

```text
当前选中：dialoguePanelRoot
已更新背景、文字、X/Y/宽高。
```

### 4. 输入：反馈并再次修改

使用者输入：

```text
整体还是太重，再冷一点，文字改成纯白，面板稍微更大。
```

编辑器输出：

```text
已调整：
background: #08121f
color: #ffffff
layout: 16 / 6 / 72 / 34
```

### 5. 输入：通过并导出

使用者输入：

```text
这版通过，导出审核 JSON。
```

Codex 输出：

```text
已导出：neon-teahouse-ui-review-2026-08-14.json
schema: neon-teahouse-ui-review/v2
页面数：7
```

### 6. 输入：应用到 WebGAL 默认工程

使用者输入：

```text
扫描 D:/邦邦二创/newwebgal，然后把这版落到“新的游戏”项目里。
```

Codex 输出：

```text
[scan] generated 43a6d6df2446a2c.json: game=新的游戏
[mapping] using 43a6d6df2446a2c.json

dry-run:
update game/template/Stage/TextBox/textbox.scss .TextBox_main:
  background: #08121f
  color: #ffffff
  left: 16.00%
  bottom: 6.00%
  width: 72.00%
  min-height: 34.00%

update game/userStyleSheet.css .Choose_item:nth-child(1)
update game/userStyleSheet.css .Choose_item:nth-child(2)
```

使用者确认：

```text
可以，应用。
```

Codex 输出：

```text
[applied] 2 file(s) updated
已生成 .bak 备份。
```

## 四、主流游戏引擎支持

插件也支持扫描主流引擎项目，并生成引擎 UI 映射：

```powershell
python scripts/scan_game_engine_project.py --project-root <project-root>
```

应用审核结果：

```powershell
python scripts/apply_review_to_engine.py --review-json <review.json> --project-root <project-root> --page-id <review-page-id>
```

当前可自动修改的文本型文件：

- Unity UI Toolkit `.uss`
- Godot `.tscn` / `.tres` / `.theme`
- Cocos Creator `.scene` / `.prefab`

Unreal `.uasset` 是二进制文件，扫描器会列出，但不会自动修改。

## 五、输出产物

审核和应用阶段会得到：

- 通用审核 JSON：`neon-teahouse-ui-review/v2`
- AIToUGUI Lite bundle JSON
- WebGAL 修改后的 `*.scss` 或 `userStyleSheet.css`
- WebGAL 原始文件备份 `*.bak`
