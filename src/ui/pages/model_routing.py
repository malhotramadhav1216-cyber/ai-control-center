"""
Intelligent Model Routing Page (Module C) for AI Control Center.
Multi-objective optimization engine balancing Cost, Latency, and Quality SLA constraints.
Recommends lowest-cost eligible models with transparent rejection rationales.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.database.repository import Repository
from src.modules.cost_analytics.calculator import CostCalculator
from src.modules.model_router.router import ModelRouter
from src.modules.model_router.provider_adapter import SimulatedGatewayProvider
from src.ui.components import render_prototype_banner


def render_model_routing_page():
    st.markdown('<div class="main-title">Module C — Intelligent Model Routing</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Rule-based multi-objective optimization: automatically routes tasks to the lowest-cost model meeting quality & latency SLAs.</div>',
        unsafe_allow_html=True
    )

    render_prototype_banner()

    # Load active model catalog
    models = Repository.get_model_profiles(active_only=True)
    if not models:
        st.error("No active model profiles found in database.")
        return

    # -------------------------------------------------------------
    # Interactive Routing Sandbox
    # -------------------------------------------------------------
    st.markdown("### 🎛️ Routing Sandbox & Constraint Configuration")
    st.markdown(
        "Define operational requirements for a task and observe how the routing engine evaluates every model candidate."
    )

    cfg_col1, cfg_col2, cfg_col3 = st.columns(3)

    with cfg_col1:
        input_tokens = st.number_input("Estimated Input Tokens:", min_value=10, max_value=200000, value=1200, step=100)
        output_tokens = st.number_input("Expected Output Tokens:", min_value=10, max_value=8000, value=600, step=50)

    with cfg_col2:
        max_cost_limit = st.number_input("Max Cost Constraint ($/req, 0 = No Cap):", min_value=0.0, max_value=1.0, value=0.015, step=0.001, format="%.5f")
        max_cost_val = max_cost_limit if max_cost_limit > 0 else None

        max_latency_limit = st.number_input("Max Latency Constraint (ms, 0 = No Cap):", min_value=0.0, max_value=3000.0, value=650.0, step=50.0)
        max_lat_val = max_latency_limit if max_latency_limit > 0 else None

    with cfg_col3:
        min_quality = st.slider("Minimum Quality Score SLA (1-10):", min_value=7.0, max_value=9.8, value=8.2, step=0.1)
        baseline_options = [m.id for m in models]
        benchmark_baseline = st.selectbox("Benchmark Baseline Model (for ROI comparison):", baseline_options, index=baseline_options.index("gpt-4o") if "gpt-4o" in baseline_options else 0)

    if st.button("⚡ Evaluate Candidate Models & Route", type="primary", use_container_width=True):
        decision = ModelRouter.route_request(
            models=models,
            input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            max_cost_usd=max_cost_val,
            max_latency_ms=max_lat_val,
            min_quality_score=min_quality,
            benchmark_baseline_model_id=benchmark_baseline
        )

        st.markdown("---")
        st.markdown("### 🏆 Optimal Model Recommendation")

        w1, w2, w3, w4 = st.columns(4)
        with w1:
            st.metric("Selected Model", decision.selected_model_name)
        with w2:
            chosen_profile = next((m for m in models if m.id == decision.selected_model_id), models[0])
            chosen_cost = CostCalculator.calculate_cost(input_tokens, output_tokens, chosen_profile)
            st.metric("Transaction Cost", f"${chosen_cost:.6f}")
        with w3:
            st.metric("Estimated Latency", f"{decision.estimated_latency_ms:.0f} ms")
        with w4:
            st.metric("Savings vs Baseline", f"{decision.cost_savings_pct:.1f}%", delta="Optimized", delta_type="positive")

        st.success(f"**Selection Rationale:** {decision.selection_reason}")

        # -------------------------------------------------------------
        # Comprehensive Candidate Evaluation Matrix
        # -------------------------------------------------------------
        st.markdown("#### 📋 Candidate Models Evaluation & Rejection Matrix")
        st.markdown("Details on why the winner was chosen and why alternatives were disqualified:")

        matrix_rows = []
        for eval_item in decision.candidate_evaluations:
            status_label = "✅ Eligible" if eval_item.eligible else "❌ Disqualified"
            reasons_str = "; ".join(eval_item.rejection_reasons) if eval_item.rejection_reasons else "All constraints satisfied"
            is_winner = "🌟 SELECTED" if eval_item.model_id == decision.selected_model_id else status_label

            matrix_rows.append({
                "Status": is_winner,
                "Model": eval_item.model_name,
                "Provider": eval_item.provider,
                "Cost ($ USD)": eval_item.cost_usd,
                "Latency (ms)": f"{eval_item.latency_ms:.0f}",
                "Quality Score": f"{eval_item.quality_score:.1f} / 10",
                "Rejection / Qualification Rationale": reasons_str,
            })

        df_matrix = pd.DataFrame(matrix_rows)
        st.dataframe(
            df_matrix.style.format({
                "Cost ($ USD)": "${:,.6f}"
            }),
            use_container_width=True,
            hide_index=True
        )

        # -------------------------------------------------------------
        # Simulated Output Display
        # -------------------------------------------------------------
        provider = SimulatedGatewayProvider()
        sim_resp = provider.execute_request(
            prompt="[Sample Request Payload]",
            model_id=decision.selected_model_id,
            expected_output_tokens=output_tokens
        )
        with st.expander("👁️ View Simulated Response Delivery (Academic Prototype Notice)"):
            st.code(sim_resp.content, language="markdown")
            st.caption(
                "Notice: This is a simulated response generated by the local prototype adapter. "
                "No live AI provider API was queried, ensuring zero billing charges."
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Full Model Catalog Matrix & Cost-Quality Frontier
    # -------------------------------------------------------------
    st.markdown("### 📊 Active Model Catalogue & Pareto Quality-Cost Tradeoffs")

    tab_cat1, tab_cat2 = st.tabs(["📑 Complete Model Profiles Table", "📈 Quality vs Cost Tradeoff Chart"])

    with tab_cat1:
        cat_data = [
            {
                "Model ID": m.id,
                "Model Name": m.name,
                "Provider": m.provider,
                "Cost In ($ / 1M)": m.cost_per_million_input,
                "Cost Out ($ / 1M)": m.cost_per_million_output,
                "Latency (ms)": m.avg_latency_ms,
                "Quality (1-10)": m.quality_score,
                "Max Context": f"{m.max_context_tokens:,} tokens",
                "Description": m.description,
            }
            for m in models
        ]
        df_cat = pd.DataFrame(cat_data)
        st.dataframe(
            df_cat.style.format({
                "Cost In ($ / 1M)": "${:,.3f}",
                "Cost Out ($ / 1M)": "${:,.3f}",
                "Latency (ms)": "{:.0f}",
                "Quality (1-10)": "{:.1f}",
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab_cat2:
        # Scatter Plot: Quality vs Input Cost
        scatter_df = pd.DataFrame([
            {
                "name": m.name,
                "provider": m.provider,
                "quality": m.quality_score,
                "cost_in": m.cost_per_million_input,
                "latency": m.avg_latency_ms
            }
            for m in models
        ])

        fig_scatter = px.scatter(
            scatter_df,
            x="cost_in",
            y="quality",
            text="name",
            size="latency",
            color="provider",
            title="Enterprise Pareto Frontier: Model Quality vs Input Token Cost",
            labels={
                "cost_in": "Input Token Price ($ per 1 Million Tokens)",
                "quality": "Benchmark Quality Score (1-10)",
                "latency": "Latency (ms)",
                "provider": "Provider"
            },
            template="plotly_white"
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(height=420)
        st.plotly_chart(fig_scatter, use_container_width=True)
