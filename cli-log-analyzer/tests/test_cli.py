import json
import subprocess
import sys
from pathlib import Path

import pytest

from logtool import __version__
from logtool.cli import main


def run_json(capsys: pytest.CaptureFixture[str], argv: list[str]) -> tuple[int, dict]:
    code = main([*argv, "--format", "json"])
    return code, json.loads(capsys.readouterr().out)


def test_summary_json(log_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, data = run_json(capsys, ["summary", str(log_file)])
    assert code == 0
    assert data["records"] == 5
    assert data["malformed"] == 1
    assert data["status_classes"]["4xx"] == 2


def test_summary_text_output(
    log_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["summary", str(log_file)]) == 0
    out = capsys.readouterr().out
    assert "records".ljust(18) + " 5" in out
    assert "error_rate".ljust(18) + " 60.00%" in out


def test_top_by_path(log_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, data = run_json(capsys, ["top", str(log_file), "--by", "path", "-n", "1"])
    assert code == 0
    assert data == {"top_path": [["/index.html", 2]]}


def test_errors_with_min_status(
    log_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, data = run_json(capsys, ["errors", str(log_file), "--min-status", "500"])
    assert code == 0
    assert data["error_records"] == 1
    assert data["by_status"] == {"500": 1}


def test_threshold_exit_code(
    log_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["summary", str(log_file), "--fail-on-error-rate", "0.5"]) == 3
    assert "exceeds threshold 50.00%" in capsys.readouterr().err
    assert main(["summary", str(log_file), "--fail-on-error-rate", "0.9"]) == 0


def test_missing_file_returns_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["summary", str(tmp_path / "missing.log")]) == 1
    assert "log file not found" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [
        ["top", "x.log", "--by", "user"],
        ["top", "x.log", "-n", "0"],
        ["summary", "x.log", "--fail-on-error-rate", "1.5"],
        [],
    ],
)
def test_bad_arguments_exit_2(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    assert excinfo.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert capsys.readouterr().out.strip() == f"logtool {__version__}"


def test_python_dash_m_entry_point(log_file: Path) -> None:
    cmd = [sys.executable, "-m", "logtool", "top", str(log_file), "-n", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "10.0.0.1" in result.stdout
