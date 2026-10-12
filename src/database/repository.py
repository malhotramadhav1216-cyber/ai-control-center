"""
Repository layer for AI Control Center.
Encapsulates all database operations using parameterized queries,
separating data persistence from presentation and business logic.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.database.connection import get_db_connection, execute_query, execute_write
from src.models.schemas import (
    Department,
    ModelProfile,
    GovernancePolicy,
    PolicyAction,
    RequestRecord,
    RequestStatus,
    RiskLevel,
    SecurityFinding,
    FindingType,
    Severity,
    RoutingDecision,
    CandidateEvaluation,
    AuditLog,
)


class Repository:
    """Data access repository for database interactions."""

    # -------------------------------------------------------------
    # Departments
    # -------------------------------------------------------------
    @staticmethod
    def get_departments() -> List[Department]:
        rows = execute_query("SELECT id, name, monthly_budget, created_at FROM departments ORDER BY name ASC")
        return [
            Department(
                id=r["id"],
                name=r["name"],
                monthly_budget=float(r["monthly_budget"]),
                created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else None
            )
            for r in rows
        ]

    @staticmethod
    def get_department(dept_id: str) -> Optional[Department]:
        rows = execute_query("SELECT id, name, monthly_budget, created_at FROM departments WHERE id = ?", (dept_id,))
        if not rows:
            return None
        r = rows[0]
        return Department(
            id=r["id"],
            name=r["name"],
            monthly_budget=float(r["monthly_budget"]),
            created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else None
        )

    @staticmethod
    def update_department_budget(dept_id: str, monthly_budget: float) -> bool:
        rows_affected = execute_write(
            "UPDATE departments SET monthly_budget = ? WHERE id = ?",
            (monthly_budget, dept_id)
        )
        return rows_affected > 0

    # -------------------------------------------------------------
    # Model Profiles
    # -------------------------------------------------------------
    @staticmethod
    def get_model_profiles(active_only: bool = True) -> List[ModelProfile]:
        query = "SELECT * FROM model_profiles"
        params: list = []
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY quality_score DESC, cost_per_million_input ASC"

        rows = execute_query(query, tuple(params))
        return [
            ModelProfile(
                id=r["id"],
                name=r["name"],
                provider=r["provider"],
                cost_per_million_input=float(r["cost_per_million_input"]),
                cost_per_million_output=float(r["cost_per_million_output"]),
                avg_latency_ms=float(r["avg_latency_ms"]),
                quality_score=float(r["quality_score"]),
                max_context_tokens=int(r["max_context_tokens"]),
                is_active=bool(r["is_active"]),
                description=r["description"],
            )
            for r in rows
        ]

    @staticmethod
    def get_model_profile(model_id: str) -> Optional[ModelProfile]:
        rows = execute_query("SELECT * FROM model_profiles WHERE id = ?", (model_id,))
        if not rows:
            return None
        r = rows[0]
        return ModelProfile(
            id=r["id"],
            name=r["name"],
            provider=r["provider"],
            cost_per_million_input=float(r["cost_per_million_input"]),
            cost_per_million_output=float(r["cost_per_million_output"]),
            avg_latency_ms=float(r["avg_latency_ms"]),
            quality_score=float(r["quality_score"]),
            max_context_tokens=int(r["max_context_tokens"]),
            is_active=bool(r["is_active"]),
            description=r["description"],
        )

    @staticmethod
    def update_model_profile(
        model_id: str,
        cost_in: float,
        cost_out: float,
        latency_ms: float,
        quality: float,
        is_active: bool
    ) -> bool:
        count = execute_write(
            """
            UPDATE model_profiles
            SET cost_per_million_input = ?,
                cost_per_million_output = ?,
                avg_latency_ms = ?,
                quality_score = ?,
                is_active = ?
            WHERE id = ?
            """,
            (cost_in, cost_out, latency_ms, quality, 1 if is_active else 0, model_id)
        )
        return count > 0

    # -------------------------------------------------------------
    # Governance Policies
    # -------------------------------------------------------------
    @staticmethod
    def get_governance_policy() -> GovernancePolicy:
        rows = execute_query("SELECT * FROM governance_policies LIMIT 1")
        if not rows:
            return GovernancePolicy()
        r = rows[0]
        return GovernancePolicy(
            id=r["id"],
            name=r["name"],
            pii_action=PolicyAction(r["pii_action"]),
            injection_action=PolicyAction(r["injection_action"]),
            high_risk_threshold=float(r["high_risk_threshold"]),
            require_approval_above_cost=float(r["require_approval_above_cost"]),
            store_prompt_previews=bool(r["store_prompt_previews"]),
        )

    @staticmethod
    def update_governance_policy(policy: GovernancePolicy) -> bool:
        count = execute_write(
            """
            INSERT INTO governance_policies (
                id, name, pii_action, injection_action, high_risk_threshold,
                require_approval_above_cost, store_prompt_previews, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                pii_action = excluded.pii_action,
                injection_action = excluded.injection_action,
                high_risk_threshold = excluded.high_risk_threshold,
                require_approval_above_cost = excluded.require_approval_above_cost,
                store_prompt_previews = excluded.store_prompt_previews,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                policy.id,
                policy.name,
                policy.pii_action.value,
                policy.injection_action.value,
                policy.high_risk_threshold,
                policy.require_approval_above_cost,
                1 if policy.store_prompt_previews else 0,
            )
        )
        return count > 0

    # -------------------------------------------------------------
    # Requests & Workflow Persistence
    # -------------------------------------------------------------
    @staticmethod
    def save_request(
        req: RequestRecord,
        findings: Optional[List[SecurityFinding]] = None,
        routing: Optional[RoutingDecision] = None,
        actor: str = "AI_Gateway"
    ) -> None:
        """Persist a complete request, its security findings, routing decision, and audit log atomically."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Insert Request
            cursor.execute(
                """
                INSERT INTO requests (
                    id, timestamp, department_id, application_name, user_identifier,
                    task_type, request_status, risk_level, selected_model_id,
                    estimated_input_tokens, estimated_output_tokens, estimated_cost_usd,
                    prompt_summary, prompt_hash, processing_time_ms, recorded_action
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    req.id,
                    req.timestamp.isoformat(),
                    req.department_id,
                    req.application_name,
                    req.user_identifier,
                    req.task_type,
                    req.request_status.value,
                    req.risk_level.value,
                    req.selected_model_id,
                    req.estimated_input_tokens,
                    req.estimated_output_tokens,
                    req.estimated_cost_usd,
                    req.prompt_summary,
                    req.prompt_hash,
                    req.processing_time_ms,
                    req.recorded_action,
                )
            )

            # Insert Security Findings
            if findings:
                for f in findings:
                    import uuid
                    f_id = f.id or f"find_{uuid.uuid4().hex[:12]}"
                    cursor.execute(
                        """
                        INSERT INTO security_findings (
                            id, request_id, finding_type, severity, matched_pattern,
                            explanation, action_taken, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f_id,
                            req.id,
                            f.finding_type.value,
                            f.severity.value,
                            f.matched_pattern,
                            f.explanation,
                            f.action_taken,
                            req.timestamp.isoformat(),
                        )
                    )

            # Insert Routing Decision
            if routing and req.selected_model_id:
                import uuid
                r_id = routing.id or f"rout_{uuid.uuid4().hex[:12]}"
                evaluations_json = json.dumps([e.model_dump() for e in routing.candidate_evaluations])
                cursor.execute(
                    """
                    INSERT INTO routing_decisions (
                        id, request_id, selected_model_id, selection_reason,
                        candidate_evaluations, estimated_latency_ms, cost_savings_pct, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r_id,
                        req.id,
                        routing.selected_model_id,
                        routing.selection_reason,
                        evaluations_json,
                        routing.estimated_latency_ms,
                        routing.cost_savings_pct,
                        req.timestamp.isoformat(),
                    )
                )

            # Insert Audit Log entry
            import uuid
            audit_id = f"aud_{uuid.uuid4().hex[:12]}"
            event_type = "SECURITY_BLOCKED" if req.request_status == RequestStatus.BLOCKED else "REQUEST_PROCESSED"
            details = f"Action: {req.recorded_action} | Model: {req.selected_model_id or 'None'} | Cost: ${req.estimated_cost_usd:.6f} | Tokens: {req.estimated_input_tokens + req.estimated_output_tokens}"
            cursor.execute(
                """
                INSERT INTO audit_logs (id, timestamp, request_id, event_type, actor, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    req.timestamp.isoformat(),
                    req.id,
                    event_type,
                    actor,
                    details,
                    "10.0.1.42"
                )
            )

    @staticmethod
    def get_requests(
        department_id: Optional[str] = None,
        model_id: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Retrieve filtered requests joined with department and model profiles."""
        query = """
            SELECT
                r.id,
                r.timestamp,
                r.department_id,
                d.name AS department_name,
                r.application_name,
                r.user_identifier,
                r.task_type,
                r.request_status,
                r.risk_level,
                r.selected_model_id,
                m.name AS model_name,
                m.provider AS model_provider,
                r.estimated_input_tokens,
                r.estimated_output_tokens,
                (r.estimated_input_tokens + r.estimated_output_tokens) AS total_tokens,
                r.estimated_cost_usd,
                r.prompt_summary,
                r.prompt_hash,
                r.processing_time_ms,
                r.recorded_action
            FROM requests r
            LEFT JOIN departments d ON r.department_id = d.id
            LEFT JOIN model_profiles m ON r.selected_model_id = m.id
            WHERE 1=1
        """
        params: list = []

        if department_id and department_id != "All":
            query += " AND r.department_id = ?"
            params.append(department_id)
        if model_id and model_id != "All":
            query += " AND r.selected_model_id = ?"
            params.append(model_id)
        if status and status != "All":
            query += " AND r.request_status = ?"
            params.append(status)
        if task_type and task_type != "All":
            query += " AND r.task_type = ?"
            params.append(task_type)
        if date_from:
            query += " AND date(r.timestamp) >= date(?)"
            params.append(date_from)
        if date_to:
            query += " AND date(r.timestamp) <= date(?)"
            params.append(date_to)

        query += " ORDER BY r.timestamp DESC LIMIT ?"
        params.append(limit)

        rows = execute_query(query, tuple(params))
        return [dict(r) for r in rows]

    @staticmethod
    def get_security_findings_for_request(request_id: str) -> List[Dict[str, Any]]:
        rows = execute_query(
            "SELECT * FROM security_findings WHERE request_id = ? ORDER BY severity DESC",
            (request_id,)
        )
        return [dict(r) for r in rows]

    @staticmethod
    def get_routing_decision_for_request(request_id: str) -> Optional[Dict[str, Any]]:
        rows = execute_query(
            """
            SELECT rd.*, mp.name as model_name, mp.provider as model_provider
            FROM routing_decisions rd
            JOIN model_profiles mp ON rd.selected_model_id = mp.id
            WHERE rd.request_id = ?
            """,
            (request_id,)
        )
        if not rows:
            return None
        res = dict(rows[0])
        try:
            res["candidate_evaluations"] = json.loads(res["candidate_evaluations"])
        except Exception:
            res["candidate_evaluations"] = []
        return res

    @staticmethod
    def get_audit_logs(limit: int = 200, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params: list = []
        if event_type and event_type != "All":
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = execute_query(query, tuple(params))
        return [dict(r) for r in rows]
