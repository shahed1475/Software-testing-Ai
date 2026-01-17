import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from saas_api.main import app  # noqa: E402


client = TestClient(app)


def test_mvp_flow():
    project_resp = client.post("/api/v1/projects", json={"name": "Demo", "description": ""})
    assert project_resp.status_code == 200
    project_id = project_resp.json()["id"]

    target_resp = client.post(
        f"/api/v1/projects/{project_id}/targets",
        json={"name": "Demo Target", "type": "web", "scope": {"url": "https://example.com"}},
    )
    assert target_resp.status_code == 200
    target_id = target_resp.json()["id"]

    verify_resp = client.post(
        f"/api/v1/targets/{target_id}/verify",
        json={"method": "http", "proof_value": "demo"},
    )
    assert verify_resp.status_code == 200

    run_resp = client.post(
        "/api/v1/runs",
        json={
            "project_id": project_id,
            "target_id": target_id,
            "suite_id": "suite-pentest-web",
            "config": {"target_url": "https://example.com", "scan_type": "pentest"},
            "safe_mode": True,
            "rate_limit": 60,
        },
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["id"]

    for _ in range(5):
        status_resp = client.get(f"/api/v1/runs/{run_id}")
        assert status_resp.status_code == 200
        if status_resp.json()["status"] == "completed":
            break
        time.sleep(0.5)

    results_resp = client.get(f"/api/v1/runs/{run_id}/results")
    assert results_resp.status_code == 200
    findings_resp = client.get(f"/api/v1/runs/{run_id}/findings")
    assert findings_resp.status_code == 200
    assert findings_resp.json(), "Expected findings to be persisted"
