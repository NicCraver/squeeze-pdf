from __future__ import annotations

import asyncio
import queue
import threading
import uuid
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from enum import Enum
from multiprocessing import cpu_count
from pathlib import Path

from backend.squeeze.compressor import compress_pdf


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


@dataclass
class Job:
    id: str
    status: JobStatus
    files: list[str]
    max_mb: float
    output_dir: str
    results: list[dict] = field(default_factory=list)
    error: str | None = None


class EventBus:
    """Thread-safe pub/sub with sync queues bridged to asyncio consumers."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[queue.Queue]] = {}
        self._lock = threading.Lock()

    def subscribe(self, job_id: str) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        with self._lock:
            self._subscribers.setdefault(job_id, []).append(q)
        return q

    def unsubscribe(self, job_id: str, q: queue.Queue) -> None:
        with self._lock:
            subs = self._subscribers.get(job_id, [])
            if q in subs:
                subs.remove(q)
            if not subs:
                self._subscribers.pop(job_id, None)

    def emit(self, job_id: str, event: dict) -> None:
        with self._lock:
            queues = list(self._subscribers.get(job_id, []))
        for q in queues:
            q.put(event)


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._executor = ProcessPoolExecutor(max_workers=max(1, cpu_count() - 1))
        self.event_bus = EventBus()

    def create_job(self, files: list[str], max_mb: float, output_dir: str) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            status=JobStatus.queued,
            files=files,
            max_mb=max_mb,
            output_dir=output_dir,
        )
        self._jobs[job_id] = job
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()
        return job

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def _run_job(self, job_id: str) -> None:
        job = self._jobs[job_id]
        job.status = JobStatus.running
        target_bytes = int(job.max_mb * 1024 * 1024)
        try:
            for file_path in job.files:
                file_name = Path(file_path).name
                self.event_bus.emit(job_id, {"type": "file_start", "file": file_name})
                future = self._executor.submit(
                    _compress_one, file_path, job.output_dir, target_bytes
                )
                result = future.result()
                self.event_bus.emit(
                    job_id,
                    {
                        "type": "file_done",
                        "file": file_name,
                        "src_size": result["src_size"],
                        "dst_size": result["dst_size"],
                        "zoom": result["zoom"],
                        "quality": result["quality"],
                        "exceeded_target": result["exceeded_target"],
                        "error": result["error"],
                    },
                )
                job.results.append(result)
            job.status = JobStatus.done
            self.event_bus.emit(job_id, {"type": "job_done", "job_id": job_id})
        except Exception as exc:
            job.status = JobStatus.failed
            job.error = str(exc)
            self.event_bus.emit(job_id, {"type": "job_failed", "error": str(exc)})


def _compress_one(file_path: str, output_dir: str, target_bytes: int) -> dict:
    src = Path(file_path)
    dst = Path(output_dir) / f"{src.stem}_compressed.pdf"
    result = compress_pdf(src, dst, target_bytes)
    return asdict(result)


job_manager = JobManager()
