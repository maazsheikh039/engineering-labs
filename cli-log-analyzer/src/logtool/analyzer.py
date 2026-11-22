"""Aggregate statistics over a stream of LogRecord objects."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from itertools import groupby

from logtool.models import LogRecord
from logtool.utils import deprecated


class LogAnalyzer:
    """Single-pass aggregator: memory depends on distinct keys, not on lines."""

    def __init__(self, records: Iterable[LogRecord] = ()) -> None:
        self.total = 0
        self.total_bytes = 0
        self.status_counts: Counter[int] = Counter()
        self.ip_counts: Counter[str] = Counter()
        self.path_counts: Counter[str] = Counter()
        self.first_seen: datetime | None = None
        self.last_seen: datetime | None = None
        self.feed(records)

    def add(self, record: LogRecord) -> None:
        self.total += 1
        self.total_bytes += record.size
        self.status_counts[record.status] += 1
        self.ip_counts[record.ip] += 1
        self.path_counts[record.path] += 1
        if self.first_seen is None or record.timestamp < self.first_seen:
            self.first_seen = record.timestamp
        if self.last_seen is None or record.timestamp > self.last_seen:
            self.last_seen = record.timestamp

    def feed(self, records: Iterable[LogRecord]) -> LogAnalyzer:
        """Consume an iterable; returns self so calls can be chained."""
        for record in records:
            self.add(record)
        return self

    @property
    def error_count(self) -> int:
        return sum(n for status, n in self.status_counts.items() if status >= 400)

    @property
    def error_rate(self) -> float:
        return self.error_count / self.total if self.total else 0.0

    def status_classes(self) -> dict[str, int]:
        classes: Counter[str] = Counter()
        for status, n in self.status_counts.items():
            classes[f"{status // 100}xx"] += n
        return dict(sorted(classes.items()))

    def top(self, field: str, n: int = 5) -> list[tuple[str, int]]:
        counters: dict[str, Counter[str] | Counter[int]] = {
            "ip": self.ip_counts,
            "path": self.path_counts,
            "status": self.status_counts,
        }
        if field not in counters:
            raise ValueError(f"unknown field {field!r}; use one of {sorted(counters)}")
        return [(str(key), count) for key, count in counters[field].most_common(n)]

    def summary(self) -> dict[str, object]:
        return {
            "records": self.total,
            "total_bytes": self.total_bytes,
            "unique_ips": len(self.ip_counts),
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "error_rate": round(self.error_rate, 4),
            "status_classes": self.status_classes(),
        }

    def __len__(self) -> int:
        return self.total

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(records={self.total}, "
            f"errors={self.error_count}, unique_ips={len(self.ip_counts)})"
        )


@deprecated("use LogAnalyzer(records).error_count instead")
def count_errors(records: Iterable[LogRecord]) -> int:
    """Old helper kept for backwards compatibility."""
    return sum(1 for record in records if record.is_error)


def hourly_counts(records: Iterable[LogRecord]) -> list[tuple[str, int]]:
    """Return (YYYY-MM-DD HH:00, count) pairs using itertools.groupby.

    Assumes *records* are already ordered chronologically by timestamp.
    """
    return [
        (hour, sum(1 for _ in group))
        for hour, group in groupby(
            records, key=lambda r: r.timestamp.strftime("%Y-%m-%d %H:00")
        )
    ]
