import gzip
import logging
import time
from pathlib import Path

import pytest

from logtool.utils import Timer, deprecated, open_log, timed


def test_open_log_plain_and_gzip(tmp_path: Path) -> None:
    plain = tmp_path / "a.log"
    plain.write_text("hello\n", encoding="utf-8")
    packed = tmp_path / "b.log.gz"
    with gzip.open(packed, "wt", encoding="utf-8") as fh:
        fh.write("packed\n")

    with open_log(plain) as fh:
        assert fh.read() == "hello\n"
    with open_log(packed) as fh:
        assert fh.read() == "packed\n"
    assert fh.closed


def test_open_log_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="log file not found"):
        with open_log(tmp_path / "nope.log"):
            pass


def test_timer_measures_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="logtool.utils")
    with Timer("nap") as timer:
        time.sleep(0.05)
    assert timer.elapsed >= 0.05
    assert "nap took" in caplog.text


def test_timer_records_time_even_on_exception() -> None:
    timer = Timer("boom")
    with pytest.raises(RuntimeError), timer:
        time.sleep(0.01)
        raise RuntimeError("fail")
    assert timer.elapsed >= 0.01


def test_timed_preserves_metadata_and_result(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="logtool.utils")

    @timed
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    assert add(2, 3) == 5
    assert add.__name__ == "add"
    assert add.__doc__ == "Add two numbers."
    assert "add took" in caplog.text


def test_timed_propagates_exceptions() -> None:
    @timed
    def explode() -> None:
        raise KeyError("x")

    with pytest.raises(KeyError):
        explode()


def test_deprecated_warns_and_still_returns() -> None:
    @deprecated("use shiny() instead")
    def rusty() -> str:
        return "ok"

    with pytest.warns(DeprecationWarning, match=r"rusty\(\) is deprecated: use shiny"):
        assert rusty() == "ok"
