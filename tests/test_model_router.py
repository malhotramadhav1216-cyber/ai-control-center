"""
Unit tests for Intelligent Model Routing module.
Tests constraint-based model filtering, lowest-cost selection, and rejection rationale.
"""

import pytest
from src.modules.model_router.router import ModelRouter
from src.models.schemas import ModelProfile


@pytest.fixture
def model_catalog():
    return [
        ModelProfile(
            id="gpt-4o", name="GPT-4o", provider="OpenAI",
            cost_per_million_input=2.50, cost_per_million_output=10.00,
            avg_latency_ms=650.0, quality_score=9.5
        ),
        ModelProfile(
            id="claude-3-5-sonnet", name="Claude 3.5 Sonnet", provider="Anthropic",
            cost_per_million_input=3.00, cost_per_million_output=15.00,
            avg_latency_ms=700.0, quality_score=9.7
        ),
        ModelProfile(
            id="gpt-4o-mini", name="GPT-4o mini", provider="OpenAI",
            cost_per_million_input=0.15, cost_per_million_output=0.60,
            avg_latency_ms=300.0, quality_score=8.2
        ),
        ModelProfile(
            id="mistral-7b", name="Mistral 7B", provider="Mistral AI",
            cost_per_million_input=0.10, cost_per_million_output=0.10,
            avg_latency_ms=180.0, quality_score=7.1
        ),
    ]


def test_routing_selects_lowest_cost_meeting_quality(model_catalog):
    # Require quality >= 8.0, should select gpt-4o-mini over gpt-4o and claude because it is cheaper
    # and over mistral-7b because mistral's quality is 7.1 < 8.0
    decision = ModelRouter.route_request(
        models=model_catalog,
        input_tokens=1000,
        estimated_output_tokens=500,
        min_quality_score=8.0,
    )
    assert decision.selected_model_id == "gpt-4o-mini"
    assert "lowest-cost eligible model" in decision.selection_reason
    assert decision.cost_savings_pct > 0


def test_routing_rejects_high_latency(model_catalog):
    # Max latency 400ms: only gpt-4o-mini (300ms) and mistral (180ms) qualify.
    # If min_quality is 8.0, only gpt-4o-mini qualifies.
    decision = ModelRouter.route_request(
        models=model_catalog,
        input_tokens=1000,
        estimated_output_tokens=500,
        max_latency_ms=400.0,
        min_quality_score=8.0,
    )
    assert decision.selected_model_id == "gpt-4o-mini"

    # Verify gpt-4o was marked ineligible with latency reason
    gpt4o_eval = next(e for e in decision.candidate_evaluations if e.model_id == "gpt-4o")
    assert not gpt4o_eval.eligible
    assert any("latency" in r.lower() for r in gpt4o_eval.rejection_reasons)


def test_routing_high_stakes_frontier(model_catalog):
    # High stakes: requires quality >= 9.6 -> only Claude 3.5 Sonnet qualifies!
    decision = ModelRouter.route_request(
        models=model_catalog,
        input_tokens=1000,
        estimated_output_tokens=500,
        min_quality_score=9.6,
    )
    assert decision.selected_model_id == "claude-3-5-sonnet"


def test_routing_impossible_constraints_fallback(model_catalog):
    # Impossible constraints: max_cost = $0.0000001 (impossible for all)
    decision = ModelRouter.route_request(
        models=model_catalog,
        input_tokens=1000,
        estimated_output_tokens=500,
        max_cost_usd=0.0000001,
    )
    # Should gracefully select fallback rather than crash
    assert decision.selected_model_id is not None
    assert "Fallback" in decision.selection_reason
