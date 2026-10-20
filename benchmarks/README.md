# Benchmarking

Do not publish invented performance numbers. Record OS, machine/CPU, Python,
Csmith and compiler versions, seed range, compiler matrix, wall-clock duration,
and verdict counts.

Example:

```bash
python difftest.py --first 0 --last 999 --jobs 4 --outdir out-1000
```

Compare throughput at `--jobs 1`, `--jobs 2`, and `--jobs 4` using the same
seed range and configuration. Repeat runs and report measured results.
Timeouts are separate from mismatches and are not evidence of a compiler bug.
