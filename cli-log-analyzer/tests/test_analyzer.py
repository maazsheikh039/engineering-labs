import pytest

from logtool.analyzer import LogAnalyzer, count_errors
from logtool.reader import parse_records


@pytest.fixture
def analyzer(sample_lines: list[str]) -> LogAnalyzer:
    return LogAnalyzer(parse_records(sample_lines))


def test_totals(analyzer: LogAnalyzer) -> None:
    assert len(analyzer) == 5
    assert analyzer.total_bytes == 3030
    assert analyzer.error_count == 3
    assert analyzer.error_rate == pytest.approx(0.6)


def test_status_classes_sorted(analyzer: LogAnalyzer) -> None:
    assert analyzer.status_classes() == {"2xx": 1, "3xx": 1, "4xx": 2, "5xx": 1}
    assert list(analyzer.status_classes()) == ["2xx", "3xx", "4xx", "5xx"]


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("ip", [("10.0.0.1", 3), ("10.0.0.2", 1)]),
        ("path", [("/index.html", 2), ("/api/v1/items", 2)]),
        ("status", [("200", 1), ("401", 1)]),
    ],
)
def test_top(
    analyzer: LogAnalyzer, field: str, expected: list[tuple[str, int]]
) -> None:
    assert analyzer.top(field, 2) == expected


def test_unknown_field_raises(analyzer: LogAnalyzer) -> None:
    with pytest.raises(ValueError, match="unknown field"):
        analyzer.top("user")


def test_summary_and_repr(analyzer: LogAnalyzer) -> None:
    summary = analyzer.summary()
    assert summary["records"] == 5
    assert summary["unique_ips"] == 3
    assert summary["first_seen"] == "2024-10-10T13:55:36+00:00"
    assert summary["last_seen"] == "2024-10-10T14:05:00+00:00"
    assert repr(analyzer) == "LogAnalyzer(records=5, errors=3, unique_ips=3)"


def test_empty_analyzer() -> None:
    empty = LogAnalyzer()
    assert empty.error_rate == 0.0
    assert empty.summary()["first_seen"] is None


def test_feed_is_incremental_and_chainable(sample_lines: list[str]) -> None:
    analyzer = LogAnalyzer()
    analyzer.feed(parse_records(sample_lines[:2])).feed(parse_records(sample_lines[2:]))
    assert len(analyzer) == 5


def test_count_errors_is_deprecated(sample_lines: list[str]) -> None:
    with pytest.warns(DeprecationWarning, match="LogAnalyzer"):
        assert count_errors(parse_records(sample_lines)) == 3
