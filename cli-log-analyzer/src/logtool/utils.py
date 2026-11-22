"""Reusable context managers and decorators."""

from __future__ import annotations

import functools
import gzip
import logging
import time
import warnings
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import TracebackType
from typing import ParamSpec, TextIO, TypeVar

log = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


@contextmanager
def open_log(path: str | Path) -> Iterator[TextIO]:
    """Open a plain or gzip-compressed log file for reading as text."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"log file not found: {p}")
    log.debug("opening %s", p)
    try:
        if p.suffix == ".gz":
            with gzip.open(p, "rt", encoding="utf-8", errors="replace") as gz:
                yield gz
        else:
            with open(p, encoding="utf-8", errors="replace") as fh:
                yield fh
    finally:
        log.debug("closed %s", p)


class Timer:
    """Class-based context manager that measures the wall time of a block."""

    def __init__(self, label: str = "block") -> None:
        self.label = label
        self.elapsed = 0.0
        self._start = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # Runs even when the block raises; returning None does not suppress it.
        self.elapsed = time.perf_counter() - self._start
        log.info("%s took %.3fs", self.label, self.elapsed)


def timed(func: Callable[P, R]) -> Callable[P, R]:
    """Log how long each call to *func* takes (INFO level)."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            log.info("%s took %.4fs", func.__qualname__, elapsed)

    return wrapper


def deprecated(reason: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator factory: emit DeprecationWarning whenever func is called."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            warnings.warn(
                f"{func.__name__}() is deprecated: {reason}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator
