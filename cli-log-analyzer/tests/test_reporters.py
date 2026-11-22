import json

import pytest

from logtool.reporters import JsonReporter, Reporter, TextReporter, get_reporter

DATA = {
    "records": 5,
    "error_rate": 0.6,
    "status_classes": {"2xx": 1, "5xx": 4},
    "top_ip": [("10.0.0.1", 3)],
}


def test_text_reporter_layout() -> None:
    assert TextReporter().render(DATA).splitlines() == [
        "records".ljust(18) + " 5",
        "error_rate".ljust(18) + " 60.00%",
        "status_classes:",
        "  " + "2xx".ljust(16) + " 1",
        "  " + "5xx".ljust(16) + " 4",
        "top_ip:",
        "  " + "10.0.0.1".ljust(16) + " 3",
    ]


def test_json_reporter_round_trips() -> None:
    parsed = json.loads(JsonReporter().render(DATA))
    assert parsed["status_classes"]["5xx"] == 4
    assert parsed["top_ip"] == [["10.0.0.1", 3]]


@pytest.mark.parametrize("name", ["text", "json"])
def test_get_reporter_returns_subclass(name: str) -> None:
    reporter = get_reporter(name)
    assert isinstance(reporter, Reporter)
    assert reporter.name == name


def test_get_reporter_unknown() -> None:
    with pytest.raises(ValueError, match="unknown format"):
        get_reporter("xml")


def test_reporter_is_abstract() -> None:
    with pytest.raises(TypeError):
        Reporter()  # type: ignore[abstract]
