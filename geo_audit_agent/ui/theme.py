from __future__ import annotations

from pathlib import Path
from html import escape

import streamlit as st


_EXTRA_CSS = r"""
<style>
:root {
  --bs-bg: #f5f7fb;
  --bs-surface: rgba(255,255,255,.88);
  --bs-surface-solid: #ffffff;
  --bs-ink: #111827;
  --bs-muted: #667085;
  --bs-line: rgba(17,24,39,.09);
  --bs-brand: #6941c6;
  --bs-brand-dark: #42307d;
  --bs-blue: #175cd3;
  --bs-success: #067647;
  --bs-warning: #b54708;
  --bs-danger: #b42318;
  --bs-shadow-sm: 0 1px 2px rgba(16,24,40,.05), 0 3px 10px rgba(16,24,40,.05);
  --bs-shadow-lg: 0 24px 64px rgba(16,24,40,.12), 0 6px 18px rgba(16,24,40,.06);
}

html { scroll-behavior: smooth; }
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 8% -5%, rgba(105,65,198,.10), transparent 28rem),
    radial-gradient(circle at 96% 6%, rgba(23,92,211,.08), transparent 26rem),
    linear-gradient(180deg, #fafbfe 0%, var(--bs-bg) 100%);
  color: var(--bs-ink);
}
[data-testid="stHeader"] { background: rgba(250,251,254,.76); backdrop-filter: blur(18px); }
.block-container { max-width: 1380px; padding-top: 2rem; padding-bottom: 5rem; }

/* Typography */
h1, h2, h3, h4, h5, h6 { letter-spacing: -.025em !important; color: var(--bs-ink) !important; }
p, label, [data-testid="stCaptionContainer"] { color: var(--bs-muted); }

/* Landing / dashboard hero */
.bs-hero {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  min-height: 350px;
  padding: 3.5rem;
  border-radius: 30px;
  color: #fff;
  background:
    linear-gradient(125deg, rgba(15,23,42,.99), rgba(38,33,88,.97) 55%, rgba(76,29,149,.94));
  box-shadow: 0 32px 90px rgba(45,36,99,.25), inset 0 1px 0 rgba(255,255,255,.18);
  border: 1px solid rgba(255,255,255,.13);
  transform-style: preserve-3d;
  perspective: 1200px;
  margin-bottom: 1.75rem;
}
.bs-hero::before {
  content: "";
  position: absolute;
  width: 420px; height: 420px; right: -90px; top: -150px;
  border-radius: 50%;
  background: radial-gradient(circle at 34% 34%, rgba(255,255,255,.44), rgba(139,92,246,.22) 32%, transparent 68%);
  z-index: -1;
  animation: bs-float 10s ease-in-out infinite;
}
.bs-hero::after {
  content: "";
  position: absolute;
  width: 280px; height: 280px; right: 22%; bottom: -190px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(56,189,248,.30), transparent 68%);
  z-index: -1;
}
.bs-kicker {
  display: inline-flex; align-items: center; gap: .5rem;
  padding: .45rem .75rem;
  border: 1px solid rgba(255,255,255,.16);
  border-radius: 999px;
  background: rgba(255,255,255,.09);
  color: rgba(255,255,255,.88);
  font-size: .72rem; font-weight: 750; letter-spacing: .09em; text-transform: uppercase;
}
.bs-hero h1 { color:#fff !important; -webkit-text-fill-color:#fff !important; font-size:clamp(2.8rem,5vw,5rem) !important; line-height:1 !important; max-width:860px; margin:1.25rem 0 .9rem !important; }
.bs-hero p { max-width:760px; color:rgba(255,255,255,.74); font-size:1.12rem; line-height:1.7; }
.bs-hero-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.75rem; max-width:830px; margin-top:1.8rem; }
.bs-hero-stat { padding:1rem 1.1rem; border-radius:16px; background:rgba(255,255,255,.075); border:1px solid rgba(255,255,255,.11); backdrop-filter:blur(14px); }
.bs-hero-stat b { display:block; font-size:1.05rem; color:#fff; }
.bs-hero-stat span { font-size:.76rem; color:rgba(255,255,255,.62); }

/* Sections and cards */
.bs-section-title { margin:2.35rem 0 1rem; }
.bs-section-title h2 { margin:0 !important; font-size:2rem !important; }
.bs-section-title p { color:var(--bs-muted); margin:.35rem 0 0; max-width:760px; }
.bs-card-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; }
.bs-card, .bs-step, .bs-panel {
  position:relative;
  border-radius:22px;
  background:linear-gradient(145deg,rgba(255,255,255,.97),rgba(248,250,252,.82));
  border:1px solid var(--bs-line);
  box-shadow:var(--bs-shadow-sm), inset 0 1px 0 #fff;
}
.bs-card { min-height:180px; padding:1.35rem; transition:transform .3s cubic-bezier(.16,1,.3,1), box-shadow .3s ease, border-color .3s ease; overflow:hidden; }
.bs-card::after { content:""; position:absolute; width:130px; height:130px; right:-65px; top:-65px; border-radius:50%; background:radial-gradient(circle,rgba(105,65,198,.10),transparent 70%); }
.bs-card:hover { transform:translateY(-6px) rotateX(1deg); box-shadow:var(--bs-shadow-lg); border-color:rgba(105,65,198,.22); }
.bs-card-icon { width:44px; height:44px; display:grid; place-items:center; border-radius:13px; font-size:1.2rem; background:#f4f3ff; color:var(--bs-brand-dark); border:1px solid rgba(105,65,198,.12); box-shadow:0 8px 18px rgba(105,65,198,.10); }
.bs-card h3 { margin:.95rem 0 .42rem !important; font-size:1.12rem !important; }
.bs-card p { color:var(--bs-muted); font-size:.88rem; line-height:1.58; margin:0; }
.bs-card small { display:block; margin-top:1rem; color:var(--bs-brand); font-weight:700; }

.bs-step-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; }
.bs-step { padding:1.25rem; }
.bs-step-num { width:32px; height:32px; display:grid; place-items:center; border-radius:10px; background:#f4f3ff; color:var(--bs-brand-dark); font-weight:800; font-size:.8rem; }
.bs-step h3 { margin:.9rem 0 .35rem !important; font-size:1rem !important; }
.bs-step p { margin:0; color:var(--bs-muted); font-size:.86rem; line-height:1.55; }

.bs-trustbar { display:flex; flex-wrap:wrap; gap:.65rem; margin:1rem 0 0; }
.bs-trustpill { padding:.55rem .75rem; border-radius:999px; background:rgba(255,255,255,.86); border:1px solid var(--bs-line); color:#344054; font-size:.76rem; font-weight:650; box-shadow:var(--bs-shadow-sm); }

.bs-callout { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:1.3rem 1.4rem; border-radius:20px; background:linear-gradient(110deg,#f4f3ff,#eff8ff); border:1px solid rgba(105,65,198,.12); margin:1.25rem 0; }
.bs-callout strong { color:#1d2939; }
.bs-callout span { color:var(--bs-muted); font-size:.86rem; }

/* Streamlit component refinement */
[data-testid="stForm"], [data-testid="stMetric"], div[data-testid="stExpander"], [data-testid="stDataFrame"], [data-testid="stVerticalBlockBorderWrapper"] {
  border-radius:20px !important;
  border:1px solid var(--bs-line) !important;
  background:rgba(255,255,255,.88) !important;
  backdrop-filter:blur(16px) saturate(135%);
  box-shadow:var(--bs-shadow-sm), inset 0 1px 0 rgba(255,255,255,.9) !important;
}
[data-testid="stMetric"] { padding:1rem 1.15rem; transition:transform .25s ease, box-shadow .25s ease; }
[data-testid="stMetric"]:hover { transform:translateY(-3px); box-shadow:0 16px 38px rgba(16,24,40,.11) !important; }
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button { min-height:44px; border-radius:12px !important; font-weight:700 !important; transition:transform .2s ease, box-shadow .2s ease !important; }
.stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover { transform:translateY(-1px); }
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] { background:linear-gradient(135deg,var(--bs-brand),#53389e) !important; border:0 !important; box-shadow:0 8px 20px rgba(105,65,198,.24) !important; }
input, textarea, [data-baseweb="select"] > div { border-radius:12px !important; border-color:rgba(52,64,84,.16) !important; background:rgba(255,255,255,.92) !important; }
input:focus, textarea:focus { box-shadow:0 0 0 4px rgba(105,65,198,.09) !important; }
[data-testid="stSidebar"] { background:rgba(255,255,255,.90); box-shadow:10px 0 40px rgba(16,24,40,.05); }
[data-testid="stSidebarNav"] a { border-radius:10px; margin:3px 8px; transition:.18s ease; }
[data-testid="stSidebarNav"] a:hover { transform:translateX(2px); background:rgba(105,65,198,.07); }
[data-testid="stAlert"] { border-radius:14px !important; border-width:1px !important; }

.bs-empty { padding:2.25rem; border-radius:22px; text-align:center; background:linear-gradient(145deg,rgba(255,255,255,.92),rgba(248,250,252,.72)); border:1px dashed rgba(105,65,198,.24); box-shadow:inset 0 1px 0 #fff; }
.bs-empty-icon { width:48px; height:48px; margin:0 auto; display:grid; place-items:center; border-radius:14px; background:#f4f3ff; color:var(--bs-brand-dark); font-size:1.35rem; }
.bs-empty h3 { margin:.8rem 0 .3rem !important; }
.bs-empty p { color:var(--bs-muted); margin:0 auto; max-width:620px; }

@keyframes bs-float { 0%,100% { transform:translate3d(0,0,0) rotate(0deg); } 50% { transform:translate3d(-12px,18px,0) rotate(4deg); } }
@keyframes bs-rise { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.block-container > div { animation:bs-rise .42s ease both; }

@media (max-width: 980px) {
  .bs-card-grid, .bs-step-grid, .bs-hero-grid { grid-template-columns:1fr; }
  .bs-hero { padding:2rem; min-height:auto; }
  .bs-callout { align-items:flex-start; flex-direction:column; }
  .block-container { padding-left:1rem; padding-right:1rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; scroll-behavior:auto !important; }
}
</style>
"""


def apply_theme() -> None:
    """Inject the shared BrandSight design system on every Streamlit page."""
    css_path = Path(__file__).resolve().parents[2] / "style.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    st.markdown(f"<style>{css}</style>{_EXTRA_CSS}", unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, *, kicker: str = "Evidence-led AI visibility") -> None:
    st.markdown(
        f"""
        <section class="bs-hero">
          <div class="bs-kicker">{escape(kicker)}</div>
          <h1>{escape(title)}</h1>
          <p>{escape(subtitle)}</p>
          <div class="bs-hero-grid">
            <div class="bs-hero-stat"><b>Multi-provider</b><span>One evidence model across four adapters</span></div>
            <div class="bs-hero-stat"><b>Attributable</b><span>Raw responses and collection metadata</span></div>
            <div class="bs-hero-stat"><b>Controlled</b><span>Approval-gated recommendations and actions</span></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(icon: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="bs-section-title">
          <div class="bs-kicker" style="color:#42307d;background:#f4f3ff;border-color:rgba(105,65,198,.14)">{escape(icon)} Workspace</div>
          <h2>{escape(title)}</h2>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty(icon: str, title: str, message: str) -> None:
    st.markdown(
        f"<div class='bs-empty'><div class='bs-empty-icon'>{escape(icon)}</div><h3>{escape(title)}</h3><p>{escape(message)}</p></div>",
        unsafe_allow_html=True,
    )
