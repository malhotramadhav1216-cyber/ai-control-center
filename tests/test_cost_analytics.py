"""
Unit tests for Cost Analytics module.
Tests token estimation, cost formula calculations, and budget forecasting.
"""

import pytest
import pandas as pd
from src.modules.cost_analytics.calculator import CostCalculator
from src.modules.cost_analytics.forecaster import CostForecaster
from src.models.schemas import ModelProfile


@pytest.fixture
def sample_model():
    return ModelProfile(
        id="test-model",
        name="Test Model",
        provider="TestAI",
        cost_per_million_input=2.00,
        cost_per_million_output=8.00,
        avg_latency_ms=400.0,
        quality_score=9.0,
    )


def test_token_estimation_empty():
    assert CostCalculator.estimate_tokens("") == 0
    assert CostCalculator.estimate_tokens("   ") == 0


def test_token_estimation_basic():
    text = "Hello world, this is a test prompt for token estimation."
    tokens = CostCalculator.estimate_tokens(text)
    assert 10 <= tokens <= 25


def test_calculate_cost(sample_model):
    # 1,000,000 in ($2) + 1,000,000 out ($8) = $10.00
    cost = CostCalculator.calculate_cost(1_000_000, 1_000_000, sample_model)
    assert cost == 10.0

    # 1,000 in ($0.002) + 500 out ($0.004) = $0.006
    small_cost = CostCalculator.calculate_cost(1_000, 500, sample_model)
    assert small_cost == pytest.approx(0.006, rel=1e-4)


def test_compare_model_costs():
    m1 = ModelProfile(
        id="cheap", name="Cheap", provider="A",
        cost_per_million_input=0.10, cost_per_million_output=0.20,
        avg_latency_ms=200, quality_score=7.5
    )
    m2 = ModelProfile(
        id="expensive", name="Expensive", provider="B",
        cost_per_million_input=5.00, cost_per_million_output=15.00,
        avg_latency_ms=800, quality_score=9.5
    )

    comparisons = CostCalculator.compare_model_costs(1000, 1000, [m2, m1])
    assert len(comparisons) == 2
    # Cheapest should be first
    assert comparisons[0]["model_id"] == "cheap"
    assert comparisons[0]["cost_usd"] < comparisons[1]["cost_usd"]


def test_forecaster_department_budgets():
    departments = [
        {"id": "dept_eng", "name": "Engineering", "monthly_budget": 1000.0},
        {"id": "dept_hr", "name": "HR", "monthly_budget": 500.0},
    ]
    # Synthetic request dataframe
    df = pd.DataFrame([
        {"timestamp": "2026-10-01 10:00:00", "department_id": "dept_eng", "estimated_cost_usd": 850.0},
        {"timestamp": "2026-10-02 10:00:00", "department_id": "dept_hr", "estimated_cost_usd": 50.0},
    ])

    results = CostForecaster.calculate_department_budgets(df, departments)
    assert len(results) == 2
    eng_res = next(r for r in results if r["department_id"] == "dept_eng")
    assert eng_res["current_spend"] == 850.0
    assert eng_res["utilization_pct"] == 85.0
    assert eng_res["status"] in ["WARNING", "CRITICAL"]


def test_spend_forecast_insufficient_data():
    empty_df = pd.DataFrame(columns=["date", "cost_usd"])
    forecast = CostForecaster.generate_spend_forecast(empty_df)
    assert forecast["avg_daily_spend"] == 0.0
