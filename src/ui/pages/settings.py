"""
Settings and Configuration Page for AI Control Center.
Enables configuration of model pricing profiles, department budgets,
governance enforcement rules, privacy settings, and demonstration data controls.
"""

import streamlit as st
import pandas as pd

from src.database.repository import Repository
from src.database.seed_data import seed_database
from src.models.schemas import GovernancePolicy, PolicyAction
from src.ui.components import render_prototype_banner


def render_settings_page():
    st.markdown('<div class="main-title">Settings & Enterprise Configuration</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Configure model pricing catalogues, departmental budgets, governance guardrails, and demo datasets.</div>',
        unsafe_allow_html=True
    )

    render_prototype_banner()

    tab_models, tab_budgets, tab_policy, tab_demo = st.tabs([
        "🤖 Model Pricing & Catalog",
        "🏢 Department Budgets",
        "🛡️ Governance & Privacy Rules",
        "🔄 Demo Data Controls"
    ])

    # -------------------------------------------------------------
    # TAB 1: Model Profiles & Pricing
    # -------------------------------------------------------------
    with tab_models:
        st.markdown("#### Configure AI Model Profiles & Token Rates")
        st.caption(
            "Prices are in USD per 1 Million (1,000,000) tokens. "
            "You can adjust these illustrative values to match updated provider contracts."
        )

        models = Repository.get_model_profiles(active_only=False)
        selected_model_id = st.selectbox(
            "Select Model Profile to Edit:",
            [m.id for m in models],
            format_func=lambda x: next(f"{m.name} ({m.provider})" for m in models if m.id == x)
        )

        curr_model = next(m for m in models if m.id == selected_model_id)

        with st.form("edit_model_form"):
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                cost_in = st.number_input(
                    "Input Price ($ / 1M tokens):",
                    min_value=0.0, max_value=100.0,
                    value=curr_model.cost_per_million_input,
                    step=0.05, format="%.4f"
                )
                cost_out = st.number_input(
                    "Output Price ($ / 1M tokens):",
                    min_value=0.0, max_value=200.0,
                    value=curr_model.cost_per_million_output,
                    step=0.10, format="%.4f"
                )
            with c_m2:
                latency = st.number_input(
                    "Average Latency (ms):",
                    min_value=10.0, max_value=5000.0,
                    value=curr_model.avg_latency_ms,
                    step=10.0
                )
                quality = st.number_input(
                    "Quality Score (1.0 to 10.0):",
                    min_value=1.0, max_value=10.0,
                    value=curr_model.quality_score,
                    step=0.1
                )
                is_active = st.checkbox("Active for Model Routing Engine", value=curr_model.is_active)

            save_model = st.form_submit_button("💾 Save Model Changes", type="primary")
            if save_model:
                Repository.update_model_profile(
                    model_id=selected_model_id,
                    cost_in=cost_in,
                    cost_out=cost_out,
                    latency_ms=latency,
                    quality=quality,
                    is_active=is_active
                )
                st.success(f"Model profile '{curr_model.name}' updated successfully.")
                st.rerun()

    # -------------------------------------------------------------
    # TAB 2: Department Budgets
    # -------------------------------------------------------------
    with tab_budgets:
        st.markdown("#### Department Monthly Budget Allocation")
        st.caption("Adjust monthly spending caps (USD) for each business unit.")

        departments = Repository.get_departments()
        for dept in departments:
            b_col1, b_col2, b_col3 = st.columns([2, 2, 1])
            with b_col1:
                st.markdown(f"**{dept.name}**")
            with b_col2:
                new_budget = st.number_input(
                    f"Monthly Budget ($)",
                    min_value=100.0, max_value=100000.0,
                    value=dept.monthly_budget,
                    step=250.0,
                    key=f"b_{dept.id}"
                )
            with b_col3:
                st.write("")
                st.write("")
                if st.button("Update", key=f"btn_{dept.id}"):
                    Repository.update_department_budget(dept.id, new_budget)
                    st.success(f"Updated {dept.name} budget to ${new_budget:,.2f}")
                    st.rerun()

    # -------------------------------------------------------------
    # TAB 3: Governance & Privacy Rules
    # -------------------------------------------------------------
    with tab_policy:
        st.markdown("#### Enterprise AI Governance Policy Configuration")
        st.caption("Define automated enforcement actions executed by the AI Gateway.")

        curr_policy = Repository.get_governance_policy()

        with st.form("governance_policy_form"):
            pol_c1, pol_c2 = st.columns(2)

            with pol_c1:
                pii_action_val = st.selectbox(
                    "Action on Detected Sensitive PII:",
                    options=["REDACT", "FLAG", "BLOCK", "ALLOW"],
                    index=["REDACT", "FLAG", "BLOCK", "ALLOW"].index(curr_policy.pii_action.value)
                )

                inj_action_val = st.selectbox(
                    "Action on Detected Prompt Injection / Attack:",
                    options=["BLOCK", "FLAG", "ALLOW"],
                    index=["BLOCK", "FLAG", "ALLOW"].index(curr_policy.injection_action.value)
                )

            with pol_c2:
                risk_thresh = st.slider(
                    "High-Risk Automatic Block Threshold:",
                    min_value=0.40, max_value=0.95,
                    value=curr_policy.high_risk_threshold,
                    step=0.05
                )

                store_previews = st.checkbox(
                    "Store Sanitized Prompt Previews in Audit Logs (Privacy Toggle)",
                    value=curr_policy.store_prompt_previews,
                    help="When disabled, records only persist SHA-256 hashes and metadata for strict GDPR/HIPAA compliance."
                )

            save_policy = st.form_submit_button("💾 Save Governance Rules", type="primary")
            if save_policy:
                new_pol = GovernancePolicy(
                    id="default_policy",
                    name="Enterprise Standard AI Policy",
                    pii_action=PolicyAction(pii_action_val),
                    injection_action=PolicyAction(inj_action_val),
                    high_risk_threshold=risk_thresh,
                    store_prompt_previews=store_previews
                )
                Repository.update_governance_policy(new_pol)
                st.success("Governance policy updated successfully.")
                st.rerun()

    # -------------------------------------------------------------
    # TAB 4: Demonstration Data Controls
    # -------------------------------------------------------------
    with tab_demo:
        st.markdown("#### Demonstration Data Management")
        st.markdown(
            "Manage fictional prototype records for Finance, Engineering, Marketing, HR, and Support."
        )

        d_col1, d_col2 = st.columns(2)

        with d_col1:
            st.markdown("##### 🔄 Reset Demonstration Dataset")
            st.caption("Clears all existing logs and repopulates ~320 realistic historical transactions across 30 days.")
            if st.button("Reset & Reseed Prototype Data", type="primary"):
                with st.spinner("Reseeding database..."):
                    seed_database(num_requests=320, days_back=30)
                st.success("Database successfully reset and reseeded with clean demonstration records.")
                st.rerun()

        with d_col2:
            st.markdown("##### ➕ Simulate Fresh Batch of Requests")
            st.caption("Generates 25 new incoming enterprise requests right now to simulate live traffic.")
            if st.button("Generate 25 New Requests"):
                from src.database.seed_data import seed_database
                # Add batch without wiping
                with st.spinner("Simulating incoming enterprise requests..."):
                    import random
                    from src.modules.workflow.gateway import AIGateway
                    from src.models.schemas import GatewayInput
                    from src.database.seed_data import SAMPLE_PROMPT_SCENARIOS, DEPARTMENTS, APPLICATIONS

                    gw = AIGateway()
                    for _ in range(25):
                        dept = random.choice(DEPARTMENTS)
                        app_pair = random.choice(APPLICATIONS[dept["id"]])
                        scenario = random.choice(SAMPLE_PROMPT_SCENARIOS)

                        inp = GatewayInput(
                            prompt=scenario["prompt"],
                            department_id=dept["id"],
                            application_name=app_pair[0],
                            user_identifier=f"emp_{dept['name'][:3].lower()}_{random.randint(100, 199)}",
                            task_type=app_pair[1],
                            min_quality_score=random.choice([7.5, 8.0, 8.5]),
                        )
                        gw.process_request(inp, persist_to_db=True)

                st.success("25 new requests processed through the gateway and logged.")
                st.rerun()
