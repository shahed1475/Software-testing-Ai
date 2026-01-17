from __future__ import annotations

from typing import Any, Dict

from .base import ScanAdapter


class ZapBaselineAdapter(ScanAdapter):
    name = "zap_baseline"

    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        target = job.get("config", {}).get("target_url", "unknown")
        findings = [
            {
                "severity": "LOW",
                "type": "X-Frame-Options missing",
                "location": target,
            },
            {
                "severity": "LOW",
                "type": "X-Content-Type-Options missing",
                "location": target,
            },
        ]
        return {
            "scanner": self.name,
            "summary": {
                "total_findings": len(findings),
            },
            "findings": findings,
        }
