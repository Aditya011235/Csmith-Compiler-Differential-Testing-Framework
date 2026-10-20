"""Optional C-Reduce integration. It only preserves output/exit-code mismatches."""
import json
import shutil
import subprocess
from pathlib import Path

def create_interestingness_test(path: Path, configurations: list[dict],
                                include_dir: str, timeout: int = 15) -> Path:
    payload = json.dumps({"configurations": configurations, "include_dir": include_dir,
                          "timeout": timeout}, separators=(",", ":"))
    script = r"""#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
cfg = json.loads(__CONFIG_JSON__)
source = Path(sys.argv[1]).resolve()
results = []
with tempfile.TemporaryDirectory(prefix="difftest_reduce_") as tmp:
    for i, item in enumerate(cfg["configurations"]):
        exe = str(Path(tmp) / f"program_{i}")
        cmd = [item["executable"], "-" + item["optimization"], "-w",
               "-I" + cfg["include_dir"], str(source), "-o", exe]
        try:
            comp = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=cfg["timeout"], check=False)
            if comp.returncode != 0:
                sys.exit(1)
            run = subprocess.run([exe], capture_output=True, text=True,
                                 timeout=cfg["timeout"], check=False)
        except (OSError, subprocess.TimeoutExpired):
            sys.exit(1)
        results.append((run.returncode, run.stdout))
sys.exit(0 if len(set(results)) > 1 else 1)
"""
    path.write_text(script.replace("__CONFIG_JSON__", repr(payload)), encoding="utf-8")
    path.chmod(0o755)
    return path

def reduce_case(source_path: Path, output_path: Path, configurations: list[dict],
                include_dir: str, jobs: int = 2, timeout: int = 15) -> dict:
    creduce = shutil.which("creduce")
    if not creduce:
        return {"status": "unavailable", "detail": "creduce executable not found"}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, output_path)
    predicate = output_path.parent / "interestingness_test.py"
    create_interestingness_test(predicate, configurations, include_dir, timeout)
    try:
        proc = subprocess.run([creduce, "--n", str(jobs), str(predicate), str(output_path)],
                              capture_output=True, text=True, timeout=3600, check=False)
        return {"status": "ok" if proc.returncode == 0 else "error",
                "returncode": proc.returncode, "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:], "output": str(output_path)}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "detail": "C-Reduce exceeded 3600 seconds"}
