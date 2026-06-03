from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from backend.server import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_job_empty_files_returns_error(client: TestClient, tmp_path: Path) -> None:
    response = client.post(
        "/api/jobs",
        json={"files": [], "max_mb": 1.0, "output_dir": str(tmp_path / "out")},
    )
    assert response.status_code in (400, 422)


def test_get_nonexistent_job_returns_404(client: TestClient) -> None:
    response = client.get("/api/jobs/does-not-exist")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_job_with_valid_setup(client: TestClient, tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()

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
    data = response.json()
    assert data["id"]
    assert data["status"] in ("queued", "running", "done")
    assert data["files"] == [str(pdf_path)]
    assert data["output_dir"] == str(output_dir)
