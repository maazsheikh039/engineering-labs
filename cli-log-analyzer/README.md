# logtool — Streaming CLI Access-Log Analysis Package

A memory-safe, typed Python 3.12 CLI package for streaming, filtering, and aggregating plain-text and gzip-compressed Apache/Nginx combined-format web server access logs.

## Objectives
- Stream arbitrarily large `.log` and `.log.gz` files with constant $O(1)$ record memory via lazy generator pipelines.
- Model log records as immutable, slot-backed domain objects with structured `ParseError` exception handling.
- Provide CI/cron-ready CLI sub-commands (`summary`, `top`, `errors`, `hourly`) with `text`, `json`, and `csv` formatters and deterministic exit codes (`0`, `1`, `2`, `3`).
- Enforce production code quality using `ruff`, `black`, `mypy --strict`, `pytest` with an 85%+ branch coverage gate, and `cProfile`/`timeit` optimization.

## Tools & Technologies Used
- **Language & Packaging:** Python 3.12, `pyproject.toml` (`src/` layout), `setuptools`, `wheel`
- **Core Standard Library:** `argparse`, `dataclasses`, `contextlib`, `functools`, `itertools`, `gzip`, `csv`, `json`, `cProfile`, `pstats`, `timeit`, `tracemalloc`
- **Testing & Quality Gate:** `pytest`, `pytest-cov`, `ruff`, `black`, `mypy` (`--strict`), `ipython`

## Key Skills Demonstrated
- **Memory-Efficient Data Pipelines:** Built composable lazy generators (`read_lines`, `parse_records`, `filter_records`, `between`) with `itertools.islice` and `itertools.groupby`, cutting peak memory from ~8.4 MiB to ~0.05 MiB on 20k-line logs.
- **Object-Oriented & Functional Design:** Implemented `@dataclass(frozen=True, slots=True)`, custom exception chaining (`raise ... from exc`), generator/class context managers (`open_log`, `Timer`), signature-preserving decorators (`@timed`, `@deprecated` with `ParamSpec`), and an ABC + decorator registry (`Reporter`, `@register`).
- **Performance Profiling & Optimization:** Identified `datetime.strptime` as the primary bottleneck via `cProfile` and replaced it with a fixed-width string-slicing parser and `@lru_cache` timezone lookup protected by characterization tests, achieving >4x faster timestamp parsing.
- **CI/CD Readiness:** Built a fully tested CLI (`tmp_path`, `capsys`, `caplog`, `parametrize`) with documented exit codes (`0` OK, `1` I/O error, `2` usage error, `3` error-rate threshold breach).

## Troubleshooting Log
- **Static Typing (`mypy --strict` `[no-any-return]`):** `argparse.Namespace` attributes default to `Any`, causing `return args.func(args)` in `cli.py` to fail strict return type checking. Resolved by binding `handler: Handler = args.func` before invocation.
- **Timestamp Parsing Bottleneck (`cProfile`):** Profiling 200,000 log lines revealed `datetime.strptime` consumed >60% of cumulative runtime due to locale/regex overhead. Replaced with fixed-offset slicing and cached `timezone` objects after pinning behavior with characterization tests.
- **Generator Cleanup on Early Exit:** Closing a downstream generator (`records.close()`) raises `GeneratorExit` at `yield`; wrapping file handles inside `with open_log(...)` inside `read_lines` guarantees deterministic file closure even on partial reads (`islice`).

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Generate sample logs and run CLI commands
python scripts/gen_logs.py --out data/access.log
logtool summary data/access.log
logtool top data/access.log --by path -n 3
logtool errors data/access.log --min-status 500 -f json
logtool hourly data/access.log --since 2024-10-10T02:00:00 --until 2024-10-10T03:59:59 -f csv
