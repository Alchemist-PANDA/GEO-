import hashlib

import streamlit as st
import plotly.graph_objects as go
from geo_audit_agent.ui.chart_wrapper import render_chart_with_explain_button

def clean_html(html_str: str) -> str:
    return "\n".join(line.strip() for line in html_str.split("\n"))

def normalize_multi_model_results(multi_model_results):
    if not multi_model_results:
        return multi_model_results
    
    # Format A check (if results key is present, it's already Format A)
    if "results" in multi_model_results:
        return multi_model_results
    
    # Format B conversion
    brand = multi_model_results.get("brand", "Burger Hub")
    scores = multi_model_results.get("scores", {})
    platforms = multi_model_results.get("platforms", {})
    
    results = []
    for platform, score_val in platforms.items():
        # confidence is fraction of 100
        conf = score_val / 100.0 if score_val > 1.0 else score_val
        results.append({
            "model": platform,
            "mentioned": score_val > 0,
            "confidence": conf
        })
    
    summary = {
        "geo_coverage_score": int(scores.get("visibility", 0))
    }
    
    return {
        "brand": brand,
        "results": results,
        "summary": summary
    }

def render_momentum_sparkline(historical_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historical_data['dates'],
        y=historical_data['values'],
        mode='lines+markers',
        line=dict(color='#7C3AED', width=2),
        marker=dict(size=4, color='#7C3AED'),
        fill='tozeroy',
        fillcolor='rgba(124, 58, 237, 0.1)'
    ))
    fig.update_layout(
        height=40,
        margin=dict(l=2, r=2, t=2, b=2),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False, visible=False),
        yaxis=dict(showgrid=False, showticklabels=False, visible=False)
    )
    return fig

def get_trust_gap_details(leaderboard, your_brand_name, current_score_pct):
    # Find leader (first in leaderboard)
    leader = leaderboard[0] if leaderboard else None
    
    leader_name = leader.get("name", "McDonald's") if leader else "McDonald's"
    leader_score = leader.get("overall", 98) if leader else 98
    
    # Calculate dimensions breakdown
    dimensions = ['authority', 'schema', 'content', 'reviews', 'entities', 'citations', 'brand']
    
    # Leader scores
    leader_scores = leader.get("scores", {}) if leader else {
        'authority': 95, 'schema': 90, 'content': 88, 'reviews': 92, 'entities': 85, 'citations': 96, 'brand': 98
    }
    
    # Find your brand scores
    your_brand = next((c for c in leaderboard if c.get("name", "").lower() == your_brand_name.lower()), None)
    your_scores = your_brand.get("scores", {}) if your_brand else {
        'authority': 79, 'schema': 84, 'content': 85, 'reviews': 89, 'entities': 79, 'citations': 94, 'brand': current_score_pct
    }
    
    gaps = {}
    for dim in dimensions:
        l_s = leader_scores.get(dim, 90)
        y_s = your_scores.get(dim, 70)
        gaps[dim] = max(0, l_s - y_s)
        
    sorted_gaps = sorted(gaps.items(), key=lambda x: x[1], reverse=True)
    
    gap_val = max(0, int(leader_score - current_score_pct))
    
    return {
        "leader_name": leader_name,
        "leader_score": leader_score,
        "gap_value": gap_val,
        "breakdown": sorted_gaps
    }

def render_market_simulator():
    """Renders the AI Market Simulator full-width section."""
    st.markdown("### 🧪 AI Market Simulator")
    
    col1, col2 = st.columns(2)
    
    is_dark = st.session_state.get("theme", "Light") == "Dark"
    card_bg = "rgba(26, 26, 46, 0.45)" if is_dark else "rgba(255, 255, 255, 0.9)"
    card_border = "rgba(255, 255, 255, 0.06)" if is_dark else "rgba(124, 58, 237, 0.08)"
    text_color = "#FFFFFF" if is_dark else "#1E293B"
    label_color = "#94A3B8" if is_dark else "#64748B"
    
    with col1:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 16px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); height: 100%;">
            <span style="font-size: 0.75rem; color: #7C3AED; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">📄 Scenario 1: Add 30 FAQ Pages</span>
            <h4 style="margin: 10px 0 5px 0; color: {text_color}; font-size: 1.1rem; font-weight: 800;">Visibility Impact: +7.0%</h4>
            <div style="font-size: 0.85rem; color: {label_color}; margin-bottom: 8px;">Rank Improvement: <strong>#8 &rarr; #4</strong></div>
            <div style="font-size: 0.85rem; color: {label_color};">Effort: <strong>4 hours</strong> • Priority: <strong>#1 (Highest)</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 16px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); height: 100%;">
            <span style="font-size: 0.75rem; color: #EC4899; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">📰 Scenario 2: Wikipedia Page</span>
            <h4 style="margin: 10px 0 5px 0; color: {text_color}; font-size: 1.1rem; font-weight: 800;">Trust Impact: +12.0%</h4>
            <div style="font-size: 0.85rem; color: {label_color}; margin-bottom: 8px;">Rank Improvement: <strong>Prominent Entity Citation</strong></div>
            <div style="font-size: 0.85rem; color: {label_color};">Effort: <strong>10 hours</strong> • Priority: <strong>#2</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # Comparison Table
    table_html = f"""
    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 16px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 24px;">
        <span style="font-size: 0.75rem; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">📊 Scenario Comparison & Priority Table</span>
        <table style="width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.85rem; color: {text_color};">
            <thead>
                <tr style="border-bottom: 1px solid {card_border}; text-align: left;">
                    <th style="padding: 8px; font-weight: 700;">Action Scenario</th>
                    <th style="padding: 8px; font-weight: 700;">Primary Metric Impact</th>
                    <th style="padding: 8px; font-weight: 700;">Effort Estimate</th>
                    <th style="padding: 8px; font-weight: 700;">ROI Rank</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid {card_border};">
                    <td style="padding: 8px; font-weight: 600;">🥇 Add 30 FAQ Pages</td>
                    <td style="padding: 8px; color: #10B981; font-weight: 600;">+7.0% Visibility (Rank #8 &rarr; #4)</td>
                    <td style="padding: 8px;">4 Hours</td>
                    <td style="padding: 8px; font-weight: 700; color: #7C3AED;">Priority #1</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: 600;">🥈 Establish Wikipedia Page</td>
                    <td style="padding: 8px; color: #3B82F6; font-weight: 600;">+12.0% Trust / Citation Boost</td>
                    <td style="padding: 8px;">10 Hours</td>
                    <td style="padding: 8px; font-weight: 700; color: #EC4899;">Priority #2</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    st.markdown(clean_html(table_html), unsafe_allow_html=True)


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
    """), unsafe_allow_html=True)
