"""
Regex-Based Security Scanner for AI Control Center.
Detects PII (Emails, Phones, SSNs, IDs, Credit Cards), API Keys,
and Prompt Injection attempts using robust regular expressions and heuristic scoring.
"""

import re
from typing import List, Tuple, Dict, Any
from src.models.schemas import SecurityFinding, FindingType, Severity, RiskLevel, RequestStatus
from src.modules.pii_guard.classifier_interface import BaseSecurityScanner, ScanResult


class RegexSecurityScanner(BaseSecurityScanner):
    """
    Production-grade regex heuristic scanner for PII and adversarial prompt injection.
    Designed for high throughput, zero external latency, and complete explainability.
    """

    # --- PII Regular Expressions ---
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    )
    PHONE_PATTERN = re.compile(
        r'(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?',
        re.IGNORECASE
    )
    SSN_PATTERN = re.compile(
        r'\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b'
    )
    GENERIC_ID_PATTERN = re.compile(
        r'\b(?:ID|SSN|TIN|PASSPORT|DL)[:\s#-]+([A-Z0-9]{6,12})\b',
        re.IGNORECASE
    )
    CREDIT_CARD_PATTERN = re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{15,16}\b'
    )
    API_KEY_PATTERNS = [
        (re.compile(r'\bsk[-_][a-zA-Z0-9_\-]{20,64}\b'), "OpenAI / Model Secret Key"),
        (re.compile(r'\bsk[-_]live[-_][0-9a-zA-Z_\-]{16,48}\b'), "Stripe Live Secret Key"),
        (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), "AWS Access Key ID"),
        (re.compile(r'\bghp_[a-zA-Z0-9]{36}\b'), "GitHub Personal Access Token"),
        (re.compile(r'\b[a-zA-Z0-9_-]*api[_-]?key[a-zA-Z0-9_-]*\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,60})["\']?', re.IGNORECASE), "Generic API Key Parameter"),
    ]

    # --- Prompt Injection & Jailbreak Heuristics ---
    INJECTION_PATTERNS = [
        (
            re.compile(r'\b(ignore|disregard|forget|override|bypass)\s+(all\s+)?(previous|prior|system|above)\s+(instructions|directives|rules|prompts|guardrails)\b', re.IGNORECASE),
            "Direct System Instruction Override Attempt",
            Severity.CRITICAL,
            0.95
        ),
        (
            re.compile(r'\b(system\s+override|system\s+reset|admin\s+mode|root\s+access|developer\s+mode)\b', re.IGNORECASE),
            "Privilege Escalation / Admin Mode Injection",
            Severity.CRITICAL,
            0.90
        ),
        (
            re.compile(r'\b(reveal|print|dump|show|output|leak)\s+(the\s+)?(system\s+prompt|hidden\s+instructions|internal\s+configuration|secret\s+keys?|passwords?|credentials?)\b', re.IGNORECASE),
            "Confidential Directive Exfiltration Attempt",
            Severity.CRITICAL,
            0.88
        ),
        (
            re.compile(r'\b(play\s+a\s+roleplay|you\s+are\s+now|act\s+as)\s+(evilgpt|dan|jailbroken|unrestricted|anarchist)\b', re.IGNORECASE),
            "Persona Hijacking / Adversarial Jailbreak Persona (DAN/EvilGPT)",
            Severity.HIGH,
            0.85
        ),
        (
            re.compile(r'\b(do\s+anything\s+now|jailbreak\s+mode|no\s+ethical\s+restrictions?)\b', re.IGNORECASE),
            "Classic Jailbreak Assertion Phrase",
            Severity.HIGH,
            0.80
        ),
        (
            re.compile(r'<!--.*?-->|```system|\[SYSTEM\]|<\|im_start\|>', re.IGNORECASE),
            "Delimiter Injection / System Role Forgery",
            Severity.MEDIUM,
            0.70
        ),
    ]

    def scan(self, prompt: str) -> ScanResult:
        """Scan prompt for PII, secrets, and prompt injections."""
        if not prompt or not prompt.strip():
            return ScanResult(
                prompt="",
                redacted_prompt="",
                risk_level=RiskLevel.NONE,
                risk_score=0.0,
                recommended_action=RequestStatus.ALLOWED,
            )

        findings: List[SecurityFinding] = []
        explanations: List[str] = []
        max_severity_score = 0.0
        redacted_text = prompt

        # 1. Scan for Emails
        for match in self.EMAIL_PATTERN.finditer(prompt):
            val = match.group(0)
            findings.append(SecurityFinding(
                finding_type=FindingType.PII_EMAIL,
                severity=Severity.LOW,
                matched_pattern=val,
                explanation="Exposes personal or corporate email address",
                action_taken="Masked with [EMAIL_REDACTED]"
            ))
            explanations.append(f"Detected email address '{val}'. Recommended: Redact before model forwarding.")
            max_severity_score = max(max_severity_score, 0.3)
            redacted_text = redacted_text.replace(val, "[EMAIL_REDACTED]")

        # 2. Scan for Phone Numbers
        for match in self.PHONE_PATTERN.finditer(prompt):
            val = match.group(0).strip()
            # Verify phone has at least 7 digits to avoid false positives with standalone numbers
            digits = re.sub(r'\D', '', val)
            if len(digits) >= 7 and len(digits) <= 15:
                findings.append(SecurityFinding(
                    finding_type=FindingType.PII_PHONE,
                    severity=Severity.LOW,
                    matched_pattern=val,
                    explanation="Exposes telephone/mobile number",
                    action_taken="Masked with [PHONE_REDACTED]"
                ))
                explanations.append(f"Detected phone number '{val}'. Recommended: Redact before model forwarding.")
                max_severity_score = max(max_severity_score, 0.3)
                redacted_text = redacted_text.replace(val, "[PHONE_REDACTED]")

        # 3. Scan for SSNs
        for match in self.SSN_PATTERN.finditer(prompt):
            val = match.group(0)
            findings.append(SecurityFinding(
                finding_type=FindingType.PII_ID,
                severity=Severity.HIGH,
                matched_pattern=val,
                explanation="Exposes US Social Security Number pattern",
                action_taken="Masked with [SSN_REDACTED] and flagged"
            ))
            explanations.append(f"Detected sensitive National ID / SSN pattern '{val}'. Highly restricted.")
            max_severity_score = max(max_severity_score, 0.8)
            redacted_text = redacted_text.replace(val, "[SSN_REDACTED]")

        # 4. Scan for Credit Cards
        for match in self.CREDIT_CARD_PATTERN.finditer(prompt):
            val = match.group(0).strip()
            digits = re.sub(r'\D', '', val)
            if len(digits) in (15, 16):
                findings.append(SecurityFinding(
                    finding_type=FindingType.PII_CREDIT_CARD,
                    severity=Severity.HIGH,
                    matched_pattern=f"{digits[:4]}-****-****-{digits[-4:]}",
                    explanation="Exposes Payment Card / PCI-DSS number pattern",
                    action_taken="Masked with [CREDIT_CARD_REDACTED]"
                ))
                explanations.append("Detected Payment Card Account Number. Potential PCI violation.")
                max_severity_score = max(max_severity_score, 0.85)
                redacted_text = redacted_text.replace(val, "[CREDIT_CARD_REDACTED]")

        # 5. Scan for API Keys & Credentials
        for pattern, label in self.API_KEY_PATTERNS:
            for match in pattern.finditer(prompt):
                val = match.group(0)
                findings.append(SecurityFinding(
                    finding_type=FindingType.API_KEY,
                    severity=Severity.CRITICAL,
                    matched_pattern=f"{val[:8]}...{val[-4:]}" if len(val) > 12 else "SECRET_KEY_DETECTED",
                    explanation=f"Detected high-entropy credential ({label})",
                    action_taken="BLOCKED request immediately to prevent credential compromise"
                ))
                explanations.append(f"Critical credential exposure: {label}. Immediate block required.")
                max_severity_score = max(max_severity_score, 0.95)
                redacted_text = redacted_text.replace(val, "[CREDENTIAL_REDACTED]")

        # 6. Scan for Prompt Injections & Jailbreaks
        for pattern, desc, severity, score in self.INJECTION_PATTERNS:
            match = pattern.search(prompt)
            if match:
                val = match.group(0)
                findings.append(SecurityFinding(
                    finding_type=FindingType.PROMPT_INJECTION,
                    severity=severity,
                    matched_pattern=val,
                    explanation=f"Adversarial prompt injection pattern: {desc}",
                    action_taken="Flagged / Blocked according to security policy"
                ))
                explanations.append(f"Suspicious prompt structure: '{val}' ({desc}).")
                max_severity_score = max(max_severity_score, score)

        # Determine overall Risk Level and Recommended Action
        if max_severity_score >= 0.85:
            risk_level = RiskLevel.CRITICAL
            recommended_action = RequestStatus.BLOCKED
        elif max_severity_score >= 0.65:
            risk_level = RiskLevel.HIGH
            recommended_action = RequestStatus.BLOCKED
        elif max_severity_score >= 0.35:
            risk_level = RiskLevel.MEDIUM
            recommended_action = RequestStatus.FLAGGED
        elif max_severity_score > 0.0:
            risk_level = RiskLevel.LOW
            recommended_action = RequestStatus.REDACTED
        else:
            risk_level = RiskLevel.NONE
            recommended_action = RequestStatus.ALLOWED

        if not explanations:
            explanations.append("No sensitive PII, credential leakage, or adversarial injection patterns identified.")

        return ScanResult(
            prompt=prompt,
            redacted_prompt=redacted_text,
            findings=findings,
            risk_level=risk_level,
            risk_score=round(max_severity_score, 2),
            recommended_action=recommended_action,
            explanations=explanations,
            scanner_metadata={
                "scanner_engine": "RegexSecurityScanner v1.2",
                "rules_evaluated": len(self.API_KEY_PATTERNS) + len(self.INJECTION_PATTERNS) + 4,
                "ml_classifier_ready": True
            }
        )
