from __future__ import annotations

from html import escape

import streamlit as st


_CSS = r"""
<style>
:root {
  --bs-bg: #f6f7f9;
  --bs-surface: #ffffff;
  --bs-surface-muted: #f9fafb;
  --bs-ink: #111827;
  --bs-muted: #667085;
  --bs-line: #d9dee7;
  --bs-primary: #0f766e;
  --bs-primary-dark: #115e59;
  --bs-blue: #1d4ed8;
  --bs-success: #15803d;
  --bs-warning: #b45309;
  --bs-danger: #b91c1c;
  --bs-neutral: #475467;
}

[data-testid="stAppViewContainer"] {
  background: var(--bs-bg);
  color: var(--bs-ink);
}

[data-testid="stHeader"] {
  background: rgba(246, 247, 249, .94);
  border-bottom: 1px solid var(--bs-line);
}

.block-container {
  max-width: 1440px;
  padding-top: 1.25rem;
  padding-bottom: 3rem;
}

h1, h2, h3, h4, h5, h6 {
  color: var(--bs-ink) !important;
  letter-spacing: 0 !important;
}

p, label, [data-testid="stCaptionContainer"] {
  color: var(--bs-muted);
}

[data-testid="stSidebar"] {
  background: #ffffff;
  border-right: 1px solid var(--bs-line);
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] p {
  color: var(--bs-ink) !important;
}

[data-testid="stRadio"] label {
  font-weight: 600;
}

.bs-topbar {
  background: var(--bs-surface);
  border: 1px solid var(--bs-line);
  border-radius: 8px;
  padding: .85rem;
  margin-bottom: 1rem;
}

.bs-page-header {
  margin: .75rem 0 1rem;
}

.bs-page-header .bs-kicker {
  color: var(--bs-primary);
  font-size: .75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
}

.bs-page-header h1 {
  font-size: 2rem !important;
  line-height: 1.2 !important;
  margin: .15rem 0 .25rem !important;
}

.bs-page-header p {
  max-width: 780px;
  margin: 0;
}

.bs-metric-card,
.bs-panel,
[data-testid="stForm"],
div[data-testid="stExpander"],
[data-testid="stDataFrame"],
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--bs-surface) !important;
  border: 1px solid var(--bs-line) !important;
  border-radius: 8px !important;
  box-shadow: 0 1px 2px rgba(16, 24, 40, .04) !important;
}

.bs-metric-card {
  min-height: 148px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.bs-metric-top,
.bs-panel-head,
.bs-metric-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .75rem;
}

.bs-metric-top span:first-child {
  color: var(--bs-muted);
  font-size: .82rem;
  font-weight: 700;
}

.bs-metric-card strong {
  display: block;
  color: var(--bs-ink);
  font-size: 1.75rem;
  line-height: 1.2;
  margin-top: .65rem;
}

.bs-metric-denom {
  color: var(--bs-muted);
  font-size: .82rem;
  margin-top: .25rem;
}

.bs-metric-foot {
  color: var(--bs-muted);
  font-size: .78rem;
  margin-top: .75rem;
}

.bs-panel {
  padding: 1rem;
  margin-bottom: 1rem;
}

.bs-panel h3 {
  font-size: 1rem !important;
  margin: 0 !important;
}

.bs-panel p {
  margin: .6rem 0 0;
}

.bs-badge {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  border-radius: 999px;
  padding: 0 .55rem;
  font-size: .72rem;
  font-weight: 700;
  border: 1px solid transparent;
  white-space: nowrap;
}

.bs-badge-live,
.bs-badge-passed {
  color: #166534;
  background: #dcfce7;
  border-color: #bbf7d0;
}

.bs-badge-cached {
  color: #1d4ed8;
  background: #dbeafe;
  border-color: #bfdbfe;
}

.bs-badge-demo {
  color: #92400e;
  background: #fef3c7;
  border-color: #fde68a;
}

.bs-badge-failed,
.bs-badge-auth-error {
  color: #991b1b;
  background: #fee2e2;
  border-color: #fecaca;
}

.bs-badge-insufficient-evidence,
.bs-badge-quota-limited {
  color: #475467;
  background: #f2f4f7;
  border-color: #e4e7ec;
}

.bs-empty {
  padding: 2rem;
  text-align: center;
  border: 1px dashed var(--bs-line);
  border-radius: 8px;
  background: var(--bs-surface);
}

.bs-empty-icon {
  color: var(--bs-primary);
  font-weight: 800;
  margin-bottom: .5rem;
}

.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {
  border-radius: 8px !important;
  min-height: 40px;
  font-weight: 700 !important;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
  background: var(--bs-primary) !important;
  border-color: var(--bs-primary) !important;
}

.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
  background: var(--bs-primary-dark) !important;
  border-color: var(--bs-primary-dark) !important;
}

input,
textarea,
[data-baseweb="select"] > div {
  border-radius: 8px !important;
}

[data-testid="stAlert"] {
  border-radius: 8px !important;
}

@media (max-width: 900px) {
  .block-container {
    padding-left: .75rem;
    padding-right: .75rem;
  }

  .bs-topbar {
    padding: .6rem;
  }

  .bs-metric-card strong {
    font-size: 1.3rem;
  }
}
</style>
"""


def apply_theme() -> None:
    """Inject the BrandSight operational SaaS theme."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <header class="bs-page-header">
          <div class="bs-kicker">{escape(kicker)}</div>
          <h1>{escape(title)}</h1>
          <p>{escape(subtitle)}</p>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_empty(icon: str, title: str, message: str) -> None:
    st.markdown(
        f"""
        <div class="bs-empty">
          <div class="bs-empty-icon">{escape(icon)}</div>
          <h3>{escape(title)}</h3>
          <p>{escape(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str, *, kicker: str = "Evidence-led AI visibility") -> None:
    render_page_header(kicker, title, subtitle)
