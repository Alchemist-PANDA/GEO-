# 🌍 BrandSight GEO — AI-Powered Search Optimization

Generative Engine Optimization (GEO) dashboard that audits how AI search engines perceive your brand and generates remediation content to improve visibility.

## Prerequisites

- Python 3.9+
- An LLM proxy endpoint (configured via environment variables)

## Installation

```bash
# Clone the repository
git clone https://github.com/Alchemist-PANDA/GEO-.git
cd GEO-

# Install dependencies
pip install -e .
# Or without editable mode:
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file in the project root:

```env
# Required: LLM Proxy
ANTHROPIC_BASE_URL=http://localhost:20128/v1
ANTHROPIC_AUTH_TOKEN=your_api_key_here

# Optional: Dashboard credentials (defaults shown)
DASHBOARD_USER=admin
DASHBOARD_PASS=geo123
```

## Running the Dashboard

```bash
streamlit run dashboard.py
```

## CLI Scripts

```bash
# Run a baseline audit
python run_baseline.py --brand "Your Brand" --category "your category" --city "Your City"

# Deploy remediation content
python deploy_remediation.py --file geo_remediation_your_brand.json

# Wait and re-run (development only)
python wait_and_rerun.py --brand "Your Brand" --category "your category" --city "Your City"

# Measure lift
python measure_lift.py
```

## Architecture

```
dashboard.py              — Streamlit UI (entry point)
geo_audit_agent/
  agent.py                — LangGraph agent pipeline
  llm_client.py           — Shared LLM proxy client
  geo_remediation_tools.py — JSON-LD, whitepaper, review tools
```

### Agent Pipeline

1. **query_llm** — Asks an LLM for brand recommendations in a city
2. **check_citation** — Checks if the brand is cited in the response
3. **gap_analyst** — Identifies missing SEO signals (JSON-LD, reviews, authority)
4. **planner** — Creates an action plan using an LLM
5. **remediation_handler** — Executes remediation tools
6. **generate_report** — Outputs the final report

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

*© 2026 Alchemist PANDA — BrandSight GEO v1.2*
