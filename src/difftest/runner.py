"""Per-seed orchestration."""
import json
import shutil
import tempfile
import time
from pathlib import Path
from .bundles import write_bundle
from .classifier import GEN_FAIL, PASS, TIMEOUT, classify
from .compiler import test_configuration
from .config import CompilerConfig, RunConfig
from .generator import generate_program
from .reducer import reduce_case

def test_seed(seed: int, config: RunConfig, compilers: list[CompilerConfig], metadata: dict) -> dict:
    started = time.monotonic()
    work = Path(tempfile.mkdtemp(prefix=f"difftest_{seed}_"))
    try:
        generated = generate_program(config.csmith, seed, work, config.gen_timeout)
        if generated["status"] != "ok":
            return {"seed": seed, "status": GEN_FAIL,
                    "detail": generated["stderr"][:500] or generated["status"],
                    "seconds": round(time.monotonic() - started, 3)}
        source_text = generated["stdout"]
        source = work / "test.c"
        source.write_text(source_text, encoding="utf-8")
        outcomes = {}
        for compiler in compilers:
            outcomes[compiler.label] = test_configuration(
                compiler, source, work / f"{compiler.label}.bin", config.include_dir,
                config.compile_timeout, config.run_timeout)
        status, detail = classify(outcomes)
        result = {"seed": seed, "status": status, "detail": detail,
                  "seconds": round(time.monotonic() - started, 3)}
        if status != PASS and (status != TIMEOUT or config.keep_timeouts):
            bundle = Path(config.outdir) / "failures" / f"seed_{seed}"
            bundle_metadata = {**metadata, "seed": seed, "include_dir": config.include_dir,
                "configurations": [{"label": c.label, "name": c.name,
                    "executable": c.executable, "optimization": c.optimization} for c in compilers]}
            write_bundle(bundle, seed, source_text, outcomes, status, detail, bundle_metadata)
            result["bundle"] = str(bundle)
            if config.reduce_failures and status == "mismatch":
                reducer_configs = [{"executable": c.executable, "optimization": c.optimization}
                                   for c in compilers]
                reduced = reduce_case(bundle / "test.c", bundle / "reduced.c", reducer_configs,
                                      config.include_dir, jobs=config.reducer_jobs)
                (bundle / "reduction.json").write_text(json.dumps(reduced, indent=2), encoding="utf-8")
                result["reduction_status"] = reduced["status"]
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)
