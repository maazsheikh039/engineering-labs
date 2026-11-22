from datetime import UTC, datetime
from pathlib import Path

import pytest

from logtool.analyzer import hourly_counts
from logtool.cli import main
from logtool.reader import between, parse_records
from logtool.reporters import CsvReporter, get_reporter


def test_between_filters_window(sample_lines: list[str]) -> None:
    since = datetime(2024, 10, 10, 13, 56, 0, tzinfo=UTC)
    until = datetime(2024, 10, 10, 14, 1, 12, tzinfo=UTC)
    recs = list(between(parse_records(sample_lines), since=since, until=until))
    assert [r.status for r in recs] == [500, 304]


def test_hourly_counts_groups_by_hour(sample_lines: list[str]) -> None:
    counts = hourly_counts(parse_records(sample_lines))
    assert counts == [("2024-10-10 13:00", 3), ("2024-10-10 14:00", 2)]


def test_csv_reporter_list_mapping_and_scalar() -> None:
    out = CsvReporter().render(
        {"total": 5, "classes": {"2xx": 3}, "top_ip": [("10.0.0.1", 3)]}
    )
    assert out.splitlines() == [
        "key,value",
        "total,5",
        "2xx,3",
        "10.0.0.1,3",
    ]


def test_get_reporter_includes_csv() -> None:
    assert isinstance(get_reporter("csv"), CsvReporter)


def test_cli_hourly_window(log_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "hourly",
            str(log_file),
            "--since",
            "2024-10-10T14:00:00",
            "--until",
            "2024-10-10T14:59:59",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "2024-10-10 14:00" in out
    assert "2024-10-10 13:00" not in out


def test_cli_hourly_invalid_since_exits_2(
    log_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["hourly", str(log_file), "--since", "yesterday"])
    assert excinfo.value.code == 2
    assert "argument --since" in capsys.readouterr().err
