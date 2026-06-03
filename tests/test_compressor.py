from pathlib import Path

from backend.squeeze import CompressResult, compress_pdf
from backend.squeeze.compressor import QUALITY_LEVELS, ZOOM_LEVELS


def test_compress_result_structure() -> None:
    result = CompressResult(
        src_path="/tmp/source.pdf",
        dst_path="/tmp/output.pdf",
        src_size=2048,
        dst_size=1024,
        zoom=1.5,
        quality=75,
        exceeded_target=False,
    )
    assert result.error is None
    assert result.src_path == "/tmp/source.pdf"
    assert result.dst_path == "/tmp/output.pdf"
    assert result.src_size == 2048
    assert result.dst_size == 1024
    assert result.zoom == 1.5
    assert result.quality == 75
    assert result.exceeded_target is False


def test_compression_constants() -> None:
    assert ZOOM_LEVELS == (2.0, 1.75, 1.5, 1.25, 1.0, 0.85, 0.72, 0.6)
    assert QUALITY_LEVELS[0] == 85
    assert QUALITY_LEVELS[-1] == 15


def test_compress_pdf_missing_source_returns_error() -> None:
    result = compress_pdf(
        Path("/nonexistent/missing.pdf"),
        Path("/tmp/squeeze-test-output.pdf"),
        target_bytes=1024,
    )
    assert result.error is not None
    assert result.dst_size == 0
    assert result.exceeded_target is False
