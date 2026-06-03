from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.jobs import Job, JobStatus, job_manager

router = APIRouter(prefix="/api")


class CreateJobRequest(BaseModel):
    files: list[str]
    max_mb: float = 1.0
    output_dir: str


def _job_to_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "status": job.status.value,
        "files": job.files,
        "max_mb": job.max_mb,
        "output_dir": job.output_dir,
        "results": job.results,
    }


def _validate_output_dir(output_dir: str) -> None:
    path = Path(output_dir)
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.touch()
        probe.unlink()
    except OSError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"output_dir not writable or creatable: {output_dir}",
        ) from exc


def _validate_files(files: list[str]) -> None:
    if not files:
        raise HTTPException(status_code=400, detail="files must not be empty")

    for file_path in files:
        path = Path(file_path)
        if not path.is_file():
            raise HTTPException(status_code=400, detail=f"File not found: {file_path}")
        if path.suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail=f"Not a PDF file: {file_path}")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/jobs")
def create_job(request: CreateJobRequest) -> dict:
    _validate_files(request.files)
    _validate_output_dir(request.output_dir)
    job = job_manager.create_job(request.files, request.max_mb, request.output_dir)
    return _job_to_dict(job)


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return _job_to_dict(job)
