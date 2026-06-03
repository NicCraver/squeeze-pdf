# squeeze-pdf 桌面客户端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 squeeze-pdf 从 CLI 重构为 macOS/Windows 双平台桌面应用（Python 后端 + Vue 3/Vite+ 前端 + pywebview 壳 + PyInstaller 打包）。

**Architecture:** pywebview 加载内嵌 FastAPI 服务的 Vue 静态页；压缩逻辑抽至 `backend/squeeze/`；WebSocket 推送进度；ProcessPoolExecutor 并行处理多 PDF。

**Tech Stack:** Python 3.12+, FastAPI, uvicorn, PyMuPDF, pywebview, PyInstaller, Vue 3, Vite+, UnoCSS, VueUse

**Spec:** `docs/superpowers/specs/2026-06-02-desktop-refactor-design.md`

---

## 文件结构概览

| 文件 | 职责 |
|------|------|
| `backend/squeeze/compressor.py` | PDF 压缩核心（从 squeeze.py 迁移） |
| `backend/squeeze/types.py` | CompressResult 等类型 |
| `backend/api/routes.py` | REST 路由 |
| `backend/api/ws.py` | WebSocket 进度推送 |
| `backend/server.py` | FastAPI 应用工厂 + 静态资源 |
| `client/app.py` | pywebview 启动入口 |
| `client/bridge.py` | 原生文件/目录对话框 |
| `apps/desktop-ui/` | Vue 3 前端 |
| `pyproject.toml` | Python 依赖 |
| `package.json` | Vite+ monorepo 根 |

---

### Task 1: Python 项目骨架与核心库迁移

**Files:**
- Create: `pyproject.toml`
- Create: `backend/__init__.py`
- Create: `backend/squeeze/__init__.py`
- Create: `backend/squeeze/types.py`
- Create: `backend/squeeze/compressor.py`
- Delete: `squeeze.py`（Task 8 完成后）
- Delete: `requirements.txt`（Task 8 完成后）

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "squeeze-pdf"
version = "0.2.0"
requires-python = ">=3.12"
dependencies = [
  "pymupdf>=1.24.0",
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.32.0",
  "pywebview>=5.0",
]

[project.optional-dependencies]
dev = ["pyinstaller>=6.0", "httpx>=0.27", "pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: 创建 types.py**

```python
from dataclasses import dataclass

@dataclass
class CompressResult:
    src_path: str
    dst_path: str
    src_size: int
    dst_size: int
    zoom: float
    quality: int
    exceeded_target: bool
    error: str | None = None
```

- [ ] **Step 3: 迁移 compressor.py**

将 `squeeze.py` 中 `_render_pdf`、`compress_pdf`、`ZOOM_LEVELS`、`QUALITY_LEVELS` 移入 `backend/squeeze/compressor.py`，函数签名改为接受/返回 `Path` 与 `CompressResult`，`print` 警告改为返回 `exceeded_target=True`。

- [ ] **Step 4: 验证核心库**

```bash
cd /Users/nic/NicProjects/squeeze-pdf
source .venv/bin/activate
pip install -e ".[dev]"
python -c "from backend.squeeze.compressor import compress_pdf; print('ok')"
```

Expected: 输出 `ok`

---

### Task 2: FastAPI 服务与任务 API

**Files:**
- Create: `backend/server.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/routes.py`
- Create: `backend/api/jobs.py`
- Create: `backend/api/ws.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: 实现 jobs 内存任务管理器 `backend/api/jobs.py`**

```python
import uuid
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

@dataclass
class Job:
    id: str
    status: JobStatus
    files: list[str]
    max_mb: float
    output_dir: str
    results: list[dict] = field(default_factory=list)

class JobManager:
    def __init__(self, max_workers: int | None = None):
        import os
        self._jobs: dict[str, Job] = {}
        self._executor = ProcessPoolExecutor(
            max_workers=max_workers or max(1, (os.cpu_count() or 2) - 1)
        )

    def create(self, files: list[str], max_mb: float, output_dir: str) -> Job: ...
    def get(self, job_id: str) -> Job | None: ...
```

- [ ] **Step 2: 实现 routes.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api")

class CreateJobRequest(BaseModel):
    files: list[str]
    max_mb: float = 1.0
    output_dir: str

@router.post("/jobs")
def create_job(req: CreateJobRequest): ...

@router.get("/jobs/{job_id}")
def get_job(job_id: str): ...
```

- [ ] **Step 3: 实现 server.py**

```python
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.api.routes import router

STATIC_DIR = Path(__file__).parent / "static"

def create_app() -> FastAPI:
    app = FastAPI(title="squeeze-pdf")
    app.include_router(router)
    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app
```

- [ ] **Step 4: 编写 API 测试**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from backend.server import create_app

def test_health():
    client = TestClient(create_app())
    # 静态目录未构建时仅测 API
    r = client.post("/api/jobs", json={"files": [], "max_mb": 1.0, "output_dir": "/tmp/out"})
    assert r.status_code in (200, 422)
```

- [ ] **Step 5: 运行测试**

```bash
pytest tests/test_api.py -v
```

---

### Task 3: WebSocket 进度推送

**Files:**
- Modify: `backend/api/ws.py`
- Modify: `backend/api/jobs.py`
- Create: `tests/test_ws.py`

- [ ] **Step 1: 实现 ws.py**

```python
from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/api/ws")
async def job_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    # 订阅 job_id 对应的事件队列，推送 JSON 事件
```

事件格式：

```json
{"type": "file_start", "file": "a.pdf"}
{"type": "file_done", "file": "a.pdf", "src_size": 4520000, "dst_size": 980200, "zoom": 1.5, "quality": 75}
{"type": "job_done", "job_id": "..."}
```

- [ ] **Step 2: jobs 执行时 publish 事件到 ws 订阅者**

- [ ] **Step 3: 运行 ws 测试**

```bash
pytest tests/test_ws.py -v
```

---

### Task 4: Vite+ Monorepo 与 Vue 前端脚手架

**Files:**
- Create: `package.json`
- Create: `apps/desktop-ui/package.json`
- Create: `apps/desktop-ui/index.html`
- Create: `apps/desktop-ui/vite.config.ts`
- Create: `apps/desktop-ui/src/main.ts`
- Create: `apps/desktop-ui/src/App.vue`
- Create: `apps/desktop-ui/uno.config.ts`

- [ ] **Step 1: 创建 monorepo 根 package.json**

```json
{
  "name": "squeeze-pdf",
  "private": true,
  "workspaces": ["apps/*"],
  "scripts": {
    "dev": "vp run desktop-ui#dev",
    "build": "vp run desktop-ui#build",
    "prepare": "vp config"
  },
  "devDependencies": { "vite-plus": "latest" },
  "engines": { "node": ">=22.12.0" },
  "packageManager": "npm@11.12.0"
}
```

- [ ] **Step 2: 创建 desktop-ui 应用**

Vue 3 + script setup + UnoCSS + VueUse。`vite.config.ts` 设置 `build.outDir: '../../backend/static'`。

- [ ] **Step 3: 安装依赖并验证 dev**

```bash
vp install
vp run desktop-ui#dev
```

Expected: 前端 dev server 启动

- [ ] **Step 4: 构建静态资源**

```bash
vp run desktop-ui#build
ls backend/static/index.html
```

---

### Task 5: Vue UI 组件

**Files:**
- Create: `apps/desktop-ui/src/components/DropZone.vue`
- Create: `apps/desktop-ui/src/components/FileList.vue`
- Create: `apps/desktop-ui/src/components/SettingsPanel.vue`
- Create: `apps/desktop-ui/src/components/ResultCard.vue`
- Create: `apps/desktop-ui/src/composables/useCompressJob.ts`

- [ ] **Step 1: SettingsPanel — 体积上限滑块 (0.1–10 MB) + 输出目录选择**

- [ ] **Step 2: DropZone — 拖拽 PDF + 点击选择（调用 bridge 或 input）**

- [ ] **Step 3: useCompressJob — POST /api/jobs + WebSocket 订阅**

```typescript
export function useCompressJob() {
  const status = ref<'idle' | 'running' | 'done'>('idle')
  const files = ref<FileItem[]>([])

  async function start(files: string[], maxMb: number, outputDir: string) {
    const res = await fetch('/api/jobs', { method: 'POST', ... })
    const { job_id } = await res.json()
    // useWebSocket(`/api/ws?job_id=${job_id}`)
  }

  return { status, files, start }
}
```

- [ ] **Step 4: FileList + ResultCard — 展示进度与结果**

- [ ] **Step 5: App.vue 组装布局**

左侧 SettingsPanel，右侧 DropZone + FileList。UnoCSS：`bg-gray-50 dark:bg-gray-900`，强调色 `text-teal-600`。

---

### Task 6: pywebview 客户端与 Bridge

**Files:**
- Create: `client/__init__.py`
- Create: `client/bridge.py`
- Create: `client/app.py`

- [ ] **Step 1: bridge.py**

```python
import webview

class Api:
    def pick_files(self) -> list[str]:
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True,
            file_types=('PDF Files (*.pdf)', '*.pdf')
        )
        return list(result or [])

    def pick_output_dir(self) -> str | None:
        result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None

    def open_folder(self, path: str) -> None:
        import subprocess, sys
        if sys.platform == "darwin":
            subprocess.run(["open", path])
        elif sys.platform == "win32":
            subprocess.run(["explorer", path])
```

- [ ] **Step 2: app.py 启动 FastAPI + pywebview**

```python
import threading
import socket
import uvicorn
import webview
from backend.server import create_app
from client.bridge import Api

def find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def main():
    port = find_free_port()
    app = create_app()
    server = threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning"),
        daemon=True,
    )
    server.start()
    webview.create_window("squeeze-pdf", f"http://127.0.0.1:{port}", js_api=Api())
    webview.start()

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 联调验证**

```bash
python -m client.app
```

Expected: 原生窗口打开，UI 可见，可选文件并触发压缩

---

### Task 7: PyInstaller 双平台打包

**Files:**
- Create: `client/pyinstaller/squeeze-pdf-macos.spec`
- Create: `client/pyinstaller/squeeze-pdf-win.spec`
- Create: `scripts/build-macos.sh`
- Create: `scripts/build-win.ps1`

- [ ] **Step 1: macOS spec — 打包 backend/static、PyMuPDF 数据文件**

- [ ] **Step 2: Windows spec — 同上，注意 WebView2 检测脚本**

- [ ] **Step 3: build 脚本**

```bash
# scripts/build-macos.sh
vp run desktop-ui#build
pyinstaller client/pyinstaller/squeeze-pdf-macos.spec --noconfirm
```

- [ ] **Step 4: macOS 本地验证**

```bash
open dist/squeeze-pdf.app
```

---

### Task 8: 清理、文档与飞书同步

**Files:**
- Delete: `squeeze.py`, `requirements.txt`
- Modify: `.squeeze-pdf-intro.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: 删除旧 CLI 文件**

- [ ] **Step 2: 更新 `.squeeze-pdf-intro.md`（桌面版架构说明）**

- [ ] **Step 3: 更新 `AGENTS.md` 开发与打包命令**

- [ ] **Step 4: 同步飞书云文档**

```bash
lark-cli docs +update --api-version v2 --as bot \
  --doc GSZhdqA0xoqLtdx7svzcrIWdnkg \
  --command overwrite --doc-format markdown \
  --content @.squeeze-pdf-intro.md
```

- [ ] **Step 5: 追加编辑时间**

---

## 验证清单

- [ ] `pytest tests/ -v` 全部通过
- [ ] `python -m client.app` 可完成端到端压缩
- [ ] macOS `.app` 可独立运行
- [ ] Windows `.exe` 在含 WebView2 的环境可运行
- [ ] 飞书云文档已更新架构章节
