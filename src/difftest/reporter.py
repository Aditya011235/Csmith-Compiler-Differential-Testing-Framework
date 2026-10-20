"""JSON and CSV report writing."""
import csv
import json
from pathlib import Path

def write_reports(outdir: Path, metadata: dict, results: list[dict], complete: bool) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    ordered = sorted(results, key=lambda row: row["seed"])
    report = {"metadata": metadata, "complete": complete,
              "summary": dict(sorted(counts.items())), "results": ordered}
    json_path = outdir / "report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    csv_path = outdir / "report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["seed", "status", "detail", "seconds"],
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered)
    return {"summary": counts, "json": str(json_path), "csv": str(csv_path)}
