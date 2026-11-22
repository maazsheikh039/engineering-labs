"""Output formatters through polymorphism and an abstract base class."""

from __future__ import annotations

import csv
import io
import json
from abc import ABC, abstractmethod
from collections.abc import Mapping

REPORTERS: dict[str, type[Reporter]] = {}


def register(cls: type[Reporter]) -> type[Reporter]:
    """Class decorator that registers a Reporter subclass under cls.name."""
    REPORTERS[cls.name] = cls
    return cls


class Reporter(ABC):
    """Turn a mapping of results into a printable string."""

    name: str = "base"

    @abstractmethod
    def render(self, data: Mapping[str, object]) -> str:
        """Return the formatted report."""


@register
class TextReporter(Reporter):
    name = "text"

    def render(self, data: Mapping[str, object]) -> str:
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, Mapping):
                lines.append(f"{key}:")
                lines.extend(f"  {k!s:<16} {v}" for k, v in value.items())
            elif isinstance(value, list):
                lines.append(f"{key}:")
                lines.extend(f"  {item!s:<16} {count}" for item, count in value)
            elif isinstance(value, float):
                lines.append(f"{key:<18} {value:.2%}")
            else:
                lines.append(f"{key:<18} {value}")
        return "\n".join(lines)


@register
class JsonReporter(Reporter):
    name = "json"

    def render(self, data: Mapping[str, object]) -> str:
        return json.dumps(data, indent=2)


@register
class CsvReporter(Reporter):
    name = "csv"

    def render(self, data: Mapping[str, object]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(["key", "value"])
        for key, value in data.items():
            if isinstance(value, Mapping):
                for k, v in value.items():
                    writer.writerow([k, v])
            elif isinstance(value, list):
                for item, count in value:
                    writer.writerow([item, count])
            else:
                writer.writerow([key, value])
        return buf.getvalue().rstrip("\n")


def get_reporter(name: str) -> Reporter:
    """Factory: look up a reporter class by name and instantiate it."""
    try:
        return REPORTERS[name]()
    except KeyError:
        raise ValueError(
            f"unknown format {name!r}; use one of {sorted(REPORTERS)}"
        ) from None
