"""
Integrated AI Gateway Workflow for AI Control Center.
Orchestrates the complete lifecycle:
Request Ingestion -> Security/PII Scan -> Policy Enforcement ->
Model Routing (if unblocked) -> Provider Simulation -> Audit Logging.
"""

import hashlib
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from src.models.schemas import (
    GatewayInput,
    WorkflowResult,
    RequestRecord,
    RequestStatus,
    RiskLevel,
    PolicyAction,
    GovernancePolicy,
)
from src.modules.cost_analytics.calculator import CostCalculator
from src.modules.pii_guard.scanner import RegexSecurityScanner
from src.modules.model_router.router import ModelRouter
from src.modules.model_router.provider_adapter import SimulatedGatewayProvider
from src.database.repository import Repository


class AIGateway:
    """Enterprise AI Governance Gateway Pipeline."""

    def __init__(self):
        self.scanner = RegexSecurityScanner()
        self.provider = SimulatedGatewayProvider()

    def process_request(
        self,
        input_data: GatewayInput,
        persist_to_db: bool = True
    ) -> WorkflowResult:
        """
        Execute end-to-end governance pipeline for an incoming prompt.
        Ensures blocked requests do not proceed through model routing.
        """
        start_time = time.perf_counter()
        req_id = f"req_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        prompt = input_data.prompt.strip()
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        # Retrieve governance policy
        policy = Repository.get_governance_policy()

        # -------------------------------------------------------------
        # STEP 1: PII & Adversarial Risk Inspection
        # -------------------------------------------------------------
        scan_result = self.scanner.scan(prompt)

        # -------------------------------------------------------------
        # STEP 2: Policy Enforcement
        # -------------------------------------------------------------
        is_blocked = False
        block_reason = None
        final_status = RequestStatus.ALLOWED
        effective_prompt = prompt

        has_injection = any(f.finding_type.value in ["PROMPT_INJECTION", "API_KEY"] for f in scan_result.findings)
        has_pii = any("PII" in f.finding_type.value for f in scan_result.findings)

        if has_injection and policy.injection_action == PolicyAction.BLOCK:
            is_blocked = True
            final_status = RequestStatus.BLOCKED
            block_reason = "Prompt violates safety policy: Prompt injection or high-risk credential pattern detected."
        elif has_pii:
            if policy.pii_action == PolicyAction.BLOCK:
                is_blocked = True
                final_status = RequestStatus.BLOCKED
                block_reason = "Prompt violates data privacy policy: Confidential PII detected and policy requires hard block."
            elif policy.pii_action == PolicyAction.REDACT:
                final_status = RequestStatus.REDACTED
                effective_prompt = scan_result.redacted_prompt
            elif policy.pii_action == PolicyAction.FLAG:
                final_status = RequestStatus.FLAGGED
            else:
                final_status = RequestStatus.ALLOWED
        elif scan_result.risk_score >= policy.high_risk_threshold:
            is_blocked = True
            final_status = RequestStatus.BLOCKED
            block_reason = f"Composite risk score ({scan_result.risk_score:.2f}) exceeded policy threshold ({policy.high_risk_threshold:.2f})."

        # -------------------------------------------------------------
        # STEP 3: Routing & Execution (Skipped if Blocked)
        # -------------------------------------------------------------
        routing_decision = None
        simulated_response = None
        selected_model_id = None
        input_tokens = CostCalculator.estimate_tokens(effective_prompt)
        output_tokens = 0
        cost_usd = 0.0

        if is_blocked:
            recorded_action = f"REQUEST_BLOCKED: {block_reason}"
            simulated_response = (
                "[REQUEST INTERCEPTED BY AI CONTROL CENTER GATEWAY]\n\n"
                f"Status: BLOCKED\n"
                f"Reason: {block_reason}\n"
                "The request was halted prior to model routing. No external API was contacted."
            )
        else:
            # Load active model profiles
            models = Repository.get_model_profiles(active_only=True)
            if not models:
                # Fallback if DB not seeded
                from src.database.seed_data import seed_database
                seed_database()
                models = Repository.get_model_profiles(active_only=True)

            # Heuristic output token estimation based on task
            output_tokens = 450
            if input_data.task_type == "Code Generation":
                output_tokens = 850
            elif input_data.task_type == "Document Summary":
                output_tokens = 500
            elif input_data.task_type == "Customer Support":
                output_tokens = 280

            # Execute Model Routing
            routing_decision = ModelRouter.route_request(
                models=models,
                input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
                max_cost_usd=input_data.max_cost_usd,
                max_latency_ms=input_data.max_latency_ms,
                min_quality_score=input_data.min_quality_score,
            )

            selected_model_id = routing_decision.selected_model_id
            chosen_profile = next((m for m in models if m.id == selected_model_id), models[0])

            # Calculate precise cost
            cost_usd = CostCalculator.calculate_cost(input_tokens, output_tokens, chosen_profile)

            # Generate simulated response
            provider_resp = self.provider.execute_request(
                prompt=effective_prompt,
                model_id=selected_model_id,
                expected_output_tokens=output_tokens
            )
            simulated_response = provider_resp.content

            recorded_action = (
                f"REQUEST_{final_status.value}_AND_ROUTED_TO_{selected_model_id.upper()}"
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Safe summary for audit record (respecting privacy toggle)
        if policy.store_prompt_previews:
            prompt_preview = effective_prompt[:120] + ("..." if len(effective_prompt) > 120 else "")
        else:
            prompt_preview = f"Sanitized task [{input_data.task_type}] - {input_tokens} tokens"

        # -------------------------------------------------------------
        # STEP 4: Usage Logging & Audit Trail Persistence
        # -------------------------------------------------------------
        if persist_to_db:
            req_record = RequestRecord(
                id=req_id,
                timestamp=now,
                department_id=input_data.department_id,
                application_name=input_data.application_name,
                user_identifier=input_data.user_identifier,
                task_type=input_data.task_type,
                request_status=final_status,
                risk_level=scan_result.risk_level,
                selected_model_id=selected_model_id,
                estimated_input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
                estimated_cost_usd=cost_usd,
                prompt_summary=prompt_preview,
                prompt_hash=prompt_hash,
                processing_time_ms=round(elapsed_ms, 2),
                recorded_action=recorded_action,
            )

            Repository.save_request(
                req=req_record,
                findings=scan_result.findings,
                routing=routing_decision,
                actor=input_data.user_identifier,
            )

        return WorkflowResult(
            request_id=req_id,
            status=final_status,
            risk_level=scan_result.risk_level,
            original_prompt_hash=prompt_hash,
            sanitized_prompt=effective_prompt,
            findings=scan_result.findings,
            routing_decision=routing_decision,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            estimated_cost_usd=cost_usd,
            recorded_action=recorded_action,
            simulated_response=simulated_response,
            processing_time_ms=round(elapsed_ms, 2),
            is_blocked=is_blocked,
            block_reason=block_reason,
        )
