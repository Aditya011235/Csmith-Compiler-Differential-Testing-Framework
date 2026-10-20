"""Failure bundles with source, outcome details, metadata and reproduction commands."""
import json
import os
import shlex
from pathlib import Path

def write_bundle(destination: Path, seed: int, source_text: str, outcomes: dict,
                 status: str, detail: str, metadata: dict) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "test.c").write_text(source_text, encoding="utf-8")
    (destination / "result.json").write_text(json.dumps(
        {"seed": seed, "status": status, "detail": detail, "outcomes": outcomes},
        indent=2), encoding="utf-8")
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    lines = ["#!/bin/sh", "set -eu", f"# Reproduce Csmith seed {seed}.",
             "mkdir -p repro-bin"]
    include_dir = metadata.get("include_dir", "/usr/include/csmith")
    for item in metadata.get("configurations", []):
        command = [item["executable"], f"-{item['optimization']}", "-w",
                   f"-I{include_dir}", "test.c", "-o", f"repro-bin/{item['label']}"]
        lines.append(" ".join(shlex.quote(arg) for arg in command))
        lines.append(shlex.quote(f"./repro-bin/{item['label']}"))
    (destination / "repro.sh").write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(destination / "repro.sh", 0o755)
    except OSError:
        pass
    return destination
