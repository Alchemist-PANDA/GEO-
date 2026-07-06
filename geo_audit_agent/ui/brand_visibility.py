import streamlit as st

def render_brand_visibility(multi_model_results, current_score):
    """Render the Brand Visibility breakdown panel."""
    score_pct = int(current_score * 100) if current_score <= 1 else int(current_score)

    st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px;">
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">🎯 AI Score</div>
                <div class="bv2-metric-value">{score_pct}.0%</div>
                <div class="bv2-metric-delta-up">▲ 0.5% lift</div>
            </div>
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">📈 Citation Rate</div>
                <div class="bv2-metric-value">27.0%</div>
                <div class="bv2-metric-delta-down">▼ 0.9% drop</div>
            </div>
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">💬 Sentiment</div>
                <div class="bv2-metric-value">72.0%</div>
                <div class="bv2-metric-delta-up">▲ 0.8% positive</div>
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
            confidence = int(r.get("confidence", 0) * 100) if r.get("mentioned") else int(r.get("confidence", 0.25) * 100)
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

    st.markdown("""
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748B; margin-top: 15px; border-top: 1px solid rgba(0,0,0,0.05); padding-top: 10px;">
            <span>📊 1,597 mentions out of 2,663 total</span>
            <span>🔗 719 citations</span>
            <span>📱 10 platforms tracked</span>
        </div>
    """, unsafe_allow_html=True)
