from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

QUEUE_DIR = Path("runtime/queue")
RESULTS_DIR = Path("runtime/results")
ARTIFACTS_DIR = Path("runtime/artifacts")


def ensure_dirs() -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def enqueue_run(run: Dict[str, Any]) -> Path:
    ensure_dirs()
    job_path = QUEUE_DIR / f"{run['id']}.json"
    job_payload = {
        "run_id": run["id"],
        "project_id": run["project_id"],
        "target_id": run["target_id"],
        "suite_id": run["suite_id"],
        "config": run.get("config", {}),
        "safe_mode": run.get("safe_mode", True),
        "rate_limit": run.get("rate_limit", 60),
    }
    job_path.write_text(json.dumps(job_payload, indent=2), encoding="utf-8")
    return job_path


def write_results(run_id: str, results: Dict[str, Any]) -> Path:
    ensure_dirs()
    result_path = RESULTS_DIR / f"{run_id}.json"
    result_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return result_path


def read_results(run_id: str) -> Dict[str, Any] | None:
    result_path = RESULTS_DIR / f"{run_id}.json"
    if not result_path.exists():
        return None
    return json.loads(result_path.read_text(encoding="utf-8"))
