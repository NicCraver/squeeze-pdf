from __future__ import annotations

import socket
import threading

import uvicorn
import webview

from backend.server import create_app
from client.bridge import Api


def find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    port = find_free_port()
    app = create_app()
    server = threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning"),
        daemon=True,
    )
    server.start()
    webview.create_window(
        "squeeze-pdf",
        f"http://127.0.0.1:{port}",
        js_api=Api(),
        width=1100,
        height=720,
        min_size=(800, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
