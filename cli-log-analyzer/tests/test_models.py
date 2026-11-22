from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from logtool.models import LogRecord, ParseError
from logtool.timeparse import parse_timestamp

VALID = (
    "10.0.0.1 - - [10/Oct/2024:13:55:36 +0000] "
    '"GET /index.html HTTP/1.1" 200 2326 "-" "curl/7.81.0"'
)


def test_from_line_parses_all_fields() -> None:
    record = LogRecord.from_line(VALID)
    assert record.ip == "10.0.0.1"
    assert record.timestamp == datetime(2024, 10, 10, 13, 55, 36, tzinfo=UTC)
    assert (record.method, record.path) == ("GET", "/index.html")
    assert (record.status, record.size) == (200, 2326)
    assert record.agent == "curl/7.81.0"


def test_dash_size_becomes_zero() -> None:
    assert LogRecord.from_line(VALID.replace("200 2326", "304 -")).size == 0


def test_common_log_format_without_agent() -> None:
    line = '10.0.0.9 - - [10/Oct/2024:13:55:36 +0000] "GET / HTTP/1.0" 200 10'
    record = LogRecord.from_line(line)
    assert record.agent == ""
    assert record.path == "/"


@pytest.mark.parametrize(
    "line",
    [
        "### corrupted entry 999 -- disk hiccup ###",
        '10.0.0.1 - - [10/Oct/2024:13:55:36 +0000] "get / HTTP/1.1" 200 1',
        '10.0.0.1 - - [10/Oct/2024:13:55:36 +0000] "GET / HTTP/1.1" 2000 1',
    ],
)
def test_invalid_lines_raise_parse_error(line: str) -> None:
    with pytest.raises(ParseError):
        LogRecord.from_line(line)


def test_bad_timestamp_reason() -> None:
    line = VALID.replace("10/Oct/2024", "10/Foo/2024")
    with pytest.raises(ParseError, match="bad timestamp") as excinfo:
        LogRecord.from_line(line)
    assert excinfo.value.line == line


@pytest.mark.parametrize(
    ("status", "expected_class", "expected_error"),
    [(200, "2xx", False), (304, "3xx", False), (404, "4xx", True), (503, "5xx", True)],
)
def test_status_helpers(status: int, expected_class: str, expected_error: bool) -> None:
    record = LogRecord.from_line(VALID.replace(" 200 ", f" {status} "))
    assert record.status_class == expected_class
    assert record.is_error is expected_error


def test_str_and_frozen() -> None:
    record = LogRecord.from_line(VALID)
    assert str(record) == "2024-10-10 13:55:36 10.0.0.1 GET /index.html -> 200"
    with pytest.raises(FrozenInstanceError):
        record.status = 500  # type: ignore[misc]


def test_parse_timestamp_handles_offsets() -> None:
    ts = parse_timestamp("10/Oct/2024:15:55:36 +0200")
    assert ts == datetime(2024, 10, 10, 13, 55, 36, tzinfo=UTC)
