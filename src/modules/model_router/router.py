"""
Intelligent Model Routing Engine for AI Control Center.
Performs rule-based multi-objective optimization across candidate model profiles.
Selects the lowest-cost model satisfying user latency, quality, and cost constraints.
"""

from typing import List, Optional, Tuple, Dict, Any
from src.models.schemas import ModelProfile, RoutingDecision, CandidateEvaluation
from src.modules.cost_analytics.calculator import CostCalculator


class ModelRouter:
    """Rule-based intelligent router optimizing for minimum cost given quality and latency SLA."""

    @staticmethod
    def route_request(
        models: List[ModelProfile],
        input_tokens: int,
        estimated_output_tokens: int = 500,
        max_cost_usd: Optional[float] = None,
        max_latency_ms: Optional[float] = None,
        min_quality_score: Optional[float] = None,
        benchmark_baseline_model_id: str = "gpt-4o"
    ) -> RoutingDecision:
        """
        Evaluate all active models against defined constraints.
        Selects the lowest-cost eligible candidate and logs rejection reasons for others.
        """
        if not models:
            raise ValueError("No active model profiles provided for routing.")

        active_models = [m for m in models if m.is_active]
        if not active_models:
            raise ValueError("All model profiles are currently marked inactive.")

        evaluations: List[CandidateEvaluation] = []
        eligible_candidates: List[Tuple[ModelProfile, float, CandidateEvaluation]] = []

        # Find baseline cost for comparison
        baseline_model = next((m for m in active_models if m.id == benchmark_baseline_model_id), active_models[0])
        baseline_cost = CostCalculator.calculate_cost(input_tokens, estimated_output_tokens, baseline_model)

        for model in active_models:
            cost = CostCalculator.calculate_cost(input_tokens, estimated_output_tokens, model)
            rejection_reasons = []

            # Check quality constraint
            if min_quality_score is not None and model.quality_score < min_quality_score:
                rejection_reasons.append(
                    f"Quality score {model.quality_score:.1f} is below minimum requirement of {min_quality_score:.1f}"
                )

            # Check latency constraint
            if max_latency_ms is not None and model.avg_latency_ms > max_latency_ms:
                rejection_reasons.append(
                    f"Average latency {model.avg_latency_ms:.0f}ms exceeds maximum threshold of {max_latency_ms:.0f}ms"
                )

            # Check cost constraint
            if max_cost_usd is not None and cost > max_cost_usd:
                rejection_reasons.append(
                    f"Estimated cost ${cost:.6f} exceeds maximum ceiling of ${max_cost_usd:.6f}"
                )

            is_eligible = len(rejection_reasons) == 0

            cand_eval = CandidateEvaluation(
                model_id=model.id,
                model_name=model.name,
                provider=model.provider,
                cost_usd=cost,
                latency_ms=model.avg_latency_ms,
                quality_score=model.quality_score,
                eligible=is_eligible,
                rejection_reasons=rejection_reasons,
            )
            evaluations.append(cand_eval)

            if is_eligible:
                eligible_candidates.append((model, cost, cand_eval))

        # Decision Logic:
        if eligible_candidates:
            # Sort by lowest cost first, then higher quality as tie-breaker
            eligible_candidates.sort(key=lambda item: (item[1], -item[0].quality_score))
            chosen_model, chosen_cost, chosen_eval = eligible_candidates[0]

            # Calculate savings vs baseline
            if baseline_cost > 0:
                savings_pct = max(0.0, ((baseline_cost - chosen_cost) / baseline_cost) * 100.0)
            else:
                savings_pct = 0.0

            constraints_str = []
            if min_quality_score: constraints_str.append(f"Quality ≥ {min_quality_score}")
            if max_latency_ms: constraints_str.append(f"Latency ≤ {max_latency_ms}ms")
            if max_cost_usd: constraints_str.append(f"Cost ≤ ${max_cost_usd:.4f}")
            c_desc = ", ".join(constraints_str) if constraints_str else "Standard Policy"

            reason = (
                f"Selected '{chosen_model.name}' as the lowest-cost eligible model "
                f"(${chosen_cost:.6f}/req) meeting all constraints ({c_desc}). "
                f"Yields {savings_pct:.1f}% estimated savings compared to baseline {baseline_model.name}."
            )

        else:
            # Fallback if no candidate satisfies 100% of strict constraints:
            # Select the candidate with highest quality that doesn't exceed cost, or best overall compromise
            active_models_sorted = sorted(active_models, key=lambda m: (-m.quality_score, CostCalculator.calculate_cost(input_tokens, estimated_output_tokens, m)))
            chosen_model = active_models_sorted[0]
            chosen_cost = CostCalculator.calculate_cost(input_tokens, estimated_output_tokens, chosen_model)
            savings_pct = 0.0

            reason = (
                f"Fallback Selection: No available model satisfied all strict constraints simultaneously. "
                f"Selected '{chosen_model.name}' as the optimal quality compromise."
            )

        # Sort candidate evaluations for clean presentation (eligible first, then by quality)
        evaluations.sort(key=lambda e: (not e.eligible, e.cost_usd))

        return RoutingDecision(
            selected_model_id=chosen_model.id,
            selected_model_name=chosen_model.name,
            selection_reason=reason,
            estimated_latency_ms=chosen_model.avg_latency_ms,
            cost_savings_pct=round(savings_pct, 1),
            candidate_evaluations=evaluations,
        )
