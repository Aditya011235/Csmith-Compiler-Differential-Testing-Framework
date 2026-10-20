"""Configuration models and validation."""
from dataclasses import dataclass
from pathlib import Path
import shutil

@dataclass(frozen=True)
class CompilerConfig:
    name: str
    executable: str
    optimization: str

    @property
    def label(self) -> str:
        return f"{self.name}-{self.optimization}"

@dataclass(frozen=True)
class RunConfig:
    first: int
    last: int
    jobs: int
    csmith: str
    include_dir: str
    outdir: str
    compile_timeout: int = 120
    run_timeout: int = 10
    gen_timeout: int = 60
    keep_timeouts: bool = False
    reduce_failures: bool = False
    reducer_jobs: int = 2

def find_csmith_include(user_value: str | None, csmith_executable: str) -> str | None:
    candidates = []
    if user_value:
        candidates.append(Path(user_value).expanduser())
    else:
        candidates.extend([Path("/usr/include/csmith"), Path("/usr/local/include/csmith"),
                          Path.home() / "csmith" / "include"])
        resolved = shutil.which(csmith_executable)
        if resolved:
            candidates.append(Path(resolved).resolve().parent.parent / "include")
        for base in (Path("/usr/local/include"), Path("/usr/include")):
            if base.exists():
                candidates.extend(p for p in base.glob("csmith*") if p.is_dir())
    for candidate in candidates:
        if (candidate / "csmith.h").is_file():
            return str(candidate.resolve())
    return None

def resolve_compilers(names: list[str], optimizations: list[str]) -> list[CompilerConfig]:
    resolved = []
    for name in names:
        executable = shutil.which(name)
        if executable:
            resolved.extend(CompilerConfig(name, executable, opt) for opt in optimizations)
    return resolved

def validate_run_config(config: RunConfig) -> None:
    if config.first < 0:
        raise ValueError("--first must be >= 0")
    if config.last < config.first:
        raise ValueError("--last must be >= --first")
    if config.jobs < 1:
        raise ValueError("--jobs must be >= 1")
    for label, value in (("compile timeout", config.compile_timeout),
                         ("run timeout", config.run_timeout),
                         ("generation timeout", config.gen_timeout)):
        if value < 1:
            raise ValueError(f"{label} must be >= 1")
    if config.reducer_jobs < 1:
        raise ValueError("--reducer-jobs must be >= 1")
