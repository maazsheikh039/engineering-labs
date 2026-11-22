"""Lazy, generator-based reading and filtering of log files."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from logtool.models import LogRecord, ParseError
from logtool.utils import open_log

log = logging.getLogger(__name__)


@dataclass
class ParseStats:
    """Mutable counters filled in while records are parsed."""

    lines: int = 0
    malformed: int = 0


def read_lines(paths: Iterable[str | Path]) -> Iterator[str]:
    """Yield non-empty lines from each file in turn (gzip-aware)."""
    for path in paths:
        with open_log(path) as fh:
            for raw in fh:
                line = raw.rstrip("\r\n")
                if line:
                    yield line


def parse_records(
    lines: Iterable[str], stats: ParseStats | None = None
) -> Iterator[LogRecord]:
    """Turn lines into LogRecord objects, skipping (and counting) bad lines."""
    for line in lines:
        if stats is not None:
            stats.lines += 1
        try:
            yield LogRecord.from_line(line)
        except ParseError as exc:
            if stats is not None:
                stats.malformed += 1
            log.debug("skipping line: %s", exc)


def filter_records(
    records: Iterable[LogRecord],
    *,
    status: int | None = None,
    min_status: int | None = None,
    path_prefix: str | None = None,
) -> Iterator[LogRecord]:
    """Yield only the records matching every criterion that is not None."""
    for record in records:
        if status is not None and record.status != status:
            continue
        if min_status is not None and record.status < min_status:
            continue
        if path_prefix is not None and not record.path.startswith(path_prefix):
            continue
        yield record


def between(
    records: Iterable[LogRecord],
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> Iterator[LogRecord]:
    """Yield records whose timestamp falls within [since, until] (inclusive)."""
    for record in records:
        if since is not None and record.timestamp < since:
            continue
        if until is not None and record.timestamp > until:
            continue
        yield record
