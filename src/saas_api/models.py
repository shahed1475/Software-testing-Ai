from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuthLoginIn(BaseModel):
    email: str
    password: str


class AuthLoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthMfaIn(BaseModel):
    code: str


class AuthMfaOut(BaseModel):
    verified: bool


class OrgOut(BaseModel):
    id: str
    name: str
    plan: str
    created_at: datetime


class UserIn(BaseModel):
    email: str
    role: str = "member"


class UserOut(BaseModel):
    id: str
    org_id: str
    email: str
    role: str
    status: str


class ProjectIn(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    org_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime


class TargetIn(BaseModel):
    name: str
    type: str = "web"
    scope: Dict[str, Any] = Field(default_factory=dict)


class TargetOut(BaseModel):
    id: str
    project_id: str
    name: str
    type: str
    scope: Dict[str, Any]
    verification_status: str
    verification_method: Optional[str] = None


class TargetVerifyIn(BaseModel):
    method: str
    proof_value: str


class RunIn(BaseModel):
    project_id: str
    target_id: str
    suite_id: str
    config: Dict[str, Any] = Field(default_factory=dict)
    safe_mode: bool = True
    rate_limit: int = 60


class RunOut(BaseModel):
    id: str
    project_id: str
    target_id: str
    suite_id: str
    status: str
    created_by: str
    created_at: datetime
    config: Dict[str, Any]


class RunQueueOut(BaseModel):
    queued_run_ids: List[str]


class BillingUsageOut(BaseModel):
    plan: str
    runs_used: int
    max_runs: int


class BillingPortalOut(BaseModel):
    url: str


class AuditEventOut(BaseModel):
    id: str
    action: str
    metadata: Dict[str, Any]
    created_at: datetime


class FindingOut(BaseModel):
    id: str
    run_id: str
    severity: str
    type: str
    location: str
    status: str


class FindingUpdateIn(BaseModel):
    status: str
