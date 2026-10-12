"""
Security Scanner Architecture & Classifier Interface.
Provides abstract contract allowing regex heuristic scanners
and trained machine-learning models (e.g. HuggingFace, Llama-Guard) to be plugged in interchangeably.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.models.schemas import SecurityFinding, RiskLevel, RequestStatus


class ScanResult(BaseModel):
    """Encapsulates the evaluation output of any security scanner implementation."""
    prompt: str
    redacted_prompt: str
    findings: List[SecurityFinding] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.NONE
    risk_score: float = 0.0  # 0.0 to 1.0
    recommended_action: RequestStatus = RequestStatus.ALLOWED
    explanations: List[str] = Field(default_factory=list)
    scanner_metadata: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = (
        "Notice: Heuristic pattern scanning cannot guarantee 100% detection of all sensitive "
        "data leaks or adversarial prompt variants. Defense-in-depth is required."
    )


class BaseSecurityScanner(ABC):
    """Abstract interface for PII and Prompt Risk analyzers."""

    @abstractmethod
    def scan(self, prompt: str) -> ScanResult:
        """Scan a prompt string and return detailed findings, risk score, and redactions."""
        pass
