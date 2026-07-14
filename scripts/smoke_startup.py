"""Offline startup checks for both application surfaces."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("FORCE_MOCK", "true")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from geo_audit_agent.api.app import app  # noqa: E402


def main() -> None:
    response = TestClient(app).get("/health")
    if response.status_code != 200 or response.json().get("status") != "healthy":
        raise RuntimeError(f"API health smoke failed: {response.status_code} {response.text}")
    streamlit_app = AppTest.from_file("dashboard.py").run(timeout=20)
    if streamlit_app.exception:
        raise RuntimeError(f"Streamlit startup smoke failed: {streamlit_app.exception}")
    print("API and Streamlit startup smoke passed")


if __name__ == "__main__":
    main()
