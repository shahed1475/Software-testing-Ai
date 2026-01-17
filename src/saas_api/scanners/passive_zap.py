from __future__ import annotations

from typing import Any, Dict

from .base import ScanAdapter


class PassiveZapAdapter(ScanAdapter):
    name = "passive_zap"

    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        target = job.get("config", {}).get("target_url", "unknown")
        findings = [
            {
                "severity": "LOW",
                "type": "Missing Security Headers",
                "location": target,
            },
            {
                "severity": "MEDIUM",
                "type": "Verbose Server Banner",
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
