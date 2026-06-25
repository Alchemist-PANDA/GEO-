import streamlit as st
import plotly.graph_objects as go

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

def render_brand_visibility(multi_model_results, current_score):
    """Render the Brand Visibility breakdown panel."""
    # Normalize input format first
    multi_model_results = normalize_multi_model_results(multi_model_results)
    
    # Compute display scores
    score_pct = int(current_score * 100) if current_score <= 1 else int(current_score)
    
    # Theme configuration
    is_dark = st.session_state.get("theme", "Light") == "Dark"
    card_bg = "rgba(26, 26, 46, 0.45)" if is_dark else "rgba(255, 255, 255, 0.9)"
    card_border = "rgba(255, 255, 255, 0.06)" if is_dark else "rgba(124, 58, 237, 0.08)"
    text_color = "#FFFFFF" if is_dark else "#1E293B"
    label_color = "#94A3B8" if is_dark else "#64748B"
    row_bg = "rgba(255, 255, 255, 0.02)" if is_dark else "rgba(255, 255, 255, 0.8)"
    row_border = "rgba(255, 255, 255, 0.04)" if is_dark else "rgba(124, 58, 237, 0.05)"
    
    # --- Compute Additional Metrics ---
    brand_name = multi_model_results.get("brand", "Burger Hub") if multi_model_results else "Burger Hub"
    
    # 1. Share of Voice
    competitors = []
    leaderboard = []
    your_mentions = 1597
    if multi_model_results:
        competitors = multi_model_results.get("competitors", [])
        leaderboard = multi_model_results.get("leaderboard", [])
        your_mentions = multi_model_results.get("your_mentions", 1597)
        
    sov_val = 37.5
    sov_subtext = "Mentions Share"
    try:
        if competitors and any(c.get("mentions") is not None for c in competitors):
            total_mentions = sum(c.get("mentions", 0) for c in competitors)
            has_self = any(c.get("name", "").lower() == brand_name.lower() for c in competitors)
            if not has_self:
                total_mentions += your_mentions
                sov_val = (your_mentions / total_mentions) * 100 if total_mentions > 0 else 0.0
            else:
                brand_comp = next(c for c in competitors if c.get("name", "").lower() == brand_name.lower())
                sov_val = (brand_comp.get("mentions", 0) / total_mentions) * 100 if total_mentions > 0 else 0.0
            sov_subtext = f"{your_mentions} of {total_mentions} mentions"
        elif leaderboard:
            total_score = sum(c.get("overall", 0) for c in leaderboard)
            your_score = next((c.get("overall", 0) for c in leaderboard if c.get("name", "").lower() == brand_name.lower()), score_pct)
            has_self = any(c.get("name", "").lower() == brand_name.lower() for c in leaderboard)
            if not has_self:
                total_score += your_score
            sov_val = (your_score / total_score) * 100 if total_score > 0 else 0.0
            sov_subtext = "Estimated from overall scores"
        else:
            sov_val = 37.5
            sov_subtext = "Estimated Share of Voice"
    except Exception:
        pass

    # 2. AI Recommendation Rank
    platform_names = ['ChatGPT', 'Gemini', 'Perplexity', 'Claude', 'Grok', 'DeepSeek']
    platform_ranks = {}
    try:
        if leaderboard:
            for platform in platform_names:
                scores = []
                for comp in leaderboard:
                    comp_scores = comp.get("scores", {})
                    val = 0
                    for k, v in comp_scores.items():
                        if k.lower() == platform.lower():
                            val = v
                            break
                    scores.append((comp.get("name", ""), val))
                
                has_self = any(name.lower() == brand_name.lower() for name, _ in scores)
                if not has_self:
                    brand_plat_score = 50
                    if multi_model_results and "results" in multi_model_results:
                        for r in multi_model_results["results"]:
                            if r.get("model", "").lower() == platform.lower():
                                brand_plat_score = int(r.get("confidence", 0) * 100) if r.get("mentioned") else int(r.get("confidence", 0.25) * 100)
                                break
                    scores.append((brand_name, brand_plat_score))
                
                sorted_comp = sorted(scores, key=lambda x: x[1], reverse=True)
                rank = [i+1 for i, (name, _) in enumerate(sorted_comp) if name.lower() == brand_name.lower()][0]
                platform_ranks[platform] = (rank, len(scores))
        else:
            platform_ranks = {
                'ChatGPT': (2, 6),
                'Gemini': (4, 6),
                'Perplexity': (1, 6),
                'Claude': (3, 6),
                'Grok': (5, 6),
                'DeepSeek': (2, 6)
            }
    except Exception:
        platform_ranks = {p: (1, 5) for p in platform_names}

    rank_items = []
    for platform in platform_names:
        r, t = platform_ranks.get(platform, (1, 5))
        rank_items.append(f"{platform}: #{r} of {t}")
    rank_inline_text = " • ".join(rank_items)

    # 3. Visibility Growth / AI Momentum
    last_score = st.session_state.get("last_scan_score")
    momentum_val = 0
    acceleration = "Slow"
    if last_score is not None:
        last_score_pct = int(last_score * 100) if last_score <= 1 else int(last_score)
        momentum_val = int(score_pct - last_score_pct)
        if abs(momentum_val) >= 15:
            acceleration = "Fast"
        elif abs(momentum_val) >= 5:
            acceleration = "Moderate"
        else:
            acceleration = "Slow"
    else:
        # mock fallback
        momentum_val = 17
        acceleration = "Fast"
        
    momentum_arrow = "▲" if momentum_val >= 0 else "▼"
    momentum_color = "#10B981" if momentum_val >= 0 else "#EF4444"
    
    historical_data = {
        'dates': ['3 months ago', '2 months ago', '1 month ago', 'Current'],
        'values': [score_pct - 15, score_pct - 8, score_pct - 4, score_pct]
    }

    # 4. AI Trust Gap
    gap_details = get_trust_gap_details(leaderboard, brand_name, score_pct)
    top_gap_dim, top_gap_val = gap_details["breakdown"][0] if gap_details["breakdown"] else ("Authority", 16)
    
    # Render KPI Cards Row (Row 1: 3 cards)
    st.markdown(clean_html(f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px;">
            <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 16px; text-align: center;">
                <span style="font-size: 0.75rem; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">🎯 AI Score</span>
                <h3 style="margin: 8px 0 2px 0; font-size: 1.8rem; font-weight: 800; color: {text_color};">{score_pct}.0%</h3>
                <span style="color: #10B981; font-size: 0.75rem; font-weight: 600;">▲ 0.5% lift</span>
            </div>
            <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 16px; text-align: center;">
                <span style="font-size: 0.75rem; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">📈 Citation Rate</span>
                <h3 style="margin: 8px 0 2px 0; font-size: 1.8rem; font-weight: 800; color: {text_color};">27.0%</h3>
                <span style="color: #EF4444; font-size: 0.75rem; font-weight: 600;">▼ 0.9% drop</span>
            </div>
            <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 16px; text-align: center;">
                <span style="font-size: 0.75rem; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">💬 Sentiment</span>
                <h3 style="margin: 8px 0 2px 0; font-size: 1.8rem; font-weight: 800; color: {text_color};">72.0%</h3>
                <span style="color: #10B981; font-size: 0.75rem; font-weight: 600;">▲ 0.8% positive</span>
            </div>
        </div>
    """), unsafe_allow_html=True)

    # Render Second Row using st.columns to allow embedding the plotly sparkline
    r2_col1, r2_col2, r2_col3 = st.columns(3)
    
    with r2_col1:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 16px; text-align: center; display: flex; flex-direction: column; justify-content: center; height: 140px;">
            <span style="font-size: 0.75rem; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">🗣️ Share of Voice</span>
            <h3 style="margin: 8px 0 2px 0; font-size: 1.8rem; font-weight: 800; color: {text_color};">{sov_val:.1f}%</h3>
            <span style="color: #64748B; font-size: 0.75rem; font-weight: 500;">{sov_subtext}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with r2_col2:
        # Card header and text metrics
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 12px 16px; height: 140px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <span style="font-size: 0.7rem; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; display: block; text-align: center;">🚀 AI Momentum</span>
                <div style="display: flex; align-items: baseline; justify-content: center; gap: 6px; margin-top: 4px;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: {text_color};">{momentum_val:+.0f}</span>
                    <span style="font-size: 0.75rem; font-weight: 700; color: {momentum_color};">{momentum_arrow} ({acceleration})</span>
                </div>
            </div>
            <div id="sparkline-wrapper" style="height: 45px; margin-bottom: 2px;">
        """, unsafe_allow_html=True)
        # Render inline sparkline
        st.plotly_chart(render_momentum_sparkline(historical_data), use_container_width=True, key="momentum_sparkline", config={'staticPlot': True, 'displayModeBar': False})
        st.markdown("</div></div>", unsafe_allow_html=True)
        
    with r2_col3:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 12px 16px; height: 140px; display: flex; flex-direction: column; justify-content: space-between; text-align: center;">
            <div>
                <span style="font-size: 0.7rem; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">📉 AI Trust Gap</span>
                <h3 style="margin: 4px 0 2px 0; font-size: 1.5rem; font-weight: 800; color: {text_color};">{gap_details['gap_value']} pts</h3>
                <span style="color: #EF4444; font-size: 0.7rem; font-weight: 600;">Gap to {gap_details['leader_name']} ({gap_details['leader_score']})</span>
            </div>
            <div style="font-size: 0.7rem; color: {label_color}; border-top: 1px solid {row_border}; padding-top: 4px; margin-top: 4px;">
                Top Gap: <strong>{top_gap_dim.title()} (+{top_gap_val})</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Render platform ranks in a beautiful standalone inline marquee card
    st.markdown(clean_html(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 10px 16px; margin-bottom: 24px; text-align: center;">
            <span style="font-size: 0.7rem; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; margin-right: 10px;">🏆 AI Ranks:</span>
            <span style="font-size: 0.75rem; color: {text_color}; font-weight: 600;">{rank_inline_text}</span>
        </div>
    """), unsafe_allow_html=True)
    
    # Build list of platforms and scores
    # If we have real results from multi_model, we can use them, otherwise we fallback to high-fidelity mocks
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
    
    # Try mapping from real results if available to keep it accurate
    if multi_model_results and "results" in multi_model_results:
        results_list = multi_model_results["results"]
        mapped_platforms = []
        for r in results_list:
            model_name = r.get("model", "")
            confidence = int(r.get("confidence", 0) * 100) if r.get("mentioned") else int(r.get("confidence", 0.25) * 100)
            mapped_platforms.append({"name": model_name, "score": confidence})
            
        # Add some other key engines if they aren't returned
        existing_names = {p["name"].lower() for p in mapped_platforms}
        for p in platforms:
            if p["name"].lower() not in existing_names:
                mapped_platforms.append(p)
                
        platforms = sorted(mapped_platforms, key=lambda x: x["score"], reverse=True)
        
    st.markdown("#### 🌐 Platform Visibility Breakdown")
    
    # Render Platform Items
    for p in platforms:
        score = p["score"]
        if score >= 75:
            color = "#10B981"  # Green
            indicator = "🟢"
        elif score >= 50:
            color = "#F59E0B"  # Yellow
            indicator = "🟡"
        else:
            color = "#EF4444"  # Red
            indicator = "🔴"
            
        st.markdown(clean_html(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: {row_bg}; border: 1px solid {row_border}; border-radius: 8px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; width: 220px;">
                    <span style="font-size: 0.9rem;">{indicator}</span>
                    <span style="font-size: 0.9rem; font-weight: 600; color: {text_color};">{p['name']}</span>
                </div>
                <div style="flex-grow: 1; margin: 0 20px; background-color: rgba(0, 0, 0, 0.05) if not is_dark else rgba(255, 255, 255, 0.05); border-radius: 9999px; height: 8px; overflow: hidden;">
                    <div style="height: 100%; width: {score}%; background: {color}; border-radius: 9999px;"></div>
                </div>
                <div style="width: 50px; text-align: right;">
                    <span style="font-size: 0.9rem; font-weight: 700; color: {color};">{score}%</span>
                </div>
            </div>
        """), unsafe_allow_html=True)
        
    # Info footer
    st.markdown(clean_html(f"""
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: {label_color}; margin-top: 15px; border-top: 1px solid {row_border}; padding-top: 10px;">
            <span>📊 1,597 mentions out of 2,663 total</span>
            <span>🔗 719 citations</span>
            <span>📱 10 platforms tracked</span>
        </div>
    """), unsafe_allow_html=True)
