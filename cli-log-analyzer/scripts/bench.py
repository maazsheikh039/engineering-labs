"""Time the full streaming pipeline with the Timer context manager."""

import logging
import sys

from logtool.analyzer import LogAnalyzer
from logtool.reader import parse_records, read_lines
from logtool.utils import Timer

logging.basicConfig(level=logging.INFO, format="%(message)s")
paths = sys.argv[1:] or ["data/access.log"]
with Timer(f"pipeline over {len(paths)} file(s)") as timer:
    analyzer = LogAnalyzer(parse_records(read_lines(paths)))
print(analyzer)
print(f"{analyzer.total / timer.elapsed:,.0f} records/s")
