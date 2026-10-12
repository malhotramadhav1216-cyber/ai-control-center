-- AI Control Center Database Schema (SQLite Compatible)
-- Supports Enterprise AI Governance, Cost Optimization, Security & Audit Trail

CREATE TABLE IF NOT EXISTS departments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    monthly_budget REAL NOT NULL DEFAULT 5000.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    cost_per_million_input REAL NOT NULL,
    cost_per_million_output REAL NOT NULL,
    avg_latency_ms REAL NOT NULL,
    quality_score REAL NOT NULL, -- 1.0 to 10.0 scale
    max_context_tokens INTEGER NOT NULL DEFAULT 128000,
    is_active INTEGER NOT NULL DEFAULT 1,
    description TEXT
);

CREATE TABLE IF NOT EXISTS governance_policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    pii_action TEXT NOT NULL DEFAULT 'REDACT', -- ALLOW, FLAG, REDACT, BLOCK
    injection_action TEXT NOT NULL DEFAULT 'BLOCK', -- ALLOW, FLAG, BLOCK
    high_risk_threshold REAL NOT NULL DEFAULT 0.70,
    require_approval_above_cost REAL NOT NULL DEFAULT 5.0,
    store_prompt_previews INTEGER NOT NULL DEFAULT 0, -- Privacy toggle: 0 = hashed/synthetic, 1 = preview
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    department_id TEXT NOT NULL,
    application_name TEXT NOT NULL,
    user_identifier TEXT NOT NULL,
    task_type TEXT NOT NULL,
    request_status TEXT NOT NULL, -- ALLOWED, REDACTED, FLAGGED, BLOCKED
    risk_level TEXT NOT NULL, -- NONE, LOW, MEDIUM, HIGH, CRITICAL
    selected_model_id TEXT, -- NULL if request was blocked
    estimated_input_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_output_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd REAL NOT NULL DEFAULT 0.0,
    prompt_summary TEXT, -- synthetic or redacted preview
    prompt_hash TEXT NOT NULL, -- SHA-256
    processing_time_ms REAL NOT NULL DEFAULT 0.0,
    recorded_action TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (selected_model_id) REFERENCES model_profiles(id)
);

CREATE TABLE IF NOT EXISTS security_findings (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    finding_type TEXT NOT NULL, -- PII_EMAIL, PII_PHONE, PII_ID, PROMPT_INJECTION, API_KEY
    severity TEXT NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    matched_pattern TEXT NOT NULL,
    explanation TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS routing_decisions (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    selected_model_id TEXT NOT NULL,
    selection_reason TEXT NOT NULL,
    candidate_evaluations TEXT NOT NULL, -- JSON string
    estimated_latency_ms REAL NOT NULL,
    cost_savings_pct REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
    FOREIGN KEY (selected_model_id) REFERENCES model_profiles(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    request_id TEXT,
    event_type TEXT NOT NULL, -- REQUEST_PROCESSED, SECURITY_BLOCKED, POLICY_UPDATE, BUDGET_ALERT
    actor TEXT NOT NULL,
    details TEXT NOT NULL,
    ip_address TEXT DEFAULT '127.0.0.1'
);

CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests(timestamp);
CREATE INDEX IF NOT EXISTS idx_requests_dept ON requests(department_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(request_status);
CREATE INDEX IF NOT EXISTS idx_requests_model ON requests(selected_model_id);
CREATE INDEX IF NOT EXISTS idx_security_req ON security_findings(request_id);
CREATE INDEX IF NOT EXISTS idx_routing_req ON routing_decisions(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(timestamp);
