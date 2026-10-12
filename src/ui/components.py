"""
Reusable UI components for AI Control Center.
Includes KPI metric cards, status badges, banners, and layout helpers.
"""

import streamlit as st
from typing import Optional


def render_prototype_banner():
    """Renders the required MBA academic prototype disclaimer banner."""
    st.markdown(
        """
        <div class="prototype-banner">
            <div>
                <strong>🎓 MBA Applied Project Prototype:</strong>
                All analytics, token counts, and cost data are <em>Illustrative Prototype Data</em>
                simulating an enterprise deployment. External paid AI APIs are disabled.
            </div>
            <span class="badge badge-allowed" style="white-space: nowrap; margin-left: 1rem;">Simulation Active</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    delta: Optional[str] = None,
    delta_type: str = "positive"
):
    """Render a styled KPI card matching corporate SaaS design."""
    delta_html = ""
    if delta:
        delta_class = f"kpi-delta-{delta_type}"
        delta_html = f"<span class='{delta_class}'>{delta}</span>"

    html = f"""
    <div class="kpi-card">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtext">{delta_html} {subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def format_status_badge(status: str) -> str:
    """Format HTML for status badges (ALLOWED, REDACTED, FLAGGED, BLOCKED)."""
    status_upper = str(status).upper()
    css_class = "badge-allowed"
    if status_upper == "REDACTED":
        css_class = "badge-redacted"
    elif status_upper == "FLAGGED":
        css_class = "badge-flagged"
    elif status_upper == "BLOCKED":
        css_class = "badge-blocked"

    return f"<span class='badge {css_class}'>{status_upper}</span>"


def format_risk_badge(risk: str) -> str:
    """Format HTML for risk level badges."""
    risk_upper = str(risk).upper()
    css_class = "badge-risk-none"
    if risk_upper == "LOW":
        css_class = "badge-risk-low"
    elif risk_upper == "MEDIUM":
        css_class = "badge-risk-medium"
    elif risk_upper == "HIGH":
        css_class = "badge-risk-high"
    elif risk_upper == "CRITICAL":
        css_class = "badge-risk-critical"

    return f"<span class='badge {css_class}'>{risk_upper}</span>"
