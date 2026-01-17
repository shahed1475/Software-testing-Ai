from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


@dataclass
class Store:
    org: Dict[str, Any] = field(default_factory=dict)
    users: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    projects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    targets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    runs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    findings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    run_logs: Dict[str, List[str]] = field(default_factory=dict)
    audit_events: List[Dict[str, Any]] = field(default_factory=list)
    run_queue: List[str] = field(default_factory=list)
    usage: Dict[str, Any] = field(default_factory=dict)

    def init_defaults(self) -> None:
        org_id = self.org.get("id") or str(uuid4())
        self.org = {
            "id": org_id,
            "name": "Default Org",
            "plan": "trial",
            "created_at": datetime.now(timezone.utc),
        }
        admin_id = str(uuid4())
        self.users[admin_id] = {
            "id": admin_id,
            "org_id": org_id,
            "email": "admin@example.com",
            "role": "admin",
            "status": "active",
        }
        self.usage = {"runs_used": 0, "max_runs": 50}

    def create_project(self, org_id: str, name: str, description: str | None) -> Dict[str, Any]:
        project_id = str(uuid4())
        project = {
            "id": project_id,
            "org_id": org_id,
            "name": name,
            "description": description,
            "created_at": datetime.now(timezone.utc),
        }
        self.projects[project_id] = project
        return project

    def create_target(self, project_id: str, name: str, target_type: str, scope: Dict[str, Any]) -> Dict[str, Any]:
        target_id = str(uuid4())
        target = {
            "id": target_id,
            "project_id": project_id,
            "name": name,
            "type": target_type,
            "scope": scope,
            "verification_status": "unverified",
            "verification_method": None,
        }
        self.targets[target_id] = target
        return target

    def create_run(self, created_by: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        run_id = str(uuid4())
        run = {
            "id": run_id,
            "project_id": payload["project_id"],
            "target_id": payload["target_id"],
            "suite_id": payload["suite_id"],
            "status": "queued",
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
            "config": payload.get("config", {}),
            "safe_mode": payload.get("safe_mode", True),
            "rate_limit": payload.get("rate_limit", 60),
        }
        self.runs[run_id] = run
        self.run_queue.append(run_id)
        self.run_logs[run_id] = ["Run queued"]
        self.usage["runs_used"] = self.usage.get("runs_used", 0) + 1
        return run

    def add_findings(self, run_id: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        created = []
        for finding in findings:
            finding_id = str(uuid4())
            record = {
                "id": finding_id,
                "run_id": run_id,
                "severity": finding.get("severity", "UNKNOWN"),
                "type": finding.get("type", "Unknown"),
                "location": finding.get("location", ""),
                "status": "open",
            }
            self.findings[finding_id] = record
            created.append(record)
        return created

    def add_log(self, run_id: str, message: str) -> None:
        if run_id not in self.run_logs:
            self.run_logs[run_id] = []
        self.run_logs[run_id].append(message)

    def add_audit_event(self, action: str, metadata: Dict[str, Any]) -> None:
        self.audit_events.append(
            {
                "id": str(uuid4()),
                "action": action,
                "metadata": metadata,
                "created_at": datetime.now(timezone.utc),
            }
        )


store = Store()
store.init_defaults()
