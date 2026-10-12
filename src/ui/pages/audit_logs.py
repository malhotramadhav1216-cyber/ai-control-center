"""
Request History and Audit Logs Page for AI Control Center.
Provides tamper-evident compliance logs, granular request history filtering,
privacy-preserving prompt summaries, drill-down investigations, and CSV exports.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.database.repository import Repository
from src.ui.components import render_prototype_banner, format_status_badge, format_risk_badge


def render_audit_logs_page():
    st.markdown('<div class="main-title">Request History & Compliance Audit Logs</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Complete audit trail of all gateway transactions, security interventions, and routing decisions.</div>',
        unsafe_allow_html=True
    )

    render_prototype_banner()

    departments = Repository.get_departments()
    dept_map = {d.id: d.name for d in departments}
    models = Repository.get_model_profiles(active_only=False)
    model_map = {m.id: m.name for m in models}

    # -------------------------------------------------------------
    # Filter Toolbar
    # -------------------------------------------------------------
    st.markdown("#### 🔍 Compliance Audit Filters")
    f1, f2, f3, f4, f5 = st.columns(5)

    with f1:
        sel_dept = st.selectbox(
            "Department:",
            ["All"] + list(dept_map.keys()),
            format_func=lambda x: "All Departments" if x == "All" else dept_map.get(x, x)
        )
    with f2:
        sel_model = st.selectbox(
            "Model:",
            ["All"] + list(model_map.keys()),
            format_func=lambda x: "All Models" if x == "All" else model_map.get(x, x)
        )
    with f3:
        sel_status = st.selectbox("Status:", ["All", "ALLOWED", "REDACTED", "FLAGGED", "BLOCKED"])
    with f4:
        sel_task = st.selectbox("Task Type:", ["All", "Code Generation", "Document Summary", "Customer Support", "Data Analysis", "General QA"])
    with f5:
        search_query = st.text_input("Search ID/User/App:", placeholder="e.g. emp_fin or req_")

    requests = Repository.get_requests(
        department_id=sel_dept,
        model_id=sel_model,
        status=sel_status,
        task_type=sel_task,
        limit=1000
    )

    df_reqs = pd.DataFrame(requests) if requests else pd.DataFrame()

    if not df_reqs.empty and search_query.strip():
        q = search_query.strip().lower()
        df_reqs = df_reqs[
            df_reqs["id"].str.lower().str.contains(q) |
            df_reqs["user_identifier"].str.lower().str.contains(q) |
            df_reqs["application_name"].str.lower().str.contains(q)
        ]

    # Privacy Toggle Notice
    st.caption(
        "🔒 **Enterprise Privacy Mode Active:** In accordance with corporate privacy guidelines, "
        "raw prompt text is not persisted in the database. Records store cryptographic SHA-256 hashes "
        "and sanitized task summaries."
    )

    # -------------------------------------------------------------
    # Requests Table
    # -------------------------------------------------------------
    tab_reqs, tab_audits = st.tabs(["📋 Processed Requests History", "🛡️ Gateway System Audit Trail"])

    with tab_reqs:
        if df_reqs.empty:
            st.info("No request records match the filter criteria.")
        else:
            st.markdown(f"**Displaying {len(df_reqs)} matching request records:**")

            disp_cols = [
                "id", "timestamp", "department_name", "application_name", "user_identifier",
                "task_type", "request_status", "risk_level", "model_name", "total_tokens", "estimated_cost_usd"
            ]
            disp_df = df_reqs[disp_cols].copy()
            disp_df.columns = [
                "Request ID", "Timestamp", "Department", "Application", "Employee ID",
                "Task Category", "Status", "Risk Level", "Model Routed", "Tokens", "Cost ($ USD)"
            ]

            st.dataframe(
                disp_df.style.format({
                    "Cost ($ USD)": "${:,.6f}",
                    "Tokens": "{:,}"
                }),
                use_container_width=True,
                hide_index=True
            )

            # Drill-Down Request Inspector
            st.markdown("#### 🔬 Request Detail Inspector")
            selected_req_id = st.selectbox("Select Request ID for Forensics:", df_reqs["id"].tolist())

            if selected_req_id:
                req_row = df_reqs[df_reqs["id"] == selected_req_id].iloc[0]
                findings = Repository.get_security_findings_for_request(selected_req_id)
                routing = Repository.get_routing_decision_for_request(selected_req_id)

                d1, d2 = st.columns([1, 1])
                with d1:
                    st.markdown("**Request Metadata**")
                    st.write(f"- **ID:** `{req_row['id']}`")
                    st.write(f"- **Timestamp:** {req_row['timestamp']}")
                    st.write(f"- **Department:** {req_row['department_name']} ({req_row['application_name']})")
                    st.write(f"- **Employee User:** {req_row['user_identifier']}")
                    st.write(f"- **Task:** {req_row['task_type']}")
                    st.write(f"- **Status / Risk:** `{req_row['request_status']}` | `{req_row['risk_level']}`")
                    st.write(f"- **Recorded Action:** {req_row['recorded_action']}")
                    st.write(f"- **Prompt SHA-256 Hash:** `{req_row['prompt_hash']}`")
                    st.write(f"- **Sanitized Summary:** {req_row['prompt_summary']}")

                with d2:
                    st.markdown("**Execution & Routing Detail**")
                    if req_row["request_status"] == "BLOCKED":
                        st.error("🚨 This request was BLOCKED by the security gateway before model routing.")
                    else:
                        st.write(f"- **Routed Model:** `{req_row['model_name']}` ({req_row['model_provider']})")
                        st.write(f"- **Input Tokens:** {req_row['estimated_input_tokens']:,}")
                        st.write(f"- **Output Tokens:** {req_row['estimated_output_tokens']:,}")
                        st.write(f"- **Cost ($ USD):** ${req_row['estimated_cost_usd']:.6f}")
                        if routing:
                            st.write(f"- **Estimated Latency:** {routing['estimated_latency_ms']:.0f} ms")
                            st.write(f"- **Cost Savings:** {routing['cost_savings_pct']:.1f}% vs baseline")
                            st.info(f"**Selection Reason:** {routing['selection_reason']}")

                if findings:
                    st.markdown("##### 🚨 Associated Security Findings")
                    f_df = pd.DataFrame(findings)[["finding_type", "severity", "matched_pattern", "explanation", "action_taken"]]
                    f_df.columns = ["Violation Type", "Severity", "Pattern", "Explanation", "Action Taken"]
                    st.dataframe(f_df, use_container_width=True, hide_index=True)

            # CSV Download
            csv_data = df_reqs.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Audit Log (CSV)",
                data=csv_data,
                file_name=f"compliance_audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with tab_audits:
        # System Audit Log
        system_audits = Repository.get_audit_logs(limit=250)
        if system_audits:
            audit_df = pd.DataFrame(system_audits)
            st.dataframe(
                audit_df[["id", "timestamp", "event_type", "actor", "details", "ip_address"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No system audit events recorded.")
