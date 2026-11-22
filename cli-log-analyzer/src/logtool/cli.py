"""Command-line interface: `logtool [-v] COMMAND FILE [FILE...]`."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from logtool import __version__
from logtool.analyzer import LogAnalyzer, hourly_counts
from logtool.reader import (
    ParseStats,
    between,
    filter_records,
    parse_records,
    read_lines,
)
from logtool.reporters import REPORTERS, get_reporter
from logtool.utils import timed

Handler = Callable[[argparse.Namespace], int]

EXIT_OK = 0
EXIT_IO_ERROR = 1
EXIT_THRESHOLD = 3


@timed
def analyze(
    paths: Sequence[str], min_status: int | None = None
) -> tuple[LogAnalyzer, ParseStats]:
    """Run the full streaming pipeline over *paths*."""
    stats = ParseStats()
    records = parse_records(read_lines(paths), stats)
    if min_status is not None:
        records = filter_records(records, min_status=min_status)
    return LogAnalyzer(records), stats


def emit(args: argparse.Namespace, data: dict[str, object]) -> None:
    print(get_reporter(args.format).render(data))


def cmd_summary(args: argparse.Namespace) -> int:
    analyzer, stats = analyze(args.files)
    data: dict[str, object] = {
        "files": len(args.files),
        "malformed": stats.malformed,
        **analyzer.summary(),
    }
    emit(args, data)
    threshold = args.fail_on_error_rate
    if threshold is not None and analyzer.error_rate > threshold:
        print(
            f"logtool: error rate {analyzer.error_rate:.2%} exceeds "
            f"threshold {threshold:.2%}",
            file=sys.stderr,
        )
        return EXIT_THRESHOLD
    return EXIT_OK


def cmd_top(args: argparse.Namespace) -> int:
    analyzer, _ = analyze(args.files)
    emit(args, {f"top_{args.by}": analyzer.top(args.by, args.n)})
    return EXIT_OK


def cmd_errors(args: argparse.Namespace) -> int:
    analyzer, _ = analyze(args.files, min_status=args.min_status)
    data: dict[str, object] = {
        "min_status": args.min_status,
        "error_records": len(analyzer),
        "by_status": {str(s): n for s, n in sorted(analyzer.status_counts.items())},
        "top_error_paths": analyzer.top("path", args.n),
    }
    emit(args, data)
    return EXIT_OK


def cmd_hourly(args: argparse.Namespace) -> int:
    records = parse_records(read_lines(args.files))
    windowed = between(records, since=args.since, until=args.until)
    emit(args, {"hourly": hourly_counts(windowed)})
    return EXIT_OK


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be >= 1, got {value}")
    return number


def ratio(value: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError(f"must be between 0 and 1, got {value}")
    return number


def iso_datetime(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO datetime: {value!r}") from exc
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logtool", description="Analyse web server access logs (plain or .gz)."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="-v INFO, -vv DEBUG"
    )

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("files", nargs="+", metavar="FILE", help="log file(s)")
    common.add_argument(
        "-f", "--format", choices=sorted(REPORTERS), default="text"
    )

    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    p_sum = sub.add_parser("summary", parents=[common], help="overall statistics")
    p_sum.add_argument(
        "--fail-on-error-rate",
        type=ratio,
        metavar="RATIO",
        help="exit with code 3 if the error rate is above RATIO (0-1)",
    )
    p_sum.set_defaults(func=cmd_summary)

    p_top = sub.add_parser("top", parents=[common], help="most frequent values")
    p_top.add_argument("--by", choices=["ip", "path", "status"], default="ip")
    p_top.add_argument("-n", type=positive_int, default=5)
    p_top.set_defaults(func=cmd_top)

    p_err = sub.add_parser("errors", parents=[common], help="4xx/5xx breakdown")
    p_err.add_argument("--min-status", type=int, default=400)
    p_err.add_argument("-n", type=positive_int, default=5)
    p_err.set_defaults(func=cmd_errors)

    p_hr = sub.add_parser("hourly", parents=[common], help="hourly request counts")
    p_hr.add_argument("--since", type=iso_datetime, default=None)
    p_hr.add_argument("--until", type=iso_datetime, default=None)
    p_hr.set_defaults(func=cmd_hourly)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    level = {0: logging.WARNING, 1: logging.INFO}.get(args.verbose, logging.DEBUG)
    logging.basicConfig(
        level=level, format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr
    )
    try:
        handler: Handler = args.func
        return handler(args)
    except FileNotFoundError as exc:
        print(f"logtool: error: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    except KeyboardInterrupt:
        print("logtool: interrupted", file=sys.stderr)
        return 130
