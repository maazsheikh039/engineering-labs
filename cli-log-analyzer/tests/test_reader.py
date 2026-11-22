import types
from itertools import islice
from pathlib import Path

from logtool.reader import ParseStats, filter_records, parse_records, read_lines


def test_read_lines_skips_blank_lines(log_file: Path) -> None:
    lines = list(read_lines([log_file]))
    assert len(lines) == 6
    assert all(lines)


def test_read_lines_chains_plain_and_gzip(log_file: Path, gz_log_file: Path) -> None:
    assert len(list(read_lines([log_file, gz_log_file]))) == 12


def test_pipeline_is_lazy(log_file: Path) -> None:
    records = parse_records(read_lines([log_file]))
    assert isinstance(records, types.GeneratorType)
    assert next(records).ip == "10.0.0.1"


def test_parse_records_counts_malformed(log_file: Path) -> None:
    stats = ParseStats()
    records = list(parse_records(read_lines([log_file]), stats))
    assert len(records) == 5
    assert stats == ParseStats(lines=6, malformed=1)


def test_generator_is_exhausted_after_one_pass(sample_lines: list[str]) -> None:
    records = parse_records(sample_lines)
    assert sum(1 for _ in records) == 5
    assert sum(1 for _ in records) == 0


def test_islice_takes_only_what_it_needs(sample_lines: list[str]) -> None:
    taken = list(islice(parse_records(sample_lines), 2))
    assert [r.status for r in taken] == [200, 401]


def test_filter_by_exact_status(sample_lines: list[str]) -> None:
    records = filter_records(parse_records(sample_lines), status=500)
    assert [r.path for r in records] == ["/api/v1/items"]


def test_filter_by_min_status_and_prefix(sample_lines: list[str]) -> None:
    records = filter_records(
        parse_records(sample_lines), min_status=400, path_prefix="/api"
    )
    assert [r.status for r in records] == [500, 404]


def test_filter_without_criteria_passes_everything(sample_lines: list[str]) -> None:
    assert len(list(filter_records(parse_records(sample_lines)))) == 5
