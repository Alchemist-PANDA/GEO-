from __future__ import annotations

from pathlib import Path

import streamlit as st


_EXTRA_CSS = r"""
<style>
:root {
  --bg: #f6f7fb;
  --surface: rgba(255,255,255,.78);
  --surface-strong: rgba(255,255,255,.94);
  --ink: #0f172a;
  --muted: #64748b;
  --purple: #7c3aed;
  --blue: #2563eb;
  --pink: #ec4899;
  --cyan: #06b6d4;
  --success: #10b981;
  --danger: #ef4444;
}

html { scroll-behavior: smooth; }
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 15% 5%, rgba(124,58,237,.12), transparent 28%),
    radial-gradient(circle at 84% 12%, rgba(37,99,235,.12), transparent 25%),
    radial-gradient(circle at 58% 82%, rgba(236,72,153,.08), transparent 26%),
    linear-gradient(180deg, #f8fafc 0%, #f3f4f8 100%);
}
[data-testid="stHeader"] { background: rgba(248,250,252,.64); backdrop-filter: blur(18px); }
.block-container { max-width: 1440px; padding-top: 2.2rem; padding-bottom: 4rem; }

/* Premium shell */
.bs-hero {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  min-height: 330px;
  padding: 3.2rem 3.4rem;
  border-radius: 32px;
  color: #fff;
  background:
    linear-gradient(125deg, rgba(8,15,35,.98), rgba(49,46,129,.96) 55%, rgba(109,40,217,.92));
  box-shadow: 0 30px 90px rgba(49,46,129,.28), inset 0 1px 0 rgba(255,255,255,.22);
  border: 1px solid rgba(255,255,255,.16);
  transform-style: preserve-3d;
  perspective: 1200px;
  margin-bottom: 1.6rem;
}
.bs-hero::before, .bs-hero::after {
  content: "";
  position: absolute;
  border-radius: 999px;
  filter: blur(1px);
  opacity: .8;
  z-index: -1;
  animation: bs-float 8s ease-in-out infinite;
}
.bs-hero::before {
  width: 360px; height: 360px; right: -80px; top: -120px;
  background: radial-gradient(circle at 35% 35%, rgba(255,255,255,.55), rgba(168,85,247,.28) 30%, transparent 68%);
}
.bs-hero::after {
  width: 250px; height: 250px; right: 18%; bottom: -150px;
  background: radial-gradient(circle, rgba(34,211,238,.45), transparent 70%);
  animation-delay: -3s;
}
.bs-kicker { display:inline-flex; gap:.5rem; align-items:center; padding:.45rem .8rem; border:1px solid rgba(255,255,255,.18); border-radius:999px; background:rgba(255,255,255,.1); font-size:.76rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
.bs-hero h1 { color:#fff !important; -webkit-text-fill-color:#fff !important; font-size:clamp(2.7rem,5vw,5.2rem) !important; line-height:.95 !important; max-width:850px; margin:1.2rem 0 .9rem !important; }
.bs-hero p { max-width:760px; color:rgba(255,255,255,.78); font-size:1.15rem; line-height:1.7; }
.bs-hero-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.8rem; max-width:820px; margin-top:1.6rem; }
.bs-hero-stat { padding:1rem 1.1rem; border-radius:18px; background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.12); backdrop-filter:blur(14px); }
.bs-hero-stat b { display:block; font-size:1.2rem; color:#fff; }
.bs-hero-stat span { font-size:.78rem; color:rgba(255,255,255,.67); }

.bs-section-title { margin:2.2rem 0 .9rem; }
.bs-section-title h2 { margin:0 !important; font-size:2rem !important; }
.bs-section-title p { color:var(--muted); margin:.35rem 0 0; }
.bs-card-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; }
.bs-card {
  position:relative;
  min-height:175px;
  padding:1.35rem;
  border-radius:24px;
  background:linear-gradient(145deg,rgba(255,255,255,.94),rgba(248,250,252,.72));
  border:1px solid rgba(124,58,237,.1);
  box-shadow:0 16px 45px rgba(15,23,42,.08), inset 0 1px 0 #fff;
  transition:transform .35s cubic-bezier(.16,1,.3,1), box-shadow .35s ease, border-color .35s ease;
  overflow:hidden;
}
.bs-card::after { content:""; position:absolute; width:150px; height:150px; right:-70px; top:-70px; border-radius:50%; background:radial-gradient(circle,rgba(124,58,237,.13),transparent 70%); }
.bs-card:hover { transform:translateY(-8px) rotateX(1.4deg) rotateY(-1.4deg); box-shadow:0 30px 70px rgba(49,46,129,.17); border-color:rgba(124,58,237,.25); }
.bs-card-icon { width:48px; height:48px; display:grid; place-items:center; border-radius:15px; font-size:1.45rem; background:linear-gradient(145deg,#fff,rgba(124,58,237,.1)); box-shadow:0 10px 25px rgba(124,58,237,.15); }
.bs-card h3 { margin:.95rem 0 .45rem !important; font-size:1.15rem !important; }
.bs-card p { color:var(--muted); font-size:.88rem; line-height:1.55; margin:0; }

/* Streamlit components */
[data-testid="stForm"], [data-testid="stMetric"], div[data-testid="stExpander"], [data-testid="stDataFrame"], [data-testid="stVerticalBlockBorderWrapper"] {
  border-radius:22px !important;
  border:1px solid rgba(124,58,237,.09) !important;
  background:rgba(255,255,255,.8) !important;
  backdrop-filter:blur(18px) saturate(145%);
  box-shadow:0 16px 42px rgba(15,23,42,.07), inset 0 1px 0 rgba(255,255,255,.9) !important;
}
[data-testid="stMetric"] { padding:1.15rem 1.25rem; transition:.3s ease; }
[data-testid="stMetric"]:hover { transform:translateY(-5px); box-shadow:0 24px 54px rgba(49,46,129,.14) !important; }
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
  min-height:46px;
  border-radius:14px !important;
  font-weight:700 !important;
  transition:transform .25s ease, box-shadow .25s ease !important;
}
.stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover { transform:translateY(-2px); }
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] {
  background:linear-gradient(135deg,var(--purple),var(--blue)) !important;
  border:0 !important;
  box-shadow:0 12px 28px rgba(79,70,229,.28) !important;
}
input, textarea, [data-baseweb="select"] > div {
  border-radius:14px !important;
  border-color:rgba(100,116,139,.18) !important;
  background:rgba(255,255,255,.82) !important;
}
input:focus, textarea:focus { box-shadow:0 0 0 4px rgba(124,58,237,.1) !important; }
[data-testid="stSidebar"] { box-shadow:12px 0 50px rgba(15,23,42,.06); }
[data-testid="stSidebarNav"] a { border-radius:11px; margin:3px 8px; transition:.2s ease; }
[data-testid="stSidebarNav"] a:hover { transform:translateX(3px); background:rgba(124,58,237,.08); }
[data-testid="stAlert"] { border-radius:16px !important; border-width:1px !important; }

.bs-empty { padding:2.1rem; border-radius:24px; text-align:center; background:linear-gradient(145deg,rgba(255,255,255,.88),rgba(248,250,252,.64)); border:1px dashed rgba(124,58,237,.25); box-shadow:inset 0 1px 0 #fff; }
.bs-empty-icon { font-size:2.4rem; filter:drop-shadow(0 10px 16px rgba(124,58,237,.2)); }
.bs-empty h3 { margin:.6rem 0 .3rem !important; }
.bs-empty p { color:var(--muted); margin:0; }

@keyframes bs-float { 0%,100% { transform:translate3d(0,0,0) rotate(0deg); } 50% { transform:translate3d(-14px,20px,0) rotate(6deg); } }
@keyframes bs-rise { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
.block-container > div { animation:bs-rise .55s ease both; }

@media (max-width: 980px) {
  .bs-card-grid, .bs-hero-grid { grid-template-columns:1fr; }
  .bs-hero { padding:2rem; min-height:auto; }
  .block-container { padding-left:1rem; padding-right:1rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; scroll-behavior:auto !important; }
}
</style>
"""


def apply_theme() -> None:
    """Load the repository theme once per Streamlit page."""
    if st.session_state.get("_brandsight_theme_loaded"):
        return
    css_path = Path(__file__).resolve().parents[2] / "style.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    st.markdown(f"<style>{css}</style>{_EXTRA_CSS}", unsafe_allow_html=True)
    st.session_state["_brandsight_theme_loaded"] = True


def render_hero(title: str, subtitle: str, *, kicker: str = "AI visibility operating system") -> None:
    st.markdown(
        f"""
        <section class="bs-hero">
          <div class="bs-kicker">✦ {kicker}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
          <div class="bs-hero-grid">
            <div class="bs-hero-stat"><b>4 providers</b><span>Evidence-aware adapters</span></div>
            <div class="bs-hero-stat"><b>Raw evidence</b><span>Attributable observations</span></div>
            <div class="bs-hero-stat"><b>Human control</b><span>Approval-gated actions</span></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(icon: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="bs-section-title">
          <div class="bs-kicker" style="color:#5b21b6;background:rgba(124,58,237,.08);border-color:rgba(124,58,237,.14)">{icon} Workspace</div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty(icon: str, title: str, message: str) -> None:
    st.markdown(
        f"<div class='bs-empty'><div class='bs-empty-icon'>{icon}</div><h3>{title}</h3><p>{message}</p></div>",
        unsafe_allow_html=True,
    )
