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
