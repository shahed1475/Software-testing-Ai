import { useEffect, useMemo, useState } from "react";

type Project = {
  id: string;
  name: string;
  description?: string | null;
};

type Target = {
  id: string;
  project_id: string;
  name: string;
  type: string;
  scope: Record<string, unknown>;
  verification_status: string;
};

type Finding = {
  id: string;
  run_id: string;
  severity: string;
  type: string;
  location: string;
  status: string;
};

type BillingUsage = {
  plan: string;
  runs_used: number;
  max_runs: number;
};

type AuditEvent = {
  id: string;
  action: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

const suites = [
  { id: "suite-api", label: "API Tests", type: "functional" },
  { id: "suite-web", label: "Web UI Tests", type: "functional" },
  { id: "suite-zap-baseline", label: "ZAP Baseline (safe)", type: "zap_baseline" },
  { id: "suite-pentest-web", label: "PenTest Web Surface", type: "pentest" },
  { id: "suite-pentest-api", label: "PenTest API Surface", type: "pentest" },
  { id: "suite-pentest-network", label: "PenTest Network", type: "pentest" }
];

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [selectedTarget, setSelectedTarget] = useState<string>("");
  const [selectedSuite, setSelectedSuite] = useState<string>(suites[0].id);
  const [runId, setRunId] = useState<string>("");
  const [runStatus, setRunStatus] = useState<string>("idle");
  const [logs, setLogs] = useState<string[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [billing, setBilling] = useState<BillingUsage | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);

  const [projectName, setProjectName] = useState("");
  const [targetName, setTargetName] = useState("");
  const [targetType, setTargetType] = useState("web");
  const [targetUrl, setTargetUrl] = useState("");
  const [safeMode, setSafeMode] = useState(true);
  const [rateLimit, setRateLimit] = useState(60);

  const selectedSuiteType = useMemo(() => {
    return suites.find((suite) => suite.id === selectedSuite)?.type || "functional";
  }, [selectedSuite]);

  useEffect(() => {
    fetch(`${apiBase}/projects`)
      .then((res) => res.json())
      .then((data) => setProjects(data))
      .catch(() => setProjects([]));

    fetch(`${apiBase}/billing/usage`)
      .then((res) => res.json())
      .then((data) => setBilling(data))
      .catch(() => setBilling(null));

    fetch(`${apiBase}/audit/events`)
      .then((res) => res.json())
      .then((data) => setAuditEvents(data))
      .catch(() => setAuditEvents([]));
  }, []);

  useEffect(() => {
    if (!selectedProject) return;
    fetch(`${apiBase}/projects/${selectedProject}/targets`)
      .then((res) => res.json())
      .then((data) => setTargets(data))
      .catch(() => setTargets([]));
  }, [selectedProject]);

  useEffect(() => {
    if (!selectedTarget) return;
    const target = targets.find((item) => item.id === selectedTarget);
    const url = target && typeof target.scope?.url === "string" ? target.scope.url : "";
    setTargetUrl(url);
  }, [selectedTarget, targets]);

  useEffect(() => {
    if (!runId) return;
    const interval = setInterval(() => {
      Promise.all([
        fetch(`${apiBase}/runs/${runId}`).then((res) => res.json()),
        fetch(`${apiBase}/runs/${runId}/logs`).then((res) => res.json()),
        fetch(`${apiBase}/runs/${runId}/findings`).then((res) => res.json()),
        fetch(`${apiBase}/billing/usage`).then((res) => res.json())
      ])
        .then(([run, logData, findingData, billingData]) => {
          setRunStatus(run.status);
          setLogs(logData.logs || []);
          setFindings(findingData || []);
          setBilling(billingData);
        })
        .catch(() => null);
    }, 1500);
    return () => clearInterval(interval);
  }, [runId]);

  const createProject = async () => {
    const res = await fetch(`${apiBase}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: projectName, description: "" })
    });
    if (!res.ok) {
      const data = await res.json();
      alert(data.detail || "Failed to create project");
      return;
    }
    const data = await res.json();
    setProjects((prev) => [...prev, data]);
    setProjectName("");
  };

  const createTarget = async () => {
    if (!selectedProject) return;
    const res = await fetch(`${apiBase}/projects/${selectedProject}/targets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: targetName,
        type: targetType,
        scope: { url: targetUrl }
      })
    });
    if (!res.ok) {
      const data = await res.json();
      alert(data.detail || "Failed to create target");
      return;
    }
    const data = await res.json();
    setTargets((prev) => [...prev, data]);
    setTargetName("");
    setTargetUrl("");
  };

  const verifyTarget = async () => {
    if (!selectedTarget) return;
    const res = await fetch(`${apiBase}/targets/${selectedTarget}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method: "http", proof_value: "demo" })
    });
    if (!res.ok) {
      const data = await res.json();
      alert(data.detail || "Failed to verify target");
      return;
    }
    const data = await res.json();
    setTargets((prev) => prev.map((t) => (t.id === data.id ? data : t)));
  };

  const startRun = async () => {
    if (!selectedProject || !selectedTarget) return;
    const res = await fetch(`${apiBase}/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: selectedProject,
        target_id: selectedTarget,
        suite_id: selectedSuite,
        config: { target_url: targetUrl, scan_type: selectedSuiteType },
        safe_mode: safeMode,
        rate_limit: rateLimit
      })
    });
    if (!res.ok) {
      const data = await res.json();
      alert(data.detail || "Failed to start run");
      return;
    }
    const data = await res.json();
    setRunId(data.id);
    setRunStatus(data.status);
    fetch(`${apiBase}/audit/events`)
      .then((res) => res.json())
      .then((events) => setAuditEvents(events))
      .catch(() => setAuditEvents([]));
  };

  return (
    <div className="container">
      <div className="hero">
        <h1>SaaS Test and PenTest Platform</h1>
        <p>Configure targets, run suites, and track findings with safe execution controls.</p>
        <div className="badges">
          <span className="badge">MVP workflow</span>
          <span className="badge">Safe scan presets</span>
          <span className="badge">Live run logs</span>
        </div>
      </div>

      <div className="layout">
        <div className="panel">
          <h3>Onboarding</h3>
          <div className="panel-subtitle">Create a project and add your first target.</div>
          <div className="form-grid">
            <div className="field">
              <label>Project name</label>
              <input value={projectName} onChange={(e) => setProjectName(e.target.value)} />
            </div>
            <div className="field" style={{ alignSelf: "end" }}>
              <button className="btn btn-primary" onClick={createProject}>Create project</button>
            </div>
          </div>
          <div className="form-grid" style={{ marginTop: 16 }}>
            <div className="field">
              <label>Target name</label>
              <input value={targetName} onChange={(e) => setTargetName(e.target.value)} />
            </div>
            <div className="field">
              <label>Target type</label>
              <select value={targetType} onChange={(e) => setTargetType(e.target.value)}>
                <option value="web">Web</option>
                <option value="api">API</option>
                <option value="network">Network</option>
              </select>
            </div>
            <div className="field">
              <label>Target URL</label>
              <input value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} placeholder="https://app.example.com" />
            </div>
            <div className="field" style={{ alignSelf: "end" }}>
              <button className="btn btn-secondary" onClick={createTarget}>Add target</button>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Project and Target</h3>
          <div className="panel-subtitle">Choose a project and target to scan.</div>
          <div className="form-grid">
            <div className="field">
              <label>Project</label>
              <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)}>
                <option value="">Select project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Target</label>
              <select value={selectedTarget} onChange={(e) => setSelectedTarget(e.target.value)}>
                <option value="">Select target</option>
                {targets.map((target) => (
                  <option key={target.id} value={target.id}>
                    {target.name} ({target.verification_status})
                  </option>
                ))}
              </select>
            </div>
            <div className="field" style={{ alignSelf: "end" }}>
              <button className="btn btn-secondary" onClick={verifyTarget}>Verify target</button>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Run configuration</h3>
          <div className="panel-subtitle">Select suites and safety controls.</div>
          <div className="scenario-list">
            {suites.map((suite) => (
              <button
                key={suite.id}
                className={`scenario-item ${suite.id === selectedSuite ? "selected" : ""}`}
                onClick={() => setSelectedSuite(suite.id)}
              >
                {suite.label}
              </button>
            ))}
          </div>
          <div className="form-grid" style={{ marginTop: 12 }}>
            <div className="field">
              <label>Safe mode</label>
              <select value={safeMode ? "true" : "false"} onChange={(e) => setSafeMode(e.target.value === "true")}>
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
            </div>
            <div className="field">
              <label>Rate limit (req/min)</label>
              <input
                type="number"
                value={rateLimit}
                onChange={(e) => setRateLimit(Number(e.target.value))}
              />
            </div>
          </div>
          <div className="buttons">
            <button className="btn btn-primary" onClick={startRun}>Start run</button>
            <span className="status-pill">Status: {runStatus}</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: runStatus === "completed" ? "100%" : runStatus === "running" ? "60%" : "10%" }} />
          </div>
        </div>

        <div className="panel">
          <h3>Live run logs</h3>
          <div className="panel-subtitle">Backend logs for the latest run.</div>
          <div className="log-box">
            {logs.length === 0 && <div className="log-entry">No logs yet.</div>}
            {logs.map((log, index) => (
              <div key={`${log}-${index}`} className="log-entry">{log}</div>
            ))}
          </div>
        </div>

        <div className="panel">
          <h3>Findings</h3>
          <div className="panel-subtitle">Triage findings produced by the scan.</div>
          <table className="table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Type</th>
                <th>Location</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {findings.length === 0 && (
                <tr>
                  <td colSpan={4}>No findings yet.</td>
                </tr>
              )}
              {findings.map((finding) => (
                <tr key={finding.id}>
                  <td className={`severity-${finding.severity.toLowerCase()}`}>{finding.severity}</td>
                  <td>{finding.type}</td>
                  <td>{finding.location}</td>
                  <td>{finding.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <h3>Billing overview</h3>
          <div className="panel-subtitle">Current plan and usage limits.</div>
          {billing ? (
            <div className="form-grid">
              <div className="field">
                <label>Plan</label>
                <input value={billing.plan} readOnly />
              </div>
              <div className="field">
                <label>Runs used</label>
                <input value={billing.runs_used} readOnly />
              </div>
              <div className="field">
                <label>Max runs</label>
                <input value={billing.max_runs} readOnly />
              </div>
            </div>
          ) : (
            <div className="log-entry">Billing data unavailable.</div>
          )}
        </div>

        <div className="panel">
          <h3>Audit events</h3>
          <div className="panel-subtitle">Recent actions for compliance review.</div>
          <div className="log-box">
            {auditEvents.length === 0 && <div className="log-entry">No audit events yet.</div>}
            {auditEvents.slice().reverse().map((event) => (
              <div key={event.id} className="log-entry">
                {event.action} · {new Date(event.created_at).toLocaleString()}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
