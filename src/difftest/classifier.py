"""Pure, unit-testable verdict classification."""
from collections import defaultdict

PASS = "pass"
MISMATCH = "mismatch"
COMPILE_DIFF = "compile_diff"
COMPILE_FAIL = "compile_fail"
TIMEOUT = "timeout"
RUNTIME_FAIL = "runtime_fail"
INCONCLUSIVE = "inconclusive"
GEN_FAIL = "gen_fail"
BUG_STATUSES = (MISMATCH, COMPILE_DIFF, RUNTIME_FAIL)

def classify(outcomes: dict) -> tuple[str, str]:
    """Compare completed executions; a timeout must not hide an observed mismatch."""
    if not outcomes:
        return INCONCLUSIVE, "no compiler outcomes"
    compiled = {k: v for k, v in outcomes.items() if v.get("compile_status") == "ok"}
    compile_failures = {k: v for k, v in outcomes.items() if v.get("compile_status") != "ok"}
    completed = {k: v for k, v in compiled.items()
                 if v.get("run_status") not in ("timeout", "launch_error", "not_run")
                 and v.get("returncode") is not None}
    groups = defaultdict(list)
    for label, result in completed.items():
        groups[(result["returncode"], result.get("stdout", ""))].append(label)
    if len(groups) > 1:
        details = []
        for (rc, stdout), labels in sorted(groups.items(), key=lambda x: repr(x[0])):
            details.append(f"{', '.join(sorted(labels))} -> rc={rc}, stdout={stdout[:120]!r}")
        return MISMATCH, " | ".join(details)
    if compile_failures and compiled:
        failed = ", ".join(f"{k} ({v.get('compile_status')})"
                           for k, v in sorted(compile_failures.items()))
        return COMPILE_DIFF, f"compilation outcomes differ; failed: {failed}"
    if not compiled:
        kinds = sorted({v.get("compile_status", "unknown") for v in outcomes.values()})
        return COMPILE_FAIL, "no configuration compiled: " + ", ".join(kinds)
    timed_out = sorted(k for k, v in compiled.items() if v.get("run_status") == "timeout")
    if timed_out:
        return TIMEOUT, "execution timed out: " + ", ".join(timed_out)
    launch_errors = sorted(k for k, v in compiled.items() if v.get("run_status") == "launch_error")
    if launch_errors:
        return INCONCLUSIVE, "could not launch executable: " + ", ".join(launch_errors)
    runtime_failures = sorted(k for k, v in compiled.items()
                              if v.get("run_status") in ("runtime_crash", "nonzero_exit"))
    if runtime_failures:
        return RUNTIME_FAIL, "runtime failure: " + ", ".join(runtime_failures)
    if len(completed) != len(outcomes):
        return INCONCLUSIVE, "not all configurations produced comparable execution results"
    return PASS, ""
