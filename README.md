---
title: BrandSight GEO
emoji: 🌍
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.32.0
app_file: geo_upload/dashboard.py
pinned: false
---

# BrandSight GEO — The AI Search Visibility Agent 🌍

**Automating brand discovery and citation lift in Generative Search Engines (ChatGPT, Perplexity, Gemini).**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Orchestration-orange)
![Multi-LLM](https://img.shields.io/badge/Multi--LLM-OpenAI_|_Groq_|_Gemini-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

```text
                                [ BrandSight GEO Architecture ]

    ┌────────────┐      ┌─────────────────┐      ┌─────────────────────────┐
    │ Brand Name │ ───> │ LangGraph Agent │ ───> │ Multi-LLM Citation Audit│
    └────────────┘      └────────┬────────┘      └────────────┬────────────┘
                                 │                            │
                    ┌────────────▼───────────┐      ┌─────────▼──────────┐
                    │  Remediation Engine    │ <─── │ Gap Severity Analys │
                    │ (JSON-LD, Whitepapers) │      └────────────────────┘
                    └────────────┬───────────┘
                                 │
                    ┌────────────▼───────────┐
                    │   GEO Lift Measurement │
                    │ (WordPress Deployment) │
                    └────────────────────────┘
```

---

## 📌 What It Does

In the era of AI-first search, your brand is either a citation or it doesn't exist. Traditional SEO does not work for LLM-based search. **BrandSight GEO** automates the entire audit → remediation → measurement cycle.

```
Brand Input → Multi-LLM Audit → Gap Analysis → Auto-Remediation → Lift Report
```

---

## 🚀 Getting Started

Follow these steps to set up and run the GEO Audit Agent on your local machine.

### 📋 Prerequisites
- **Python 3.10+**
- **pip** (Python package manager)
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/Alchemist-PANDA/GEO-.git
cd GEO-
```

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. API Keys
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Fill in your API keys in the `.env` file. You can use **Groq** for free high-speed inference or **OpenAI/Gemini**.

### 4. Run Locally
```bash
streamlit run dashboard.py
```

The dashboard will open at `http://localhost:8501`

### 5. First Audit
Enter a brand name (e.g., "Burger Hub"), select a category and city, then click **"Run Multi-Model Audit"** to analyze visibility across ChatGPT, Claude, Gemini, and Perplexity.

---

## 🌐 Deployment

### Streamlit Community Cloud
1. Push your code to GitHub
2. Connect your repo at [share.streamlit.io](https://share.streamlit.io)
3. Set `dashboard.py` as the entry file
4. Add secrets in the Streamlit dashboard (Settings → Secrets):
   ```toml
   GOOGLE_API_KEY = "your-key-here"
   ```

### Render / Railway / Fly.io
Use `dashboard.py` as the Streamlit entry file. All platforms support Streamlit apps natively.

**Important**: The app runs in mock mode by default if no API keys are present. This is deployment-safe.

---

## 📸 Screenshots
![Dashboard](docs/screenshots/dashboard_overview.png)
*More screenshots available in the [screenshots directory](docs/screenshots/).*

---

## 🗂️ Project Structure
```text
GEO-/
├── geo_upload/               # Main application and demo runner
│   ├── dashboard.py          # Streamlit UI with authentication
│   ├── run_baseline.py       # Pre-remediation audit script
│   ├── deploy_remediation.py # Remediation content generator
│   ├── measure_lift.py       # Post-audit lift measurement
│   └── *.json                # Audit state and history files
├── geo_audit_agent/          # Core Agent Logic
│   ├── agent.py              # LangGraph state machine (6 nodes)
│   ├── geo_remediation_tools.py # Content generation tools
│   └── __init__.py
├── docs/
│   └── screenshots/          # Visual assets guide
├── .env.example              # Configuration template
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

---

## 🔴 The Problem: The "AI Invisibility Crisis"
90% of brands are absent from ChatGPT, Perplexity, and Gemini recommendations because they lack the "authority signals" LLMs require.

## ⚙️ The Engineering Decisions
- **LangGraph**: Used for a deterministic **State Machine** cycle.
- **Streamlit**: Selected for rapid UI prototyping and Python-native interaction.
- **JSON-LD**: The standard machine-readable format LLMs use for fact extraction.

---

**[BrandSight GEO]** | Licensed under MIT. | **Read the [ARCHITECTURE.md](./ARCHITECTURE.md)** for a technical deep dive.
