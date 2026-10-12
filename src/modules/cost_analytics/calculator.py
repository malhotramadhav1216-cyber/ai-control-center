"""
Token and Cost Calculation Engine for AI Control Center.
Provides token estimation heuristics and exact pricing formulas for model profiles.
"""

import math
from typing import Dict, Any, Optional
from src.models.schemas import ModelProfile


class CostCalculator:
    """Calculates token counts and monetary costs across AI models."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count using standard heuristic (~4 characters per token for English/code).
        Provides a realistic estimate without requiring external tokenizer libraries.
        """
        if not text or not text.strip():
            return 0
        cleaned = text.strip()
        # Heuristic: 1 token ~= 3.8 to 4 characters in English and code
        char_count = len(cleaned)
        word_count = len(cleaned.split())
        # Blend character and word counts for robust estimation across code and prose
        estimated = int(math.ceil(max(char_count / 3.8, word_count * 1.3)))
        return max(1, estimated)

    @staticmethod
    def calculate_cost(
        input_tokens: int,
        output_tokens: int,
        model: ModelProfile
    ) -> float:
        """
        Calculate total cost in USD for a request given input/output tokens and model pricing.
        Model prices are per 1 Million (1,000,000) tokens.
        """
        input_cost = (input_tokens / 1_000_000.0) * model.cost_per_million_input
        output_cost = (output_tokens / 1_000_000.0) * model.cost_per_million_output
        return round(input_cost + output_cost, 6)

    @staticmethod
    def compare_model_costs(
        input_tokens: int,
        output_tokens: int,
        models: list[ModelProfile]
    ) -> list[Dict[str, Any]]:
        """Compare estimated costs across a list of models."""
        comparisons = []
        for m in models:
            cost = CostCalculator.calculate_cost(input_tokens, output_tokens, m)
            comparisons.append({
                "model_id": m.id,
                "model_name": m.name,
                "provider": m.provider,
                "cost_usd": cost,
                "quality_score": m.quality_score,
                "avg_latency_ms": m.avg_latency_ms,
            })
        return sorted(comparisons, key=lambda x: x["cost_usd"])
