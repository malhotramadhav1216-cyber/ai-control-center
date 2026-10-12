# AI Control Center — Enterprise AI Governance & Cost-Optimization Platform

🎓 **Applied MBA Capstone Project**  
*A modular, enterprise-grade AI governance, security guardrail, and multi-model cost-routing software prototype.*

---

## 1. Executive Summary & Business Problem

Enterprises integrating generative AI face four critical challenges:

1. **Escalating AI & Token Costs:** Unmanaged traffic blindly queries frontier models (e.g., GPT-4o, Claude 3.5 Sonnet) for lightweight corporate tasks, resulting in severe cloud expenditure inflation.
2. **Privacy, Compliance & Data Leakage Risks:** Employees risk leaking Personally Identifiable Information (PII), confidential client data, and API credentials into third-party AI APIs. In addition, adversarial prompt injection attacks threaten internal policies.
3. **Absence of Usage Visibility:** Financial leaders and CIOs cannot attribute AI expenses by department, application, or business task.
4. **Governance & Audit Trail Bottlenecks:** Lack of programmatic API gateway enforcement to automatically allow, redact, flag, or block non-compliant prompts before external transmission.

**AI Control Center** solves these problems by providing an integrated enterprise software platform featuring **Token Cost Analytics**, **PII & Data Leak Guard**, and **Intelligent Model Routing**.

---

## 2. Core Functional Modules

### Module A — Token Cost Analytics
- **Live Consumption Tracking:** Real-time token counting (input/output) and exact cost calculation based on configurable provider rate cards.
- **Multi-Dimensional Attribution:** Breakdown of spending by business unit (Engineering, Finance, Marketing, HR, Customer Support), LLM model profile, and application.
- **Budget Threshold Alerts:** Early-warning indicators for department budgets (Safe, Warning, Critical) with daily run-rate burn metrics.
- **Predictive Run-Rate Forecasting:** 14-day and 30-day time-series forecasting blending 7-day moving averages and linear trend projection.
- **Data Export:** Instant CSV export of all filtered historical consumption records.

### Module B — PII & Data Leak Guard
- **Automated PII Detection:** Heuristic pattern scanning for email addresses (RFC 5322), international phone numbers (E.164), US Social Security Numbers (`XXX-XX-XXXX`), credit card patterns, and API credentials (OpenAI, Stripe, AWS).
- **Adversarial Prompt Injection Defense:** Detects direct system prompt overrides, confidential directive exfiltration, and persona hijacking jailbreaks (e.g., DAN, EvilGPT).
- **In-Flight Data Masking:** Dynamic prompt redaction (e.g. replacing sensitive tokens with `[EMAIL_REDACTED]`, `[SSN_REDACTED]`) before model forwarding.
- **Defense-in-Depth Architecture:** Built on an extensible `BaseSecurityScanner` interface ready for fine-tuned transformer classifiers (e.g. Meta Llama-Guard, RoBERTa).
- **Limitations Disclosure:** Transparently discloses that pattern-matching heuristics cannot guarantee 100% defense against zero-day paraphrasing.

### Module C — Intelligent Model Routing
- **Multi-Objective Rule Optimization:** Evaluates active model profiles across Cost, Latency, and Quality SLAs.
- **Lowest-Cost Compliant Recommendation:** Automatically routes each request to the lowest-cost model that satisfies quality and latency constraints.
- **Transparent Rejection Rationales:** Detailed qualification and disqualification audit matrix for every evaluated candidate model.
- **Strategic ROI Quantification:** Compares optimized routed expenditure against unmanaged frontier model baselines (e.g. GPT-4o).
- **Provider Abstraction:** Implements `BaseLLMProvider` decoupling business logic from external API vendors.

---

## 3. Integrated AI Gateway Workflow

The platform connects all three modules into an automated pipeline:

```
[Employee / Enterprise App Prompt]
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                 AI CONTROL CENTER GATEWAY                   │
│                                                             │
│  1. PII & Prompt Risk Scan (RegexSecurityScanner)           │
│     - Inspects for PII, API keys, and injection attempts    │
│                                                             │
│  2. Policy Enforcement (GovernancePolicy)                   │
│     ├── If Injection or High Risk  ──▶ Blocked ($0 cost)    │
│     └── If PII                     ──▶ Masked / Redacted    │
│                                                             │
│  3. Intelligent Model Router (ModelRouter)                  │
│     - Evaluates active models against Quality & Latency SLA │
│     - Recommends lowest-cost eligible provider              │
│     - (Blocked requests bypass routing completely)          │
│                                                             │
│  4. Provider Adapter (SimulatedGatewayProvider)             │
│     - Formats prompt & executes completion                  │
│                                                             │
│  5. Tamper-Evident Audit Logging (Repository)               │
│     - Computes SHA-256 prompt hash (zero raw prompt storage)│
│     - Records exact tokens, cost, latency, and findings     │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
[Executive Dashboards & Predictive Cost Analytics]
```

---

## 4. Technology Stack

- **Frontend & UI:** Streamlit (v1.50) with custom enterprise SaaS CSS design system.
- **Backend Core:** Python 3.9+ with clean modular package architecture.
- **Data Analytics:** Pandas & NumPy for multi-dimensional aggregations and run-rate projections.
- **Data Visualizations:** Plotly Graph Objects & Plotly Express.
- **Data Validation & Schemas:** Pydantic v2.
- **Database:** SQLite 3 with parameterized queries, foreign key enforcement, and cloud-DB migration abstraction.
- **Automated Testing:** Pytest unit and integration test suite.
- **Hosting Targets:** Local macOS / Linux and Streamlit Community Cloud.

---

## 5. Local Setup & Execution (macOS Guide)

### Prerequisites
- macOS terminal (zsh or bash)
- Python 3.9 or higher

### Step-by-Step Installation

1. **Clone or navigate to the repository:**
   ```bash
   cd /path/to/ai-control-center
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install project dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize and seed demonstration data:**
   ```bash
   python -m src.database.seed_data
   ```

5. **Run the automated test suite:**
   ```bash
   pytest tests/ -v
   ```
   *(All 23 automated tests should pass with 0 failures).*

6. **Launch the web application:**
   ```bash
   streamlit run app.py
   ```
   The application will automatically open in your default browser at `http://localhost:8501`.

---

## 6. GitHub Repository & Online Deployment Guide

### Publishing to GitHub
1. Initialize git and commit:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit of AI Control Center prototype"
   ```
2. Create a new repository on GitHub (e.g., `ai-control-center`).
3. Push to GitHub:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<your-username>/ai-control-center.git
   git push -u origin main
   ```

### Deploying to Streamlit Community Cloud
1. Sign in to [share.streamlit.io](https://share.streamlit.io/) with your GitHub account.
2. Click **New app**.
3. Select your repository: `<your-username>/ai-control-center`.
4. Branch: `main`.
5. Main file path: `app.py`.
6. Click **Deploy**.

> **Important Cloud Storage Note:** Streamlit Community Cloud runs on ephemeral Linux containers. Local SQLite database modifications reset upon container reboots. For production deployments requiring persistent data retention, configure a managed cloud database (e.g. Supabase or PostgreSQL) by setting the `DATABASE_URL` environment variable in Streamlit Cloud Secrets.

---

## 7. Prototype Disclosures & Transparency Matrix

| Dimension | Implementation Status | Technical Details |
| :--- | :--- | :--- |
| **Integrated AI Gateway** | **100% Functional** | Complete lifecycle from request ingestion to policy enforcement, routing, and logging. |
| **Token Cost Calculator** | **100% Functional** | Exact mathematical calculation per 1M tokens based on configurable model rate cards. |
| **PII & Injection Guard** | **100% Functional** | Regex scanning for emails, phones, SSNs, credit cards, API keys, and injection overrides. |
| **Intelligent Model Router**| **100% Functional** | Rule-based multi-objective optimization across Cost, Latency, and Quality constraints. |
| **Relational Database** | **100% Functional** | Normalized SQLite schema with parameterized queries and data access repository. |
| **LLM Provider Calls** | **Simulated Prototype** | Uses `SimulatedGatewayProvider` to eliminate paid API dependencies during academic grading. |
| **Model Catalog Prices** | **Illustrative Rates** | Pre-populated with representative market rates; fully editable via the Settings page. |
| **Sample Dataset** | **Illustrative Prototype** | 320+ realistic fictional historical records for Finance, Eng, Mktg, HR, and Support. |
| **Prompt Audit Storage** | **Privacy Compliant** | Stores cryptographic SHA-256 hashes and task summaries; raw prompts are not logged. |

---

## 8. Academic Project Information

- **Project Title:** AI Control Center — Enterprise AI Governance & Cost-Optimization Platform
- **Program:** Master of Business Administration (MBA)
- **Specialization:** Applied AI Management & Enterprise Technology Governance
