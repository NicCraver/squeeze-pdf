from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.server import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _make_pdf(path: Path) -> None:
    doc = fitz.open()
    doc.new_page()
    doc.save(path)
    doc.close()


def test_websocket_receives_job_progress_events(client: TestClient, tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_pdf(pdf_path)
    output_dir = tmp_path / "output"

    response = client.post(
        "/api/jobs",
        json={
            "files": [str(pdf_path)],
            "max_mb": 1.0,
            "output_dir": str(output_dir),
        },
    )
    assert response.status_code == 200
    job_id = response.json()["id"]

    events: list[dict] = []
    with client.websocket_connect(f"/api/ws?job_id={job_id}") as websocket:
        while True:
            event = websocket.receive_json()
            events.append(event)
            if event["type"] in ("job_done", "job_failed"):
                break

    event_types = [event["type"] for event in events]
    assert "file_start" in event_types or "job_done" in event_types
    assert event_types[-1] == "job_done"
    assert events[-1]["job_id"] == job_id

    if "file_start" in event_types:
        file_start = next(e for e in events if e["type"] == "file_start")
        assert file_start["file"] == "sample.pdf"

    if "file_done" in event_types:
        file_done = next(e for e in events if e["type"] == "file_done")
        assert file_done["file"] == "sample.pdf"
        assert "src_size" in file_done
        assert "dst_size" in file_done


def test_websocket_unknown_job_closes(client: TestClient) -> None:
    with client.websocket_connect("/api/ws?job_id=does-not-exist") as websocket:
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_json()
