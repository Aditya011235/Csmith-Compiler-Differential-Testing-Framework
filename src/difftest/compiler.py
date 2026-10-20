"""Compiler execution and program execution helpers."""
import subprocess
import time
from pathlib import Path
from .config import CompilerConfig

def run_command(command: list[str], timeout: int, cwd: Path | None = None) -> dict:
    started = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                              errors="replace", timeout=timeout, check=False)
        return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
                "timed_out": False, "seconds": round(time.monotonic() - started, 4),
                "launch_error": None}
    except subprocess.TimeoutExpired as exc:
        def decode(value):
            return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")
        return {"returncode": None, "stdout": decode(exc.stdout), "stderr": decode(exc.stderr),
                "timed_out": True, "seconds": round(time.monotonic() - started, 4),
                "launch_error": None}
    except OSError as exc:
        return {"returncode": None, "stdout": "", "stderr": str(exc), "timed_out": False,
                "seconds": round(time.monotonic() - started, 4), "launch_error": str(exc)}

def test_configuration(compiler: CompilerConfig, source: Path, executable_path: Path,
                       include_dir: str, compile_timeout: int, run_timeout: int) -> dict:
    command = [compiler.executable, f"-{compiler.optimization}", "-w",
               f"-I{include_dir}", str(source), "-o", str(executable_path)]
    comp = run_command(command, compile_timeout, cwd=source.parent)
    if comp["launch_error"]:
        compile_status = "compiler_missing"
    elif comp["timed_out"]:
        compile_status = "compile_timeout"
    elif comp["returncode"] == 0:
        compile_status = "ok"
    elif comp["returncode"] is not None and comp["returncode"] < 0:
        compile_status = "compiler_crash"
    else:
        compile_status = "compile_error"
    result = {
        "compiler": compiler.name, "compiler_path": compiler.executable,
        "optimization": compiler.optimization, "label": compiler.label,
        "compile_status": compile_status, "compile_returncode": comp["returncode"],
        "compile_stdout": comp["stdout"], "compile_stderr": comp["stderr"],
        "compile_seconds": comp["seconds"], "run_status": "not_run",
        "returncode": None, "stdout": "", "stderr": "", "run_seconds": 0.0,
        "compile_command": command,
    }
    if compile_status != "ok":
        return result
    run = run_command([str(executable_path)], run_timeout, cwd=source.parent)
    if run["launch_error"]:
        run_status = "launch_error"
    elif run["timed_out"]:
        run_status = "timeout"
    elif run["returncode"] == 0:
        run_status = "ok"
    elif run["returncode"] is not None and run["returncode"] < 0:
        run_status = "runtime_crash"
    else:
        run_status = "nonzero_exit"
    result.update({"run_status": run_status, "returncode": run["returncode"],
                   "stdout": run["stdout"], "stderr": run["stderr"],
                   "run_seconds": run["seconds"]})
    return result
