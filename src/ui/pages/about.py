"""
About the Prototype Page for AI Control Center.
Presents the MBA project context, business problem statement,
architecture diagrams, transparent prototype disclosures, and future roadmap.
"""

import streamlit as st
from src.ui.components import render_prototype_banner


def render_about_page():
    st.markdown('<div class="main-title">About AI Control Center</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Enterprise AI Governance & Cost-Optimization Platform — MBA Applied Capstone Project</div>',
        unsafe_allow_html=True
    )

    render_prototype_banner()

    # -------------------------------------------------------------
    # Executive Summary & Business Problem
    # -------------------------------------------------------------
    st.markdown("### 🎯 Executive Context & The Enterprise AI Challenge")
    st.markdown(
        """
        As global enterprises accelerate the rollout of generative AI capabilities across engineering,
        customer operations, finance, and human resources, Chief Information Officers (CIOs) and Chief
        Financial Officers (CFOs) face four acute managerial bottlenecks:
        """
    )

    b1, b2 = st.columns(2)
    with b1:
        st.markdown(
            """
            1. **Uncontrolled Token Consumption & Escalating Costs:**
               Development teams and business units frequently default to frontier flagship models (e.g., GPT-4o, Claude 3.5 Sonnet)
               even for lightweight classification, summarization, or repetitive customer support tasks. Unmanaged token
               consumption leads to unpredictable quarterly billing spikes.
            2. **Privacy, Security & Data Leakage Risks:**
               Employees inadvertently paste customer records, non-public financial summaries, Social Security numbers,
               or internal credentials into prompts. Adversarial prompts and jailbreak phrases can bypass safety controls.
            """
        )
    with b2:
        st.markdown(
            """
            3. **Lack of Centralized Consumption Visibility:**
               Organizations suffer from siloed AI adoption. Financial controllers lack granular attribution showing
               which business unit, application, or employee generated expenses, leading to chargeback disputes.
            4. **Absence of Uniform Governance & Audit Trails:**
               Enterprises lack programmatic policy enforcement at the API gateway layer. Without standardized audit
               logs, compliance officers cannot satisfy emerging AI regulatory frameworks (e.g., EU AI Act, NIST AI RMF).
            """
        )

    st.markdown("---")

    # -------------------------------------------------------------
    # Transparent Implementation Matrix
    # -------------------------------------------------------------
    st.markdown("### 🔍 Transparent Prototype Status Matrix")
    st.markdown(
        "In accordance with rigorous academic and engineering standards, this platform clearly distinguishes "
        "between functional software logic, illustrative simulation, and future production roadmap:"
    )

    col_w, col_s, col_f = st.columns(3)

    with col_w:
        st.markdown("#### ✅ What is Fully Functional")
        st.markdown(
            """
            - **End-to-End AI Gateway Pipeline:** Centralized request ingestion, PII scanning, policy enforcement, model routing, and persistent logging.
            - **Token Cost Analytics Engine:** Heuristic token estimation, multi-dimensional aggregation (by dept, model, application), and 14/30-day run-rate forecasting.
            - **PII & Injection Guard:** Regex pattern engine detecting emails, phone numbers, SSNs, credit cards, API keys, and adversarial prompt injections.
            - **Intelligent Model Router:** Multi-objective rule-based optimizer evaluating Quality, Latency, and Cost to recommend the lowest-cost compliant model with rejection rationales.
            - **Relational Persistence:** Normalized SQLite database with parameterized queries and repository abstraction.
            - **Audit Trail & CSV Export:** Compliance logs, drill-down forensics, and data export.
            """
        )

    with col_s:
        st.markdown("#### ⚙️ What is Simulated")
        st.markdown(
            """
            - **LLM Provider API Responses:** To ensure zero paid cloud API dependencies, responses are returned by `SimulatedGatewayProvider` with synthetic metadata.
            - **Illustrative Model Pricing:** Catalog token prices are based on public enterprise rate cards, marked as illustrative and user-editable.
            - **Historical Demonstration Dataset:** 320+ realistic historical transactions spread across 30 days for Finance, Engineering, Marketing, HR, and Support.
            - **Prompt Privacy Previews:** Raw confidential prompts are not stored; synthetic previews and SHA-256 hashes are used.
            """
        )

    with col_f:
        st.markdown("#### 🚀 Future Enterprise Roadmap")
        st.markdown(
            """
            - **Live Provider SDKs:** Connecting official OpenAI, Anthropic Claude, and Google Vertex AI provider adapters using enterprise API keys.
            - **Fine-Tuned ML Guardrails:** Upgrading the regex scanner interface to Meta Llama-Guard or Microsoft Presidio transformer models.
            - **Cloud Managed Database:** Swapping the SQLite repository layer for managed PostgreSQL, AWS RDS, or Supabase.
            - **Enterprise Single Sign-On (SSO):** SAML 2.0 / Okta OAuth2 authentication with role-based access control (RBAC).
            """
        )

    st.markdown("---")

    # -------------------------------------------------------------
    # Architecture Overview
    # -------------------------------------------------------------
    st.markdown("### 🏛️ System Architecture & Integrated Workflow")

    st.markdown(
        """
        ```
        [Employee / Enterprise Application]
                       │ (Submits Prompt)
                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                 AI CONTROL CENTER GATEWAY                   │
        │                                                             │
        │  1. PII & Risk Inspection (RegexSecurityScanner)            │
        │     - Scans for Email, Phone, SSN, Credit Cards, Secrets    │
        │     - Detects System Overrides, Jailbreaks, Injections      │
        │                                                             │
        │  2. Governance Policy Interceptor (GovernancePolicy)        │
        │     ├── [VIOLATION / HIGH RISK] ──▶ Block & Halted ($0 cost)│
        │     └── [ALLOWED / REDACTED]    ──▶ Forward to Router       │
        │                                                             │
        │  3. Intelligent Model Router (ModelRouter)                  │
        │     - Evaluates Catalog (Quality SLA, Latency, Max Cost)    │
        │     - Selects Lowest-Cost Eligible Model                    │
        │     - Computes ROI vs Baseline Frontier Model (GPT-4o)      │
        │                                                             │
        │  4. Provider Adapter (SimulatedGatewayProvider)             │
        │     - Formats payload & executes completion                 │
        │                                                             │
        │  5. Usage & Compliance Audit Logging (Repository)           │
        │     - SHA-256 Prompt Hashing (Zero Raw Prompt Storage)      │
        │     - Records Exact Tokens, Cost, Latency & Audit Trail     │
        └─────────────────────────────────────────────────────────────┘
                       │
                       ▼
        [Executive Dashboards & Predictive Cost Analytics]
        ```
        """
    )

    st.markdown("---")

    # -------------------------------------------------------------
    # Technology Stack
    # -------------------------------------------------------------
    st.markdown("### 🛠️ Technology Stack Specifications")

    tech_df = pd.DataFrame([
        {"Layer": "Frontend Framework", "Technology": "Streamlit (v1.50) + Custom Corporate CSS Design System"},
        {"Layer": "Application Backend", "Technology": "Python 3.9+ with modular service architecture"},
        {"Layer": "Data Processing", "Technology": "Pandas & NumPy for multi-dimensional aggregations and run-rate modeling"},
        {"Layer": "Interactive Visualization", "Technology": "Plotly Graph Objects & Plotly Express"},
        {"Layer": "Data Modeling & Contracts", "Technology": "Pydantic v2 (Strict validation and schemas)"},
        {"Layer": "Database & Storage", "Technology": "SQLite 3 with parameterized queries and foreign key constraints"},
        {"Layer": "Automated Quality Assurance", "Technology": "Pytest (Automated unit and integration test suite)"},
        {"Layer": "Deployment Target", "Technology": "Local macOS / Linux and Streamlit Community Cloud"},
    ])

    st.dataframe(tech_df, use_container_width=True, hide_index=True)
