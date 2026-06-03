# squeeze-pdf 桌面客户端重构设计

> 日期：2026-06-02  
> 状态：已批准  
> 决策：macOS + Windows 双平台；仅桌面客户端，不保留 CLI

## 背景

现有 `squeeze.py` 为单文件 CLI，通过 PyMuPDF 栅格化 + JPEG 压缩将 PDF 压到指定体积上限。需重构为带 GUI 的跨平台桌面应用，后端 Python、前端 Vue 3 + Vite+，由 Python 打包客户端。

## 目标

- 提供简洁美观的桌面 GUI，替代 CLI
- macOS 与 Windows 双平台发布
- 保持良好压缩性能（多 PDF 并行）
- 前后端分离，便于独立开发与测试

## 非目标

- 不保留 `python squeeze.py` CLI 入口
- 不做 Web 在线版
- 第一版不做 OCR / 保留文本层

## 方案选型

采用 **pywebview + 内嵌 FastAPI**（方案 A）：

- pywebview 提供原生窗口（macOS WebKit / Windows WebView2）
- FastAPI 托管 Vue 构建产物并提供 REST + WebSocket API
- PyInstaller 各平台独立打包

未选方案 B（JS Bridge 直连）：前后端耦合高，进度推送复杂。  
未选方案 C（NiceGUI/Flet）：不符合 Vite+ Vue3 要求。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│  pywebview 原生窗口 (macOS WebKit / Windows WebView2)    │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Vue 3 + Vite+ + UnoCSS (apps/desktop-ui)       │  │
│  │  · 拖拽/选择 PDF  · 体积上限滑块  · 进度与结果     │  │
│  └───────────────────────┬───────────────────────────┘  │
└──────────────────────────┼──────────────────────────────┘
                           │ HTTP + WebSocket
┌──────────────────────────▼──────────────────────────────┐
│  FastAPI (backend/)                                      │
│  · POST /api/jobs        创建压缩任务                     │
│  · GET  /api/jobs/{id}   查询状态                         │
│  · WS   /api/ws          实时进度推送                     │
│  · bridge 转发原生文件/目录对话框                          │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  squeeze 核心库 (backend/squeeze/)                        │
│  · compress_pdf()  · ProcessPoolExecutor 并行            │
└─────────────────────────────────────────────────────────┘
```

## 目录结构

```
squeeze-pdf/
├── apps/
│   └── desktop-ui/              # Vue 3 + Vite+ + UnoCSS
│       ├── src/
│       │   ├── App.vue
│       │   ├── components/      # DropZone, FileList, ProgressPanel
│       │   └── composables/     # useCompressJob, useWebSocket
│       └── package.json
├── backend/
│   ├── squeeze/                 # 压缩核心（原 squeeze.py 逻辑）
│   │   ├── compressor.py
│   │   └── types.py
│   ├── api/
│   │   ├── routes.py
│   │   └── ws.py
│   ├── server.py                # FastAPI 工厂 + 静态资源挂载
│   └── __init__.py
├── client/
│   ├── app.py                   # pywebview 启动器
│   ├── bridge.py                # 原生对话框等桥接
│   └── pyinstaller/
│       ├── squeeze-pdf-macos.spec
│       └── squeeze-pdf-win.spec
├── package.json                 # Vite+ monorepo 根
├── pyproject.toml               # Python 依赖与脚本
├── AGENTS.md
└── docs/superpowers/
    ├── specs/
    └── plans/
```

## 技术栈

| 层级 | 选型 | 说明 |
|------|------|------|
| 前端 | Vue 3 + Vite+ + UnoCSS + VueUse | 简洁 UI，响应式布局 |
| 后端 | FastAPI + uvicorn | 异步 API + WebSocket |
| PDF | PyMuPDF (`fitz`) | 沿用现有压缩算法 |
| 并行 | `ProcessPoolExecutor` | 多 PDF 并行，worker = CPU-1 |
| 客户端壳 | pywebview | macOS WebKit / Windows WebView2 |
| 打包 | PyInstaller | 各平台独立 spec |

## 核心数据流

1. 用户拖拽或选择 PDF → 前端 POST `/api/jobs`（文件路径 + `max_mb` + `output_dir`）
2. 后端创建任务 ID，进程池执行压缩
3. WebSocket 推送：`{ file, status, progress, src_size, dst_size, zoom, quality, error? }`
4. 完成后展示结果，「打开输出目录」通过 bridge 调用系统文件管理器

## API 设计

### POST /api/jobs

请求：

```json
{
  "files": ["/path/to/a.pdf", "/path/to/b.pdf"],
  "max_mb": 1.0,
  "output_dir": "/path/to/output"
}
```

响应：

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

### GET /api/jobs/{job_id}

返回任务状态与每个文件的结果摘要。

### WebSocket /api/ws?job_id={id}

推送任务级与文件级进度事件。

## UI 设计

- **布局**：左侧参数面板（体积上限滑块、输出目录），右侧文件列表 + 进度
- **交互**：大面积拖拽区、多文件选择、单文件失败不中断批次
- **结果**：压缩前后体积、压缩率、zoom/quality 参数
- **视觉**：中性灰 + teal 强调色，支持浅色/深色模式
- **原则**：极简、信息密度适中、操作路径 ≤ 3 步完成压缩

## 双平台打包

| 平台 | pywebview 后端 | 产物 | 注意 |
|------|----------------|------|------|
| macOS | WebKit（系统内置） | `.app` | 可选代码签名 |
| Windows | WebView2 | `.exe` | 需检测/引导 WebView2 Runtime |

构建流程：

```bash
vp run desktop-ui#build          # 前端 → backend/static/
pyinstaller client/pyinstaller/squeeze-pdf-{platform}.spec
```

## 错误处理

- 单文件失败不中断批次，错误写入该文件结果项
- WebSocket 断线自动重连（VueUse `useWebSocket`）
- 本地端口占用时自动递增
- 无法在目标体积内压缩时显示警告（沿用现有逻辑）

## 压缩算法（不变）

- zoom 预设：2.0 → 1.75 → 1.5 → 1.25 → 1.0 → 0.85 → 0.72 → 0.6
- JPEG quality：85 递减至 20（步长 5）
- 搜索策略：先固定 zoom 遍历 quality，再降低 zoom

## 迁移与清理

- `squeeze.py` 逻辑迁移至 `backend/squeeze/compressor.py` 后删除
- 删除 `requirements.txt`，改由 `pyproject.toml` 管理
- 更新 `.squeeze-pdf-intro.md`、飞书云文档、`AGENTS.md`

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| Windows 无 WebView2 | 启动时检测，引导安装 |
| PyInstaller 体积大 | 排除无关模块，UPX 可选 |
| 大文件并行内存占用 | 限制 worker 数，队列化任务 |
