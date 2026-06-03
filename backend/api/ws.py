from __future__ import annotations

import asyncio
import queue

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.jobs import JobStatus, job_manager

router = APIRouter()


async def _wait_for_job(job_id: str, timeout: float = 5.0) -> bool:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if job_manager.get_job(job_id) is not None:
            return True
        await asyncio.sleep(0.05)
    return False


async def _forward_events(websocket: WebSocket, sync_q: queue.Queue) -> None:
    while True:
        try:
            event = sync_q.get_nowait()
        except queue.Empty:
            await asyncio.sleep(0.05)
            continue
        await websocket.send_json(event)
        if event.get("type") in ("job_done", "job_failed"):
            break


@router.websocket("/api/ws")
async def job_progress(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()

    if not await _wait_for_job(job_id):
        await websocket.close(code=4004, reason="Job not found")
        return

    job = job_manager.get_job(job_id)
    assert job is not None

    if job.status == JobStatus.done:
        await websocket.send_json({"type": "job_done", "job_id": job_id})
        return
    if job.status == JobStatus.failed:
        await websocket.send_json(
            {"type": "job_failed", "error": job.error or "Job failed"}
        )
        return

    sync_q = job_manager.event_bus.subscribe(job_id)
    try:
        await _forward_events(websocket, sync_q)
    except WebSocketDisconnect:
        pass
    finally:
        job_manager.event_bus.unsubscribe(job_id, sync_q)
