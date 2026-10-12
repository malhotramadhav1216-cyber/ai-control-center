"""
AI Control Center — Enterprise AI Governance & Cost-Optimization Platform.
Main Streamlit application entry point.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI Control Center | Enterprise AI Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom CSS
from src.ui.styles import CUSTOM_CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Ensure Database is Initialized and Seeded
from src.database.connection import initialize_database
from src.database.repository import Repository
from src.database.seed_data import seed_database

try:
    initialize_database()
    models = Repository.get_model_profiles(active_only=False)
    if not models:
        seed_database(num_requests=320, days_back=30)
except Exception as e:
    st.error(f"Database initialization error: {e}")

# Import UI Pages
from src.ui.pages.overview import render_overview_page
from src.ui.pages.cost_analytics import render_cost_analytics_page
from src.ui.pages.pii_guard import render_pii_guard_page
from src.ui.pages.model_routing import render_model_routing_page
from src.ui.pages.audit_logs import render_audit_logs_page
from src.ui.pages.reports_forecasting import render_reports_forecasting_page
from src.ui.pages.settings import render_settings_page
from src.ui.pages.about import render_about_page

# -------------------------------------------------------------
# Sidebar Navigation & System Telemetry
# -------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-title">🛡️ AI Control Center</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">Enterprise AI Governance & Cost Optimization</div>
            <div class="sidebar-badge">MBA APPLIED PROTOTYPE</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    pages = {
        "1. Overview Dashboard": render_overview_page,
        "2. Token Cost Analytics": render_cost_analytics_page,
        "3. PII & Data Leak Guard": render_pii_guard_page,
        "4. Intelligent Model Routing": render_model_routing_page,
        "5. Request History & Audit Logs": render_audit_logs_page,
        "6. Reports & Forecasting": render_reports_forecasting_page,
        "7. Settings & Configuration": render_settings_page,
        "8. About the Prototype": render_about_page,
    }

    selected_page = st.radio(
        "Navigation Menu:",
        list(pages.keys()),
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("##### ⚙️ Gateway Status")

    active_models_count = len(Repository.get_model_profiles(active_only=True))
    st.markdown(f"• **Status:** <span style='color:#10b981; font-weight:600;'>ONLINE</span>", unsafe_allow_html=True)
    st.markdown(f"• **Mode:** Simulation Adapter")
    st.markdown(f"• **Active Models:** {active_models_count}")
    st.markdown(f"• **Database:** SQLite 3 (Normalized)")
    st.markdown(f"• **Build:** v1.2.0 Capstone")

    st.markdown("---")
    st.caption("Developed for MBA Applied AI Project. Illustrative Prototype Data.")

# -------------------------------------------------------------
# Render Active Page
# -------------------------------------------------------------
render_func = pages.get(selected_page, render_overview_page)
render_func()
