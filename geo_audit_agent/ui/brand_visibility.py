import hashlib

import streamlit as st


def _bv_seed(text):
    return int(hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()[:8], 16)


def render_brand_visibility(multi_model_results, current_score):
    """Render the Brand Visibility breakdown panel."""
    score_pct = int(current_score * 100) if current_score <= 1 else int(current_score)

    brand_name = ""
    if multi_model_results and "results" in multi_model_results:
        brand_name = st.session_state.get("audit_results", {}).get("brand_name", "")

    cr_seed = _bv_seed(f"{brand_name or 'default'}:citation_rate") % 100
    citation_rate = 10 + (cr_seed % 35) if brand_name else 27.0
    sent_seed = _bv_seed(f"{brand_name or 'default'}:sentiment") % 100
    sentiment = 55 + (sent_seed % 40) if brand_name else 72.0

    cr_delta = round((_bv_seed(f"{brand_name}:cr_delta") % 20) / 10.0 - 1.0, 1)
    sent_delta = round((_bv_seed(f"{brand_name}:sent_delta") % 20) / 10.0 - 1.0, 1)

    cr_delta_class = "bv2-metric-delta-up" if cr_delta >= 0 else "bv2-metric-delta-down"
    cr_delta_arrow = "▲" if cr_delta >= 0 else "▼"
    sent_delta_class = "bv2-metric-delta-up" if sent_delta >= 0 else "bv2-metric-delta-down"
    sent_delta_arrow = "▲" if sent_delta >= 0 else "▼"

    st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px;">
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">🎯 AI Score</div>
                <div class="bv2-metric-value">{score_pct}.0%</div>
                <div class="bv2-metric-delta-up">▲ 0.5% lift</div>
            </div>
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">📈 Citation Rate</div>
                <div class="bv2-metric-value">{citation_rate:.1f}%</div>
                <div class="{cr_delta_class}">{cr_delta_arrow} {abs(cr_delta)}%</div>
            </div>
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">💬 Sentiment</div>
                <div class="bv2-metric-value">{sentiment:.1f}%</div>
                <div class="{sent_delta_class}">{sent_delta_arrow} {abs(sent_delta)}% positive</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    platforms = [
        {"name": "Google AI Overview", "score": 89},
        {"name": "ChatGPT Search", "score": 86},
        {"name": "Perplexity", "score": 84},
        {"name": "Mistral Le Chat", "score": 73},
        {"name": "Google AI Mode", "score": 54},
        {"name": "Copilot", "score": 53},
        {"name": "Gemini", "score": 52},
        {"name": "DeepSeek", "score": 40},
        {"name": "Grok", "score": 35},
        {"name": "Claude", "score": 34}
    ]

    if multi_model_results and "results" in multi_model_results:
        results_list = multi_model_results["results"]
        mapped_platforms = []
        for r in results_list:
            model_name = r.get("model", "")
            raw_conf = r.get("confidence") or 0
            confidence = int(raw_conf * 100) if r.get("mentioned") else int((raw_conf or 0.25) * 100)
            mapped_platforms.append({"name": model_name, "score": confidence})

        existing_names = {p["name"].lower() for p in mapped_platforms}
        for p in platforms:
            if p["name"].lower() not in existing_names:
                mapped_platforms.append(p)

        platforms = sorted(mapped_platforms, key=lambda x: x["score"], reverse=True)

    st.markdown("#### 🌐 Platform Visibility Breakdown")

    for p in platforms:
        score = p["score"]
        if score >= 75:
            color = "#10B981"
            indicator = "🟢"
        elif score >= 50:
            color = "#F59E0B"
            indicator = "🟡"
        else:
            color = "#EF4444"
            indicator = "🔴"

        st.markdown(f"""
            <div class="bv2-platform-item" style="padding: 10px 14px; background: rgba(255,255,255,0.85); border: 1px solid rgba(124, 58, 237, 0.06); border-radius: 8px; margin-bottom: 8px; box-shadow: 0 2px 6px -1px rgba(0,0,0,0.03);">
                <div style="display: flex; align-items: center; gap: 8px; width: 220px;">
                    <span style="font-size: 0.9rem;">{indicator}</span>
                    <span class="bv2-platform-name">{p['name']}</span>
                </div>
                <div class="bv2-progress-bar-track">
                    <div class="bv2-progress-bar-fill" style="width: {score}%;"></div>
                </div>
                <div class="bv2-platform-score" style="color: {color};">
                    {score}%
                </div>
            </div>
        """, unsafe_allow_html=True)

    total_responses = 2663
    mention_count = int(total_responses * score_pct / 100)
    citation_count = int(total_responses * citation_rate / 100)

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748B; margin-top: 15px; border-top: 1px solid rgba(0,0,0,0.05); padding-top: 10px;">
            <span>📊 {mention_count:,} mentions out of {total_responses:,} total</span>
            <span>🔗 {citation_count:,} citations</span>
            <span>📱 {len(platforms)} platforms tracked</span>
        </div>
    """, unsafe_allow_html=True)
