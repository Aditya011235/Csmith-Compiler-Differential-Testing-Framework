"""Csmith program generation."""
import subprocess
from pathlib import Path

def generate_program(csmith: str, seed: int, cwd: Path, timeout: int) -> dict:
    try:
        proc = subprocess.run([csmith, "--seed", str(seed)], cwd=cwd,
                              capture_output=True, text=True, errors="replace",
                              timeout=timeout, check=False)
        return {"status": "ok" if proc.returncode == 0 else "error",
                "returncode": proc.returncode, "stdout": proc.stdout,
                "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        def decode(value):
            return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")
        return {"status": "timeout", "returncode": None,
                "stdout": decode(exc.stdout), "stderr": decode(exc.stderr), "timed_out": True}
    except OSError as exc:
        return {"status": "error", "returncode": None, "stdout": "",
                "stderr": str(exc), "timed_out": False}
