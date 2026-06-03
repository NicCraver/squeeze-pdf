# Agent 指南

## 项目简介

**squeeze-pdf** 是已实现的跨平台桌面应用（macOS / Windows），用于将 PDF 批量压缩到指定体积上限。架构为 **Python 后端（FastAPI）+ Vue 3 前端（Vite+）+ pywebview 壳 + PyInstaller 打包**，无 CLI 入口。

- 压缩核心：`backend/squeeze/compressor.py`
- 前端：`apps/desktop-ui/`
- 客户端入口：`python -m client.app`
- macOS 打包：`./scripts/build-macos.sh`
- 架构设计：`docs/superpowers/specs/2026-06-02-desktop-refactor-design.md`
- 实施计划：`docs/superpowers/plans/2026-06-02-desktop-refactor.md`

## 开发流程

```bash
cd /Users/nic/NicProjects/squeeze-pdf

# 1. Python 虚拟环境与依赖
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. 前端依赖
vp install

# 3. 构建前端 → backend/static/
vp run desktop-ui#build

# 4. 启动桌面客户端
python -m client.app
```

生产构建：

```bash
./scripts/build-macos.sh              # dist/squeeze-pdf.app + squeeze-pdf-macOS.dmg
# Windows（在 Windows 上）:
# .\scripts\build-win.ps1             # squeeze-pdf-Windows-Setup.exe
```

## GitHub Actions 打包 CI

参考 `/Users/nic/w/py-caj-pdf` 的 `.github/workflows/build.yml`。

| 工作流 | 说明 |
|--------|------|
| `test` | Ubuntu 上 `pytest` |
| `build` | macOS DMG + Windows Inno Setup 安装包 |
| `release` | push 到 `main`/`master` 或 tag `v*` 时发布到 GitHub Releases |

产物：

- `squeeze-pdf-macOS.dmg`
- `squeeze-pdf-Windows-Setup.exe`

在 macOS 上拉取 Windows 安装包（需 `gh` CLI 且仓库已推送）：

```bash
./scripts/fetch_windows_build.sh
```

手动触发：GitHub **Actions** → **Build** → **Run workflow**。

运行测试：

```bash
source .venv/bin/activate && pytest tests/ -v
```

## 飞书云文档

| 项 | 值 |
|---|---|
| 标题 | squeeze-pdf 项目介绍 |
| 文档 ID | `GSZhdqA0xoqLtdx7svzcrIWdnkg` |
| 链接 | https://tjmeiteng.feishu.cn/docx/GSZhdqA0xoqLtdx7svzcrIWdnkg |
| 本地源文件 | `.squeeze-pdf-intro.md` |

本地 Markdown 是云文档内容的**源文件**。更新介绍时先改 `.squeeze-pdf-intro.md`，再同步到飞书。

## 前置条件

- 已安装 [lark-cli](https://github.com/larksuite/cli)（本项目使用 `~/.vite-plus/bin/lark-cli`）
- 执行前检查授权：`lark-cli auth status`
- **创建 / 更新云文档**使用 bot 身份（`--as bot`），无需用户 OAuth 的 `docx:document:create` 权限；创建后 CLI 会自动为当前用户授予可管理权限
- `@file` 引用必须是**相对路径**，需先 `cd` 到项目根目录

若需以用户身份读取文档，可补充授权：

```bash
lark-cli auth login --scope "docx:document:create docx:document:readonly"
```

## 同步流程

### 1. 更新本地源文件

编辑 `.squeeze-pdf-intro.md`，保持结构与现有章节一致（概述、核心能力、工作原理、安装、使用方法等）。

### 2. 全量同步到云文档

内容有实质变更时，用 `overwrite` 覆盖远程文档：

```bash
cd /Users/nic/NicProjects/squeeze-pdf

lark-cli docs +update \
  --api-version v2 \
  --as bot \
  --doc GSZhdqA0xoqLtdx7svzcrIWdnkg \
  --command overwrite \
  --doc-format markdown \
  --content @.squeeze-pdf-intro.md
```

建议先 dry-run 预览请求：

```bash
lark-cli docs +update ... --dry-run
```

### 3. 追加编辑时间

每次同步完成后，在文档**末尾**追加编辑时间（不要写进 `.squeeze-pdf-intro.md`，避免下次 overwrite 重复堆叠）：

```bash
cd /Users/nic/NicProjects/squeeze-pdf

EDIT_TIME="$(date '+%Y-%m-%d %H:%M:%S %Z')"

lark-cli docs +update \
  --api-version v2 \
  --as bot \
  --doc GSZhdqA0xoqLtdx7svzcrIWdnkg \
  --command append \
  --doc-format markdown \
  --content $'\n\n*编辑时间：'"${EDIT_TIME}"'*'
```

### 4. 首次创建（仅文档不存在时）

```bash
cd /Users/nic/NicProjects/squeeze-pdf

lark-cli docs +create \
  --api-version v2 \
  --as bot \
  --doc-format markdown \
  --content @.squeeze-pdf-intro.md \
  --title "squeeze-pdf 项目介绍"
```

创建成功后，将返回的 `document_id` 与 `url` 更新到本文「飞书云文档」表格。

## API 版本说明

- 必须使用 **`--api-version v2`**；v1 已弃用
- v2 创建 / 更新用 **`--doc-format markdown --content`**，不是 v1 的 `--markdown`
- v2 更新用 **`--command`**（`overwrite` | `append` | `str_replace` 等），不是 v1 的 `--mode`

## Agent 检查清单

同步云文档时：

- [ ] 先改 `.squeeze-pdf-intro.md`，再执行飞书同步
- [ ] 在项目根目录执行命令（`@file` 相对路径要求）
- [ ] 全量同步用 `--command overwrite`
- [ ] 同步后追加编辑时间（`append`）
- [ ] 向用户返回文档链接
- [ ] 若文档 ID 变更，同步更新本文表格

## 常见问题

| 现象 | 处理 |
|------|------|
| `missing scope: docx:document:create` | 改用 `--as bot`，或执行上方 `auth login` 补授权 |
| `--file must be a relative path` | `cd` 到项目根，使用 `@.squeeze-pdf-intro.md` |
| `--content is required` | v2 需 `--doc-format markdown --content`，不能用 v1 的 `--markdown` |
| 编辑时间重复出现 | 编辑时间仅通过 `append` 追加，不要写入 `.squeeze-pdf-intro.md` |
