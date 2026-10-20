#!/usr/bin/env python3
"""Convenience CLI entry point for the src-layout package."""
from pathlib import Path
import sys

_SRC = Path(__file__).resolve().parent / "src"
__version__ = "0.2.0"
if __name__ == "__main__":
    sys.path.insert(0, str(_SRC))
else:
    # Permit imports such as `from difftest.bundles import ...` in tests even
    # though this compatibility script shares the package name.
    __path__ = [str(_SRC / "difftest")]
from difftest.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
