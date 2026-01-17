from __future__ import annotations

import time
from typing import Any, Dict

from .queue import enqueue_run, write_results
from .scanners.mock_pentest import MockPentestAdapter
from .scanners.passive_zap import PassiveZapAdapter
from .scanners.zap_baseline import ZapBaselineAdapter
from .store import store


def _select_adapter(job: Dict[str, Any]):
    suite_id = job.get("suite_id", "")
    scan_type = job.get("config", {}).get("scan_type", "")
    if "zap" in suite_id or scan_type == "zap_baseline":
        return ZapBaselineAdapter()
    if "pentest" in suite_id or "pentest" in scan_type:
        return MockPentestAdapter()
    return PassiveZapAdapter()


def process_run(run_id: str) -> None:
    run = store.runs.get(run_id)
    if not run:
        return
    run["status"] = "running"
    store.add_log(run_id, "Worker started")
    job = {
        "run_id": run["id"],
        "project_id": run["project_id"],
        "target_id": run["target_id"],
        "suite_id": run["suite_id"],
        "config": run.get("config", {}),
        "safe_mode": run.get("safe_mode", True),
        "rate_limit": run.get("rate_limit", 60),
    }
    enqueue_run(run)
    store.add_log(run_id, f"Job enqueued for suite {job['suite_id']}")
    adapter = _select_adapter(job)
    store.add_log(run_id, f"Scanner selected: {adapter.name}")
    time.sleep(1.5)
    scan_output = adapter.run(job)
    store.add_log(run_id, "Scan completed")
    results = {
        "run_id": run_id,
        "scanner": scan_output["scanner"],
        "findings": scan_output["findings"],
        "summary": scan_output["summary"],
    }
    write_results(run_id, results)
    store.add_log(run_id, "Results persisted")
    store.add_findings(run_id, scan_output["findings"])
    run["status"] = "completed"
    store.add_log(run_id, "Run completed")
