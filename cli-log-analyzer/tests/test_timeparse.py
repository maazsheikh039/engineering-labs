from datetime import datetime

import pytest

from logtool.timeparse import TS_FORMAT, parse_timestamp


@pytest.mark.parametrize(
    "value",
    [
        "10/Oct/2024:13:55:36 +0000",
        "01/Jan/2023:00:00:00 -0530",
        "29/Feb/2024:23:59:59 +1400",
    ],
)
def test_matches_strptime(value: str) -> None:
    expected = datetime.strptime(value, TS_FORMAT)
    assert parse_timestamp(value) == expected
    assert parse_timestamp(value).utcoffset() == expected.utcoffset()


@pytest.mark.parametrize(
    "value",
    [
        "10/Oct/2024 13:55:36 +0000",
        "10/Xyz/2024:13:55:36 +0000",
        "garbage",
    ],
)
def test_rejects_bad_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_timestamp(value)
