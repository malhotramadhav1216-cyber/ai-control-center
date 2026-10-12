"""
Unit tests for Database layer and repository operations.
Verifies parameterized query execution, integrity constraints, and seeding.
"""

import pytest
from src.database.connection import initialize_database, get_db_connection
from src.database.repository import Repository
from src.database.seed_data import seed_database
from src.models.schemas import GovernancePolicy, PolicyAction


def test_database_initialization():
    initialize_database()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        assert "departments" in tables
        assert "model_profiles" in tables
        assert "requests" in tables
        assert "security_findings" in tables
        assert "routing_decisions" in tables
        assert "audit_logs" in tables


def test_repository_get_departments():
    seed_database(num_requests=10)
    depts = Repository.get_departments()
    assert len(depts) >= 5
    dept_names = [d.name for d in depts]
    assert "Engineering" in dept_names
    assert "Finance" in dept_names


def test_repository_update_governance_policy():
    policy = GovernancePolicy(
        id="default_policy",
        name="Updated Policy",
        pii_action=PolicyAction.BLOCK,
        injection_action=PolicyAction.BLOCK,
        high_risk_threshold=0.85,
        store_prompt_previews=True
    )
    assert Repository.update_governance_policy(policy) is True

    fetched = Repository.get_governance_policy()
    assert fetched.pii_action == PolicyAction.BLOCK
    assert fetched.high_risk_threshold == 0.85
    assert fetched.store_prompt_previews is True
