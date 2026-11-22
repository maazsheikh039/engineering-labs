#!/usr/bin/env python3
"""Generate deterministic Apache combined-format access logs."""

import argparse
import gzip
from datetime import UTC, datetime, timedelta
from pathlib import Path

IPS = ["203.0.113.10", "198.51.100.23", "192.0.2.77", "203.0.113.99"]
IP_PATTERN = [0, 0, 0, 1, 1, 2, 3]  # index: i % 7
STATUS_PATTERN = [200] * 14 + [301, 304, 404, 404, 500, 503]  # index: i % 20
PATH_PATTERN = ["/api/v1/items"] * 4 + ["/index.html"] * 2 + ["/login", "/admin"]
AGENTS = ["curl/7.81.0", "Mozilla/5.0 (X11; Linux x86_64)", "python-requests/2.31.0"]


def make_line(i: int, start: datetime) -> str:
    if i % 1000 == 999:
        return f"### corrupted entry {i} -- disk hiccup ###"
    ts = (start + timedelta(seconds=i)).strftime("%d/%b/%Y:%H:%M:%S %z")
    ip = IPS[IP_PATTERN[i % 7]]
    status = STATUS_PATTERN[i % 20]
    path = PATH_PATTERN[i % 8]
    method = "POST" if path == "/login" else "GET"
    size = "-" if status == 304 else str(500 + (i % 10) * 100)
    agent = AGENTS[i % 3]
    return f'{ip} - - [{ts}] "{method} {path} HTTP/1.1" {status} {size} "-" "{agent}"'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lines", type=int, default=20000)
    parser.add_argument("--start", default="2024-10-10T00:00:00")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start).replace(tzinfo=UTC)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if args.out.suffix == ".gz" else open
    with opener(args.out, "wt", encoding="utf-8") as fh:
        for i in range(args.lines):
            fh.write(make_line(i, start) + "\n")
    print(f"wrote {args.lines} lines to {args.out}")


if __name__ == "__main__":
    main()
