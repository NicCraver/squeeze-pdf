# -*- mode: python ; coding: utf-8 -*-
# Windows onedir build: dist/squeeze-pdf/squeeze-pdf.exe
#
# Requires WebView2 Runtime on the target machine (pywebview backend).
# PyMuPDF ships libmupdf and mupdf-devel data beside the Python package.
# PyInstaller does not auto-detect these; collect_data_files/collect_dynamic_libs
# (or a custom hook) are required. See pymupdf docs / PyInstaller hook notes.

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None
project_root = Path(SPECPATH).resolve().parent.parent

pymupdf_datas = collect_data_files("pymupdf")
pymupdf_binaries = collect_dynamic_libs("pymupdf")

static_src = project_root / "backend" / "static"

a = Analysis(
    [str(project_root / "client" / "app.py")],
    pathex=[str(project_root)],
    binaries=pymupdf_binaries,
    datas=[
        (str(static_src), "backend/static"),
        *pymupdf_datas,
    ],
    hiddenimports=[
        "fitz",
        "pymupdf",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "webview",
        "client.bridge",
        "backend.server",
        "backend.api.routes",
        "backend.api.ws",
        "backend.api.jobs",
        "backend.squeeze.compressor",
        "backend.squeeze.types",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="squeeze-pdf",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="squeeze-pdf",
)
