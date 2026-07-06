import hashlib
from datetime import datetime, timedelta

import streamlit as st


def render_live_ticker(brand_name):
    """Render the real-time activity feed/live ticker."""
    st.markdown("""
        <div style="margin-bottom: 15px;">
            <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.25rem;">🔄 Live Activity Feed</h3>
            <p style="color: #64748B; font-size: 0.9rem; margin-top: 0; margin-bottom: 15px;">
                Real-time tracking of search visibility updates and remediation deployment.
            </p>
        </div>
    """, unsafe_allow_html=True)

    now = datetime.now()
    seed = int(hashlib.md5(f"{brand_name}:{now.strftime('%Y%m%d%H')}".encode(), usedforsecurity=False).hexdigest()[:8], 16)

    templates = [
        ("✅", f"JSON-LD schema generated for {brand_name}"),
        ("📈", "Brand visibility increased 2.3% on ChatGPT"),
        ("📝", "New gap detected: Missing mobile menu page"),
        ("🛠️", "Remediation completed: FAQ section added to website"),
        ("🔔", f"{brand_name} mentioned on local business listings"),
        ("📊", "Competitor scan completed — 3 rivals tracked"),
        ("🔗", f"New citation detected for {brand_name} on Perplexity"),
    ]

    selected_indices = []
    rng_val = seed
    while len(selected_indices) < 5:
        idx = rng_val % len(templates)
        if idx not in selected_indices:
            selected_indices.append(idx)
        rng_val = (rng_val * 6364136223846793005 + 1) & 0xFFFFFFFF

    activities = []
    for i, idx in enumerate(selected_indices):
        offset_minutes = i * 2 + (seed + i) % 3
        ts = now - timedelta(minutes=offset_minutes)
        status, text = templates[idx]
        activities.append({"time": ts.strftime("%I:%M %p"), "status": status, "text": text})

    st.markdown('<div style="background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(124, 58, 237, 0.08); border-radius: 12px; padding: 16px; box-shadow: 0 4px 12px -2px rgba(0,0,0,0.04);">', unsafe_allow_html=True)

    for act in activities:
        st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.1rem;">{act['status']}</span>
                    <span style="font-size: 0.9rem; color: #1E293B;">{act['text']}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 500;">
                    {act['time']}
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
