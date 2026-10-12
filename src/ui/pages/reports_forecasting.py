"""
Reports & Forecasting Page for AI Control Center.
Provides executive forward-looking cost projections, ROI analysis of model routing,
and department budget exhaustion timelines.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.database.repository import Repository
from src.modules.cost_analytics.forecaster import CostForecaster
from src.ui.components import render_prototype_banner, render_metric_card


def render_reports_forecasting_page():
    st.markdown('<div class="main-title">Reports & Predictive Forecasting</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Strategic forward-looking expenditure models, budget exhaustion risk projections, and ROI quantification.</div>',
        unsafe_allow_html=True
    )

    render_prototype_banner()

    departments = Repository.get_departments()
    dept_dicts = [{"id": d.id, "name": d.name, "monthly_budget": d.monthly_budget} for d in departments]
    requests = Repository.get_requests(limit=3000)
    df = pd.DataFrame(requests) if requests else pd.DataFrame()

    if df.empty:
        st.warning("Insufficient historical data for forecasting.")
        return

    # Calculate actual spending history
    df["date"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d")
    daily_spend = df.groupby("date")["estimated_cost_usd"].sum().reset_index()
    daily_spend.columns = ["date", "cost_usd"]

    # -------------------------------------------------------------
    # Multi-Scenario Predictive Forecasting
    # -------------------------------------------------------------
    st.markdown("### 🔮 Multi-Scenario 30-Day Forward Expenditure Projections")

    base_forecast = CostForecaster.generate_spend_forecast(daily_spend, forecast_days=30)
    avg_daily = base_forecast["avg_daily_spend"]
    recent_daily = base_forecast["recent_daily_spend"]

    sc_col1, sc_col2 = st.columns([3, 1])

    with sc_col1:
        # Build 3 scenarios:
        # 1. Baseline Run-Rate
        # 2. Aggressive GenAI Adoption (+35% query volume growth)
        # 3. Aggressive Model Optimization (-25% cost via router)
        f_dates = [datetime.now() + timedelta(days=i) for i in range(1, 31)]
        f_date_strs = [d.strftime("%Y-%m-%d") for d in f_dates]

        baseline_vals = [recent_daily * (1 + 0.005 * i) for i in range(1, 31)]
        high_growth_vals = [recent_daily * (1 + 0.015 * i) for i in range(1, 31)]
        optimized_vals = [recent_daily * 0.75 * (1 + 0.002 * i) for i in range(1, 31)]

        fig_sc = go.Figure()

        # Historical curve
        fig_sc.add_trace(go.Scatter(
            x=daily_spend["date"],
            y=daily_spend["cost_usd"],
            name="Historical Spend",
            line=dict(color="#64748b", width=1.5)
        ))

        # Baseline
        fig_sc.add_trace(go.Scatter(
            x=f_date_strs,
            y=baseline_vals,
            name="Baseline Run-Rate",
            line=dict(color="#2563eb", width=2.5, dash="dash")
        ))

        # High Adoption
        fig_sc.add_trace(go.Scatter(
            x=f_date_strs,
            y=high_growth_vals,
            name="High Enterprise Adoption (+35%)",
            line=dict(color="#ef4444", width=2, dash="dot")
        ))

        # Optimized
        fig_sc.add_trace(go.Scatter(
            x=f_date_strs,
            y=optimized_vals,
            name="Routing-Optimized (-25%)",
            line=dict(color="#10b981", width=2, dash="dashdot")
        ))

        fig_sc.update_layout(
            title="30-Day Spending Trajectory Under Different Enterprise Scenarios",
            xaxis_title="Date",
            yaxis_title="Projected Daily Cost ($ USD)",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=360,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    with sc_col2:
        st.markdown("##### 30-Day Cost Scenarios")
        st.metric("Baseline Projection", f"${sum(baseline_vals):,.2f}")
        st.metric("High Growth (+35%)", f"${sum(high_growth_vals):,.2f}", delta="+35%", delta_type="negative")
        st.metric("Router Optimized", f"${sum(optimized_vals):,.2f}", delta="-25%", delta_type="positive")

    # -------------------------------------------------------------
    # Strategic ROI Quantification: Intelligent Routing vs Unmanaged LLM Baseline
    # -------------------------------------------------------------
    st.markdown("### 💰 Strategic ROI: Intelligent Routing vs Unmanaged LLMs")
    st.markdown(
        "Quantifies organizational cost savings achieved by automatically routing lower-stakes tasks "
        "to high-efficiency models instead of routing all enterprise traffic blindly to frontier models."
    )

    # Calculate actual spend vs what it would cost if everything went to GPT-4o ($2.50 in / $10 out)
    total_in = df["estimated_input_tokens"].sum()
    total_out = df["estimated_output_tokens"].sum()
    actual_spend = df["estimated_cost_usd"].sum()

    unmanaged_gpt4o_cost = (total_in / 1_000_000 * 2.50) + (total_out / 1_000_000 * 10.00)
    unmanaged_claude_cost = (total_in / 1_000_000 * 3.00) + (total_out / 1_000_000 * 15.00)

    savings_vs_gpt4o = max(0.0, unmanaged_gpt4o_cost - actual_spend)
    savings_pct_gpt4o = (savings_vs_gpt4o / unmanaged_gpt4o_cost * 100.0) if unmanaged_gpt4o_cost > 0 else 0.0

    roi_c1, roi_c2, roi_c3, roi_c4 = st.columns(4)
    with roi_c1:
        render_metric_card("Actual Managed Spend", f"${actual_spend:,.2f}", "With intelligent routing")
    with roi_c2:
        render_metric_card("Unmanaged GPT-4o Spend", f"${unmanaged_gpt4o_cost:,.2f}", "If all queries used GPT-4o")
    with roi_c3:
        render_metric_card("Net Cost Savings", f"${savings_vs_gpt4o:,.2f}", "Preserved enterprise budget", delta=f"{savings_pct_gpt4o:.1f}% Saved", delta_type="positive")
    with roi_c4:
        # Annualized run-rate savings
        annual_savings = savings_vs_gpt4o * 12
        render_metric_card("Annualized Projected ROI", f"${annual_savings:,.2f}", "Projected annual savings", delta="12-Month Run-Rate", delta_type="positive")

    # -------------------------------------------------------------
    # Department Exhaustion Timeline
    # -------------------------------------------------------------
    st.markdown("### ⏳ Department Budget Depletion Timeline")
    budget_eval = CostForecaster.calculate_department_budgets(df, dept_dicts)

    depletion_rows = []
    for b in budget_eval:
        depletion_rows.append({
            "Department": b["department_name"],
            "Monthly Budget": b["budget"],
            "Current Spend": b["current_spend"],
            "Daily Run-Rate": b["daily_run_rate"],
            "Projected Month-End": b["projected_month_end"],
            "Projected Utilization": f"{b['projected_utilization_pct']}%",
            "Days Remaining Before Depletion": f"{b['days_remaining_est']} days" if b['days_remaining_est'] < 999 else "Ample Headroom",
            "Risk Tier": b["status"],
        })

    st.dataframe(
        pd.DataFrame(depletion_rows).style.format({
            "Monthly Budget": "${:,.2f}",
            "Current Spend": "${:,.2f}",
            "Daily Run-Rate": "${:,.2f}/day",
            "Projected Month-End": "${:,.2f}",
        }),
        use_container_width=True,
        hide_index=True
    )

    # Export Executive Report
    st.markdown("### 📄 Export Executive Forecast Summary")
    rep_csv = pd.DataFrame(depletion_rows).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Executive Budget & Forecast Summary (CSV)",
        data=rep_csv,
        file_name=f"executive_ai_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        type="primary"
    )
