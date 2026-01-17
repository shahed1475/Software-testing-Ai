from datetime import datetime
from typing import List
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    AuthLoginIn,
    AuthLoginOut,
    AuthMfaIn,
    AuthMfaOut,
    OrgOut,
    ProjectIn,
    ProjectOut,
    RunIn,
    RunOut,
    RunQueueOut,
    TargetIn,
    TargetOut,
    TargetVerifyIn,
    UserIn,
    UserOut,
    FindingOut,
    FindingUpdateIn,
    BillingUsageOut,
    BillingPortalOut,
    AuditEventOut,
)
from .queue import read_results
from .store import store
from .worker import process_run

app = FastAPI(title="SaaS Test Platform API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_org_id() -> str:
    return store.org["id"]


@app.post("/api/v1/auth/login", response_model=AuthLoginOut)
def login(payload: AuthLoginIn) -> AuthLoginOut:
    token = f"demo-{payload.email}-{datetime.utcnow().timestamp()}"
    return AuthLoginOut(access_token=token)


@app.post("/api/v1/auth/logout")
def logout() -> dict:
    return {"ok": True}


@app.post("/api/v1/auth/mfa/verify", response_model=AuthMfaOut)
def verify_mfa(payload: AuthMfaIn) -> AuthMfaOut:
    return AuthMfaOut(verified=payload.code == "000000")


@app.get("/api/v1/orgs/me", response_model=OrgOut)
def get_org() -> OrgOut:
    return OrgOut(**store.org)


@app.get("/api/v1/orgs/me/users", response_model=List[UserOut])
def list_users() -> List[UserOut]:
    return [UserOut(**user) for user in store.users.values()]


@app.post("/api/v1/orgs/me/users", response_model=UserOut)
def create_user(payload: UserIn) -> UserOut:
    user_id = f"user-{len(store.users) + 1}"
    user = {
        "id": user_id,
        "org_id": _get_org_id(),
        "email": payload.email,
        "role": payload.role,
        "status": "invited",
    }
    store.users[user_id] = user
    return UserOut(**user)


@app.patch("/api/v1/orgs/me/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserIn) -> UserOut:
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="User not found")
    user = store.users[user_id]
    user["email"] = payload.email
    user["role"] = payload.role
    return UserOut(**user)


@app.get("/api/v1/projects", response_model=List[ProjectOut])
def list_projects() -> List[ProjectOut]:
    return [ProjectOut(**project) for project in store.projects.values()]


@app.post("/api/v1/projects", response_model=ProjectOut)
def create_project(payload: ProjectIn) -> ProjectOut:
    project = store.create_project(_get_org_id(), payload.name, payload.description)
    return ProjectOut(**project)


@app.get("/api/v1/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: str) -> ProjectOut:
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**project)


@app.patch("/api/v1/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, payload: ProjectIn) -> ProjectOut:
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["name"] = payload.name
    project["description"] = payload.description
    return ProjectOut(**project)


@app.get("/api/v1/projects/{project_id}/targets", response_model=List[TargetOut])
def list_targets(project_id: str) -> List[TargetOut]:
    targets = [t for t in store.targets.values() if t["project_id"] == project_id]
    return [TargetOut(**target) for target in targets]


@app.post("/api/v1/projects/{project_id}/targets", response_model=TargetOut)
def create_target(project_id: str, payload: TargetIn) -> TargetOut:
    target = store.create_target(project_id, payload.name, payload.type, payload.scope)
    return TargetOut(**target)


@app.post("/api/v1/targets/{target_id}/verify", response_model=TargetOut)
def verify_target(target_id: str, payload: TargetVerifyIn) -> TargetOut:
    target = store.targets.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    target["verification_status"] = "verified"
    target["verification_method"] = payload.method
    store.add_audit_event("target.verified", {"target_id": target_id, "method": payload.method})
    return TargetOut(**target)


@app.get("/api/v1/targets/{target_id}", response_model=TargetOut)
def get_target(target_id: str) -> TargetOut:
    target = store.targets.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return TargetOut(**target)


@app.patch("/api/v1/targets/{target_id}", response_model=TargetOut)
def update_target(target_id: str, payload: TargetIn) -> TargetOut:
    target = store.targets.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    target["name"] = payload.name
    target["type"] = payload.type
    target["scope"] = payload.scope
    return TargetOut(**target)


@app.post("/api/v1/runs", response_model=RunOut)
def create_run(payload: RunIn) -> RunOut:
    if payload.target_id not in store.targets:
        raise HTTPException(status_code=404, detail="Target not found")
    target = store.targets[payload.target_id]
    if target.get("verification_status") != "verified":
        raise HTTPException(status_code=400, detail="Target not verified")
    if store.usage.get("runs_used", 0) >= store.usage.get("max_runs", 0):
        raise HTTPException(status_code=402, detail="Run limit reached")
    run = store.create_run(created_by="system", payload=payload.model_dump())
    store.add_audit_event(
        "run.created",
        {"run_id": run["id"], "target_id": run["target_id"], "suite_id": run["suite_id"]},
    )
    thread = threading.Thread(target=process_run, args=(run["id"],), daemon=True)
    thread.start()
    return RunOut(
        id=run["id"],
        project_id=run["project_id"],
        target_id=run["target_id"],
        suite_id=run["suite_id"],
        status=run["status"],
        created_by=run["created_by"],
        created_at=run["created_at"],
        config=run["config"],
    )


@app.get("/api/v1/runs/{run_id}", response_model=RunOut)
def get_run(run_id: str) -> RunOut:
    run = store.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunOut(
        id=run["id"],
        project_id=run["project_id"],
        target_id=run["target_id"],
        suite_id=run["suite_id"],
        status=run["status"],
        created_by=run["created_by"],
        created_at=run["created_at"],
        config=run["config"],
    )


@app.get("/api/v1/runs/{run_id}/results")
def get_run_results(run_id: str) -> dict:
    results = read_results(run_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    return results


@app.get("/api/v1/runs/{run_id}/logs")
def get_run_logs(run_id: str) -> dict:
    logs = store.run_logs.get(run_id)
    if logs is None:
        raise HTTPException(status_code=404, detail="Logs not found")
    return {"run_id": run_id, "logs": logs}


@app.get("/api/v1/runs/{run_id}/findings", response_model=List[FindingOut])
def get_findings(run_id: str) -> List[FindingOut]:
    findings = [f for f in store.findings.values() if f["run_id"] == run_id]
    return [FindingOut(**finding) for finding in findings]


@app.patch("/api/v1/findings/{finding_id}", response_model=FindingOut)
def update_finding(finding_id: str, payload: FindingUpdateIn) -> FindingOut:
    finding = store.findings.get(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding["status"] = payload.status
    return FindingOut(**finding)


@app.post("/api/v1/runs/{run_id}/cancel", response_model=RunOut)
def cancel_run(run_id: str) -> RunOut:
    run = store.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run["status"] = "cancelled"
    return RunOut(
        id=run["id"],
        project_id=run["project_id"],
        target_id=run["target_id"],
        suite_id=run["suite_id"],
        status=run["status"],
        created_by=run["created_by"],
        created_at=run["created_at"],
        config=run["config"],
    )


@app.get("/api/v1/runs/queue", response_model=RunQueueOut)
def get_queue() -> RunQueueOut:
    return RunQueueOut(queued_run_ids=list(store.run_queue))


@app.get("/api/v1/billing/usage", response_model=BillingUsageOut)
def get_billing_usage() -> BillingUsageOut:
    return BillingUsageOut(
        plan=store.org.get("plan", "trial"),
        runs_used=store.usage.get("runs_used", 0),
        max_runs=store.usage.get("max_runs", 0),
    )


@app.post("/api/v1/billing/portal", response_model=BillingPortalOut)
def get_billing_portal() -> BillingPortalOut:
    return BillingPortalOut(url="https://billing.example.com/portal")


@app.get("/api/v1/audit/events", response_model=List[AuditEventOut])
def get_audit_events() -> List[AuditEventOut]:
    return [AuditEventOut(**event) for event in store.audit_events]
