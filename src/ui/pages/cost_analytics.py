"""
Token Cost Analytics Page (Module A) for AI Control Center.
Comprehensive cost transparency, token consumption tracking,
department & model breakdowns, filtering, CSV export, and spend forecasting.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from src.database.repository import Repository
from src.modules.cost_analytics.forecaster import CostForecaster
from src.ui.components import render_prototype_banner, render_metric_card


def render_cost_analytics_page():
    st.markdown('<div class="main-title">Module A — Token Cost Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Granular visibility into AI token consumption, multi-dimensional expenditure, and budget forecasting.</div>',
        unsafe_allow_html=True
    )

    render_prototype_banner()

    # Load data
    departments = Repository.get_departments()
    dept_map = {d.id: d.name for d in departments}
    dept_dicts = [{"id": d.id, "name": d.name, "monthly_budget": d.monthly_budget} for d in departments]
    models = Repository.get_model_profiles(active_only=False)
    model_map = {m.id: m.name for m in models}

    # -------------------------------------------------------------
    # Interactive Filter Toolbar
    # -------------------------------------------------------------
    st.markdown("#### 🔍 Filter Request History & Analytics")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)

    with f_col1:
        selected_dept = st.selectbox(
            "Department Filter:",
            ["All"] + list(dept_map.keys()),
            format_func=lambda x: "All Departments" if x == "All" else dept_map.get(x, x)
        )

    with f_col2:
        selected_model = st.selectbox(
            "Model Filter:",
            ["All"] + list(model_map.keys()),
            format_func=lambda x: "All Models" if x == "All" else model_map.get(x, x)
        )

    with f_col3:
        task_types = ["All", "Code Generation", "Document Summary", "Customer Support", "Data Analysis", "General QA"]
        selected_task = st.selectbox("Task Category:", task_types)

    with f_col4:
        status_options = ["All", "ALLOWED", "REDACTED", "FLAGGED", "BLOCKED"]
        selected_status = st.selectbox("Request Status:", status_options)

    # Fetch filtered requests
    raw_reqs = Repository.get_requests(
        department_id=selected_dept,
        model_id=selected_model,
        task_type=selected_task,
        status=selected_status,
        limit=2000
    )
    df = pd.DataFrame(raw_reqs) if raw_reqs else pd.DataFrame()

    if df.empty:
        st.info("No records match the selected filter criteria.")
        return

    # -------------------------------------------------------------
    # Cost KPI Cards
    # -------------------------------------------------------------
    total_cost = df["estimated_cost_usd"].sum()
    total_in_tokens = df["estimated_input_tokens"].sum()
    total_out_tokens = df["estimated_output_tokens"].sum()
    total_tokens = total_in_tokens + total_out_tokens
    avg_cost_per_req = df["estimated_cost_usd"].mean()

    # Identify highest cost team and model
    top_dept_name = df.groupby("department_name")["estimated_cost_usd"].sum().idxmax() if not df.empty else "N/A"
    top_model_name = df.dropna(subset=["model_name"]).groupby("model_name")["estimated_cost_usd"].sum().idxmax() if not df.dropna(subset=["model_name"]).empty else "N/A"

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_metric_card("Total Filtered Spend", f"${total_cost:,.2f}", f"{len(df):,} requests")
    with kpi2:
        render_metric_card("Total Tokens", f"{total_tokens / 1_000_000:.2f}M", f"{total_in_tokens/1e6:.2f}M in / {total_out_tokens/1e6:.2f}M out")
    with kpi3:
        render_metric_card("Avg Cost / Request", f"${avg_cost_per_req:.4f}", "Mean transaction cost")
    with kpi4:
        render_metric_card("Highest Cost Dept", str(top_dept_name), "Largest resource consumer", delta="Top Team", delta_type="warning")
    with kpi5:
        render_metric_card("Highest Cost Model", str(top_model_name), "Dominant cost driver", delta="Top Driver", delta_type="warning")

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Multi-Dimensional Expenditure Visualizations
    # -------------------------------------------------------------
    st.markdown("### 📊 Expenditure by Department, Model, and Application")
    tab1, tab2, tab3 = st.tabs(["🏢 By Department", "🤖 By Model Profile", "📱 By Application"])

    with tab1:
        c_dept1, c_dept2 = st.columns([1, 1])
        with c_dept1:
            dept_breakdown = df.groupby("department_name").agg(
                cost=("estimated_cost_usd", "sum"),
                requests=("id", "count"),
                tokens=("total_tokens", "sum")
            ).reset_index().sort_values("cost", ascending=False)

            fig_d = px.bar(
                dept_breakdown,
                x="department_name",
                y="cost",
                title="Total AI Expenditure by Department ($ USD)",
                labels={"department_name": "Department", "cost": "Cost ($ USD)"},
                color="cost",
                color_continuous_scale="Teal"
            )
            fig_d.update_layout(template="plotly_white", coloraxis_showscale=False, height=320)
            st.plotly_chart(fig_d, use_container_width=True)

        with c_dept2:
            st.markdown("##### Department Summary Table")
            st.dataframe(
                dept_breakdown.style.format({
                    "cost": "${:,.2f}",
                    "requests": "{:,}",
                    "tokens": "{:,}"
                }),
                use_container_width=True,
                hide_index=True
            )

    with tab2:
        c_mod1, c_mod2 = st.columns([1, 1])
        with c_mod1:
            valid_model_df = df.dropna(subset=["model_name"])
            model_breakdown = valid_model_df.groupby("model_name").agg(
                cost=("estimated_cost_usd", "sum"),
                in_tokens=("estimated_input_tokens", "sum"),
                out_tokens=("estimated_output_tokens", "sum"),
                req_count=("id", "count")
            ).reset_index().sort_values("cost", ascending=False)

            fig_m = px.pie(
                model_breakdown,
                names="model_name",
                values="cost",
                title="Share of AI Expenditure by Model Profile",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_m.update_layout(height=320)
            st.plotly_chart(fig_m, use_container_width=True)

        with c_mod2:
            st.markdown("##### Model Profile Consumption Table")
            st.dataframe(
                model_breakdown.style.format({
                    "cost": "${:,.2f}",
                    "in_tokens": "{:,}",
                    "out_tokens": "{:,}",
                    "req_count": "{:,}"
                }),
                use_container_width=True,
                hide_index=True
            )

    with tab3:
        app_breakdown = df.groupby(["application_name", "department_name"]).agg(
            cost=("estimated_cost_usd", "sum"),
            requests=("id", "count"),
            tokens=("total_tokens", "sum")
        ).reset_index().sort_values("cost", ascending=False)

        fig_app = px.bar(
            app_breakdown,
            x="application_name",
            y="cost",
            color="department_name",
            title="AI Consumption by Enterprise Application",
            labels={"application_name": "Application", "cost": "Cost ($ USD)", "department_name": "Department"},
        )
        fig_app.update_layout(template="plotly_white", height=320)
        st.plotly_chart(fig_app, use_container_width=True)

    # -------------------------------------------------------------
    # Daily & Monthly Spending Trends + Forecasting
    # -------------------------------------------------------------
    st.markdown("### 📈 Daily Spending Trends & Expenditure Forecasting")

    df["date"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d")
    daily_spend = df.groupby("date")["estimated_cost_usd"].sum().reset_index()
    daily_spend.columns = ["date", "cost_usd"]

    forecast_res = CostForecaster.generate_spend_forecast(daily_spend, forecast_days=14)

    col_fc1, col_fc2 = st.columns([3, 1])

    with col_fc1:
        fig_fc = go.Figure()
        # Historical
        fig_fc.add_trace(go.Scatter(
            x=daily_spend["date"],
            y=daily_spend["cost_usd"],
            name="Actual Daily Spend ($)",
            mode="lines+markers",
            line=dict(color="#2563eb", width=2)
        ))
        # Forecast
        if forecast_res["forecast"]:
            f_df = pd.DataFrame(forecast_res["forecast"])
            fig_fc.add_trace(go.Scatter(
                x=f_df["date"],
                y=f_df["forecast_cost_usd"],
                name="Projected Forecast (Run-rate)",
                mode="lines",
                line=dict(color="#10b981", width=2.5, dash="dash")
            ))
            fig_fc.add_trace(go.Scatter(
                x=f_df["date"],
                y=f_df["upper_bound_usd"],
                name="Upper Bound (+18%)",
                mode="lines",
                line=dict(width=0),
                showlegend=False
            ))
            fig_fc.add_trace(go.Scatter(
                x=f_df["date"],
                y=f_df["lower_bound_usd"],
                name="Lower Bound (-18%)",
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(16, 185, 129, 0.15)",
                showlegend=False
            ))

        fig_fc.update_layout(
            title="14-Day Forward Expenditure Forecast (Linear + Moving Average Blend)",
            xaxis_title="Date",
            yaxis_title="Estimated Daily Cost ($ USD)",
            template="plotly_white",
            height=340,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_fc, use_container_width=True)

    with col_fc2:
        st.markdown("##### Forecast Metrics")
        st.metric("Trend Direction", forecast_res["trend"])
        st.metric("Avg Daily Run-rate", f"${forecast_res['avg_daily_spend']:.2f}/day")
        st.metric("14-Day Projected Spend", f"${forecast_res['projected_period_spend']:.2f}")

    # -------------------------------------------------------------
    # Department Budget Thresholds & Warnings
    # -------------------------------------------------------------
    st.markdown("### ⚠️ Department Budget Threshold Alerts")
    all_reqs = Repository.get_requests(limit=3000)
    all_df = pd.DataFrame(all_reqs) if all_reqs else pd.DataFrame()
    budget_eval = CostForecaster.calculate_department_budgets(all_df, dept_dicts)

    for b in budget_eval:
        status_color = "green" if b["status"] == "HEALTHY" else ("orange" if b["status"] == "WARNING" else "red")
        b_c1, b_c2, b_c3 = st.columns([2, 3, 1])
        with b_c1:
            st.markdown(f"**{b['department_name']}**")
            st.caption(f"Budget: ${b['budget']:,.2f} | Current Spend: ${b['current_spend']:,.2f}")
        with b_c2:
            progress_val = min(1.0, max(0.0, b["utilization_pct"] / 100.0))
            st.progress(progress_val)
            st.caption(f"Utilization: {b['utilization_pct']}% | Projected Month-End: ${b['projected_month_end']:,.2f} ({b['projected_utilization_pct']}%)")
        with b_c3:
            if b["status"] == "CRITICAL":
                st.error("🚨 CRITICAL (>90%)")
            elif b["status"] == "WARNING":
                st.warning("⚠️ WARNING (>70%)")
            else:
                st.success("✅ HEALTHY")

    # -------------------------------------------------------------
    # CSV Data Export
    # -------------------------------------------------------------
    st.markdown("### 📥 Export Filtered Token & Cost Records")
    export_df = df[[
        "id", "timestamp", "department_name", "application_name", "task_type",
        "request_status", "model_name", "estimated_input_tokens",
        "estimated_output_tokens", "total_tokens", "estimated_cost_usd", "recorded_action"
    ]].copy()

    csv_data = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered Cost Data (CSV)",
        data=csv_data,
        file_name=f"ai_cost_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        type="primary"
    )
