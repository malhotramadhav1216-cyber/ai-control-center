"""
Custom CSS styling and design system for AI Control Center.
Provides clean enterprise SaaS styling, typography, status badges, and cards.
"""

CUSTOM_CSS = """
<style>
/* Main typography and container spacing */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Header customization */
.main-title {
    font-size: 1.85rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.25rem;
    letter-spacing: -0.02em;
}

.sub-title {
    font-size: 0.95rem;
    color: #64748b;
    margin-bottom: 1.5rem;
}

/* Metric KPI Card */
.kpi-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1.15rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.kpi-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
}

.kpi-label {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    margin-bottom: 0.4rem;
}

.kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.2;
}

.kpi-subtext {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 0.35rem;
}

.kpi-delta-positive {
    color: #10b981;
    font-weight: 600;
}

.kpi-delta-negative {
    color: #ef4444;
    font-weight: 600;
}

.kpi-delta-warning {
    color: #f59e0b;
    font-weight: 600;
}

/* Status Badges */
.badge {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    text-align: center;
}

.badge-allowed {
    background-color: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
}

.badge-redacted {
    background-color: #eff6ff;
    color: #1e40af;
    border: 1px solid #bfdbfe;
}

.badge-flagged {
    background-color: #fffbeb;
    color: #92400e;
    border: 1px solid #fde68a;
}

.badge-blocked {
    background-color: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
}

/* Risk Badges */
.badge-risk-none { background-color: #f1f5f9; color: #475569; }
.badge-risk-low { background-color: #ecfdf5; color: #047857; }
.badge-risk-medium { background-color: #fffbeb; color: #b45309; }
.badge-risk-high { background-color: #fff7ed; color: #c2410c; }
.badge-risk-critical { background-color: #fef2f2; color: #b91c1c; font-weight: 700; }

/* Prototype Disclaimer Banner */
.prototype-banner {
    background-color: #f8fafc;
    border-left: 4px solid #3b82f6;
    padding: 0.65rem 1rem;
    border-radius: 0 6px 6px 0;
    margin-bottom: 1.25rem;
    font-size: 0.85rem;
    color: #334155;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.workflow-step-box {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

/* Sidebar Branding */
.sidebar-brand {
    padding: 0.5rem 0 1.25rem 0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 1rem;
}

.sidebar-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.sidebar-badge {
    display: inline-block;
    background-color: #e0e7ff;
    color: #3730a3;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    margin-top: 0.25rem;
}
</style>
"""
