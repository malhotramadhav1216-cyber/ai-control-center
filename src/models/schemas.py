"""
Pydantic data models and schemas for AI Control Center.
Ensures strong typing, data validation, and clean contracts between modules.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class RequestStatus(str, Enum):
    ALLOWED = "ALLOWED"
    REDACTED = "REDACTED"
    FLAGGED = "FLAGGED"
    BLOCKED = "BLOCKED"


class RiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingType(str, Enum):
    PII_EMAIL = "PII_EMAIL"
    PII_PHONE = "PII_PHONE"
    PII_ID = "PII_ID"
    PII_CREDIT_CARD = "PII_CREDIT_CARD"
    API_KEY = "API_KEY"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    CONFIDENTIAL_KEYWORD = "CONFIDENTIAL_KEYWORD"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    REDACT = "REDACT"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class Department(BaseModel):
    id: str
    name: str
    monthly_budget: float = 5000.0
    created_at: Optional[datetime] = None


class ModelProfile(BaseModel):
    id: str
    name: str
    provider: str
    cost_per_million_input: float  # in USD
    cost_per_million_output: float  # in USD
    avg_latency_ms: float
    quality_score: float  # 1.0 to 10.0 scale
    max_context_tokens: int = 128000
    is_active: bool = True
    description: Optional[str] = None


class GovernancePolicy(BaseModel):
    id: str = "default_policy"
    name: str = "Enterprise Standard AI Policy"
    pii_action: PolicyAction = PolicyAction.REDACT
    injection_action: PolicyAction = PolicyAction.BLOCK
    high_risk_threshold: float = 0.70
    require_approval_above_cost: float = 5.0
    store_prompt_previews: bool = False  # Privacy toggle: if false, do not persist raw prompts


class SecurityFinding(BaseModel):
    id: Optional[str] = None
    finding_type: FindingType
    severity: Severity
    matched_pattern: str
    explanation: str
    action_taken: str


class CandidateEvaluation(BaseModel):
    model_id: str
    model_name: str
    provider: str
    cost_usd: float
    latency_ms: float
    quality_score: float
    eligible: bool
    rejection_reasons: List[str] = Field(default_factory=list)


class RoutingDecision(BaseModel):
    id: Optional[str] = None
    request_id: Optional[str] = None
    selected_model_id: str
    selected_model_name: str
    selection_reason: str
    estimated_latency_ms: float
    cost_savings_pct: float = 0.0
    candidate_evaluations: List[CandidateEvaluation] = Field(default_factory=list)


class RequestRecord(BaseModel):
    id: str
    timestamp: datetime
    department_id: str
    department_name: Optional[str] = None
    application_name: str
    user_identifier: str
    task_type: str
    request_status: RequestStatus
    risk_level: RiskLevel
    selected_model_id: Optional[str] = None
    selected_model_name: Optional[str] = None
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    prompt_summary: Optional[str] = None
    prompt_hash: str
    processing_time_ms: float = 0.0
    recorded_action: str
    security_findings: List[SecurityFinding] = Field(default_factory=list)
    routing_decision: Optional[RoutingDecision] = None


class AuditLog(BaseModel):
    id: str
    timestamp: datetime
    request_id: Optional[str] = None
    event_type: str
    actor: str
    details: str
    ip_address: str = "127.0.0.1"


class GatewayInput(BaseModel):
    prompt: str
    department_id: str
    application_name: str
    user_identifier: str = "demo_employee"
    task_type: str = "General QA"
    max_cost_usd: Optional[float] = None
    max_latency_ms: Optional[float] = None
    min_quality_score: Optional[float] = None


class WorkflowResult(BaseModel):
    request_id: str
    status: RequestStatus
    risk_level: RiskLevel
    original_prompt_hash: str
    sanitized_prompt: str
    findings: List[SecurityFinding] = Field(default_factory=list)
    routing_decision: Optional[RoutingDecision] = None
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    recorded_action: str
    simulated_response: Optional[str] = None
    processing_time_ms: float = 0.0
    is_blocked: bool = False
    block_reason: Optional[str] = None
