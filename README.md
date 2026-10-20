# Csmith Compiler Differential Testing

A Python harness that generates C programs with [Csmith](https://github.com/csmith-project/csmith), compiles each program with multiple compiler/optimization configurations, executes the resulting binaries, and compares observable results.

The goal is to identify **candidate compiler correctness issues** and save enough metadata to reproduce and investigate them. A mismatch is not automatically a confirmed compiler bug.

## Features

- Csmith-generated test programs, keyed by reproducible seed.
- Configurable compiler matrix and optimization levels.
- Concurrent seed execution.
- Separate classification for output/exit-code mismatches, compilation differences, compilation failures, timeouts, and runtime failures.
- JSON and CSV reports with toolchain metadata and per-seed durations.
- Failure bundles containing generated source, results, metadata, and a reproduction script.
- Optional C-Reduce integration for observed output mismatches.
- Unit tests and GitHub Actions CI; unit tests do not require Csmith or a real compiler installation.

## Requirements

Linux is recommended (Ubuntu/WSL2 is fine), Python 3.10+, Csmith, GCC, Clang, and the Csmith development header `csmith.h`. C-Reduce is optional.

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv gcc clang csmith libcsmith-dev git
```

Package names can vary by Ubuntu release. If `csmith.h` is not found automatically, locate it and pass its containing directory using `--include`.

## Install

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Test

```bash
python -m unittest discover -s tests -v
```

These tests use Python subprocesses and fixtures; they do not require Csmith.

## Run a small campaign

```bash
python difftest.py --first 0 --last 11 --jobs 4
```

This tests 12 seeds. With GCC and Clang at `O0`, `O2`, and `O3`, each seed is compiled and run under six configurations.

Run a larger campaign:

```bash
python difftest.py --first 0 --last 999 --jobs 4 --outdir out-1000
```

Use `python difftest.py --help` for options.

### Useful options

```text
--compilers gcc,clang
--opts O0,O2,O3
--jobs 4
--first 0 --last 99
--include /path/to/directory/containing/csmith.h
--outdir out
--run-timeout 10
--compile-timeout 120
--gen-timeout 60
--keep-timeouts
--reduce-failures
```

`--reduce-failures` requires `creduce` and attempts reduction only for output mismatches. C-Reduce can take a long time; inspect and verify any reduced case yourself.

## Output

```text
out/
├── report.json
├── report.csv
└── failures/
    └── seed_42/
        ├── test.c
        ├── result.json
        ├── metadata.json
        ├── repro.sh
        └── reduced.c  # only if reduction was attempted
```

Actual files depend on the run. Reports include a completion flag so interrupted campaigns can be distinguished from completed campaigns.

## Verdicts

- `pass`: comparable executions agree on exit code and stdout.
- `mismatch`: completed executions disagree on exit code or stdout; investigate as a candidate correctness issue.
- `compile_diff`: some configurations compile while others do not, without an already-observed output mismatch.
- `compile_fail`: no configuration compiled.
- `timeout`: an execution timed out without an already-observed mismatch.
- `runtime_fail`: a compiled program crashed or returned non-zero without an already-observed mismatch.
- `gen_fail`: Csmith failed or timed out.
- `inconclusive`: insufficient comparable results.

The harness compares exact stdout and exit code. It does not prove a mismatch is caused by a compiler defect. Platform differences, compiler flags, environment, and test assumptions must be investigated.

## Reproduce a bundle

From a failure directory:

```bash
./repro.sh
```

The script expects the recorded compiler executables and Csmith headers to remain available. Review scripts before running bundles from untrusted sources.

## Benchmarking

See [`benchmarks/README.md`](benchmarks/README.md). Publish only measurements you actually collected.

## Limitations

- No automatic root-cause diagnosis.
- Compilation differences are candidate issues, not proof of a compiler bug.
- C-Reduce is optional; its predicate preserves output/exit-code disagreement only when every configuration compiles and runs.
- No GPU/CUDA testing is included.
- Compiler diagnostics are captured but not compared as program output.

## Resume guidance

Only claim features you personally ran and verified. A defensible project description after testing this repository:

> Built a Python-based C compiler differential-testing harness using Csmith; automated parallel compilation and execution across GCC/Clang optimization levels, classified mismatches and failure modes, and generated reproducible JSON/CSV reports and failure bundles.

Add claims about scale, C-Reduce, or real compiler bugs only after measuring or confirming them.
