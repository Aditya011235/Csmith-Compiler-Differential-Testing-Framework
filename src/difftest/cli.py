"""Command-line interface."""
import argparse
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from . import __version__
from .classifier import BUG_STATUSES, PASS
from .config import RunConfig, find_csmith_include, resolve_compilers, validate_run_config
from .reporter import write_reports
from .runner import test_seed

def first_line(command: list[str]) -> str:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
        text = proc.stdout or proc.stderr
        return text.splitlines()[0] if text.splitlines() else "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Differentially test C compilers using Csmith-generated programs.")
    parser.add_argument("--first", type=int, default=0, help="first seed, inclusive")
    parser.add_argument("--last", type=int, default=99, help="last seed, inclusive")
    parser.add_argument("--compilers", default="gcc,clang", help="comma-separated compiler commands")
    parser.add_argument("--opts", default="O0,O2,O3", help="comma-separated optimization levels")
    parser.add_argument("--jobs", type=int, default=2, help="concurrent seeds")
    parser.add_argument("--csmith", default="csmith", help="Csmith executable")
    parser.add_argument("--include", default=None, help="directory containing csmith.h")
    parser.add_argument("--outdir", default="out", help="report/failure output directory")
    parser.add_argument("--gen-timeout", type=int, default=60)
    parser.add_argument("--compile-timeout", type=int, default=120)
    parser.add_argument("--run-timeout", type=int, default=10)
    parser.add_argument("--keep-timeouts", action="store_true")
    parser.add_argument("--reduce-failures", action="store_true",
                        help="attempt C-Reduce on output mismatches (requires creduce)")
    parser.add_argument("--reducer-jobs", type=int, default=2)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    csmith = shutil.which(args.csmith)
    if not csmith:
        parser.error(f"Csmith executable not found: {args.csmith!r}")
    include = find_csmith_include(args.include, csmith)
    if not include:
        parser.error("could not find csmith.h; pass --include /path/to/directory-containing-csmith.h")
    names = [x.strip() for x in args.compilers.split(",") if x.strip()]
    opts = [x.strip() for x in args.opts.split(",") if x.strip()]
    allowed = {"O0", "O1", "O2", "O3", "Os", "Oz"}
    if not opts or any(x not in allowed for x in opts):
        parser.error(f"--opts values must be from {sorted(allowed)}")
    compilers = resolve_compilers(names, opts)
    missing = sorted(set(names) - {c.name for c in compilers})
    if missing:
        print("warning: compiler(s) not found and skipped: " + ", ".join(missing), file=sys.stderr)
    if len(compilers) < 2:
        parser.error("need at least two available compiler/optimization configurations")
    config = RunConfig(args.first, args.last, args.jobs, csmith, include, args.outdir,
        args.compile_timeout, args.run_timeout, args.gen_timeout, args.keep_timeouts,
        args.reduce_failures, args.reducer_jobs)
    try:
        validate_run_config(config)
    except ValueError as exc:
        parser.error(str(exc))
    outdir = Path(config.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "tool": "csmith-compiler-difftest", "tool_version": __version__,
        "csmith_path": csmith, "csmith_version": first_line([csmith, "--version"]),
        "include_dir": include,
        "compiler_versions": {c.name: {"path": c.executable,
            "version": first_line([c.executable, "--version"])} for c in compilers},
        "configurations": [{"label": c.label, "name": c.name, "executable": c.executable,
                            "optimization": c.optimization} for c in compilers],
        "seed_range": {"first": config.first, "last": config.last}, "jobs": config.jobs,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    print(f"Csmith: {metadata['csmith_version']}")
    print("Configurations: " + ", ".join(c.label for c in compilers))
    results, complete = [], True
    futures = {}
    with ThreadPoolExecutor(max_workers=config.jobs) as executor:
        for seed in range(config.first, config.last + 1):
            futures[executor.submit(test_seed, seed, config, compilers, metadata)] = seed
        try:
            for done, future in enumerate(as_completed(futures), start=1):
                seed = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"seed": seed, "status": "internal_error",
                              "detail": f"{type(exc).__name__}: {exc}", "seconds": 0}
                results.append(result)
                if result["status"] == PASS:
                    print(f"[{done}/{len(futures)}] seed {seed}: pass")
                else:
                    print(f"[{done}/{len(futures)}] seed {seed}: {result['status']} - {result['detail']}")
        except KeyboardInterrupt:
            complete = False
            for future in futures:
                future.cancel()
            print("\\nInterrupted: writing partial report.", file=sys.stderr)
    report = write_reports(outdir, metadata, results, complete)
    print(f"\\nSummary: {len(results)} seeds completed")
    for status, count in sorted(report["summary"].items()):
        print(f"  {status:16s} {count}")
    print(f"Reports: {report['json']} and {report['csv']}")
    if any(result["status"] in BUG_STATUSES for result in results):
        return 1
    return 0 if complete else 130
