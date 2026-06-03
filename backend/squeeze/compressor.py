from __future__ import annotations

import tempfile
from pathlib import Path

import fitz

from backend.squeeze.types import CompressResult

ZOOM_LEVELS = (2.0, 1.75, 1.5, 1.25, 1.0, 0.85, 0.72, 0.6)
QUALITY_LEVELS = tuple(range(85, 14, -5))


def _render_pdf(
    src: fitz.Document,
    zoom: float,
    jpeg_quality: int,
) -> fitz.Document:
    """把每一页栅格化为 JPEG 后写入新 PDF（去掉巨型嵌入字体等）。"""
    out = fitz.open()
    for page in src:
        rect = page.rect
        new_page = out.new_page(width=rect.width, height=rect.height)
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        jpeg = pix.tobytes("jpeg", jpg_quality=jpeg_quality)
        new_page.insert_image(rect, stream=jpeg)
    return out


def compress_pdf(
    src_path: Path,
    dst_path: Path,
    target_bytes: int,
) -> CompressResult:
    """在不超过 target_bytes 的前提下尽量保持清晰度。"""
    try:
        src_size = src_path.stat().st_size
    except OSError as exc:
        return CompressResult(
            src_path=str(src_path),
            dst_path=str(dst_path),
            src_size=0,
            dst_size=0,
            zoom=0.0,
            quality=0,
            exceeded_target=False,
            error=str(exc),
        )

    try:
        src = fitz.open(src_path)
        try:
            best_doc: fitz.Document | None = None
            best_size = 0
            best_zoom = ZOOM_LEVELS[-1]
            best_quality = QUALITY_LEVELS[-1]

            for zoom in ZOOM_LEVELS:
                for quality in QUALITY_LEVELS:
                    candidate = _render_pdf(src, zoom, quality)
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                            tmp_path = Path(tmp.name)
                        candidate.save(tmp_path, garbage=4, deflate=True)
                        size = tmp_path.stat().st_size
                        tmp_path.unlink(missing_ok=True)

                        if size <= target_bytes:
                            dst_path.parent.mkdir(parents=True, exist_ok=True)
                            candidate.save(dst_path, garbage=4, deflate=True)
                            return CompressResult(
                                src_path=str(src_path),
                                dst_path=str(dst_path),
                                src_size=src_size,
                                dst_size=size,
                                zoom=zoom,
                                quality=quality,
                                exceeded_target=False,
                            )

                        if best_doc is None or size < best_size:
                            if best_doc is not None:
                                best_doc.close()
                            best_doc = candidate
                            best_size = size
                            best_zoom = zoom
                            best_quality = quality
                            candidate = None
                    finally:
                        if candidate is not None:
                            candidate.close()

            if best_doc is None:
                raise RuntimeError(f"无法压缩: {src_path}")

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            best_doc.save(dst_path, garbage=4, deflate=True)
            best_doc.close()
            return CompressResult(
                src_path=str(src_path),
                dst_path=str(dst_path),
                src_size=src_size,
                dst_size=best_size,
                zoom=best_zoom,
                quality=best_quality,
                exceeded_target=True,
            )
        finally:
            src.close()
    except Exception as exc:
        return CompressResult(
            src_path=str(src_path),
            dst_path=str(dst_path),
            src_size=src_size,
            dst_size=0,
            zoom=0.0,
            quality=0,
            exceeded_target=False,
            error=str(exc),
        )
