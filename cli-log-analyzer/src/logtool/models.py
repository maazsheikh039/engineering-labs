"""Domain model: one parsed access-log line."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from logtool.timeparse import parse_timestamp

# Apache/Nginx "combined" format. Referrer and user agent are optional, so the
# shorter "common" format is accepted as well.
LOG_PATTERN = re.compile(
    r"(?P<ip>\S+) \S+ \S+ \[(?P<ts>[^\]]+)\] "
    r'"(?P<method>[A-Z]+) (?P<path>\S+) (?P<protocol>[^"]+)" '
    r"(?P<status>\d{3}) (?P<size>\d+|-)"
    r'(?: "(?P<referrer>[^"]*)" "(?P<agent>[^"]*)")?'
)


class ParseError(ValueError):
    """Raised when a line cannot be turned into a LogRecord."""

    def __init__(self, line: str, reason: str = "unrecognised log format") -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"{reason}: {line[:60]!r}")


@dataclass(frozen=True, slots=True)
class LogRecord:
    """One request. Immutable (frozen) and memory-lean (slots)."""

    ip: str
    timestamp: datetime
    method: str
    path: str
    status: int
    size: int
    agent: str = ""

    @classmethod
    def from_line(cls, line: str) -> LogRecord:
        """Alternative constructor: build a record from one raw log line."""
        text = line.strip()
        match = LOG_PATTERN.match(text)
        if match is None:
            raise ParseError(text)
        try:
            timestamp = parse_timestamp(match["ts"])
        except ValueError as exc:
            raise ParseError(text, "bad timestamp") from exc
        size = match["size"]
        return cls(
            ip=match["ip"],
            timestamp=timestamp,
            method=match["method"],
            path=match["path"],
            status=int(match["status"]),
            size=0 if size == "-" else int(size),
            agent=match["agent"] or "",
        )

    @property
    def is_error(self) -> bool:
        return self.status >= 400

    @property
    def status_class(self) -> str:
        return f"{self.status // 100}xx"

    def __str__(self) -> str:
        return (
            f"{self.timestamp:%Y-%m-%d %H:%M:%S} {self.ip} "
            f"{self.method} {self.path} -> {self.status}"
        )
