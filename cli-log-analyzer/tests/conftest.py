"""Shared pytest fixtures."""

import gzip
from pathlib import Path

import pytest

SAMPLE_LINES = [
    '10.0.0.1 - - [10/Oct/2024:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326 "-" "curl/7.81.0"',
    '10.0.0.2 - - [10/Oct/2024:13:55:37 +0000] "POST /login HTTP/1.1" 401 512 "-" "curl/7.81.0"',
    "this is not a log line",
    '10.0.0.1 - - [10/Oct/2024:13:56:00 +0000] "GET /api/v1/items HTTP/1.1" 500 128 "-" "python-requests/2.31.0"',
    '10.0.0.3 - - [10/Oct/2024:14:01:12 +0000] "GET /index.html HTTP/1.1" 304 -',
    '10.0.0.1 - - [10/Oct/2024:14:05:00 +0000] "GET /api/v1/items HTTP/1.1" 404 64 "-" "Mozilla/5.0"',
]


@pytest.fixture
def sample_lines() -> list[str]:
    return list(SAMPLE_LINES)


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    path = tmp_path / "access.log"
    path.write_text("\n".join(SAMPLE_LINES) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def gz_log_file(tmp_path: Path) -> Path:
    path = tmp_path / "access.log.1.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write("\n".join(SAMPLE_LINES) + "\n")
    return path
