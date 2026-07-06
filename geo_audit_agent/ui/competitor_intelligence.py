import streamlit as st
import plotly.graph_objects as go

from geo_audit_agent.ui.chart_wrapper import render_chart_with_copilot


def render_competitor_intelligence(competitor_data):
    """Render the Competitor Intelligence dashboard tab with formatted UI cards."""
    if not competitor_data:
        st.info("Run an audit to generate competitor intelligence data.")
        return

    brand_name = competitor_data.get("brand", "Your Brand")
    brand_scores = competitor_data.get("brand_scores", {})
    competitors = competitor_data.get("competitors", [])
    summary = competitor_data.get("summary", {})

    # Summary KPI row
    rank = summary.get("brand_rank", "-")
    total = summary.get("total_competitors", 0)
    opportunity = summary.get("top_opportunity", "N/A")

    st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px;">
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">🏆 Brand Rank</div>
                <div class="bv2-metric-value">#{rank}</div>
                <div style="color: #64748B; font-size: 0.85rem;">out of {total + 1} brands</div>
            </div>
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">📊 GEO Score</div>
                <div class="bv2-metric-value">{brand_scores.get('geo_score', 0)}%</div>
                <div style="color: #64748B; font-size: 0.85rem;">your brand's AI visibility</div>
            </div>
            <div class="bv2-metric-card">
                <div class="bv2-metric-label">🎯 Top Opportunity</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #7C3AED; margin-top: 6px;">{opportunity}</div>
                <div style="color: #64748B; font-size: 0.85rem;">biggest gap vs competitors</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Radar chart comparison
    if competitors:
        st.markdown("#### 🕸️ Competitive Radar")
        metrics = ["GEO Score", "Citation Rate", "Content Depth", "Schema Coverage", "Platform Presence"]
        metric_keys = ["geo_score", "citation_rate", "content_depth", "schema_coverage", "platform_presence"]

        fig = go.Figure()

        brand_values = [brand_scores.get(k, 0) for k in metric_keys]
        fig.add_trace(go.Scatterpolar(
            r=brand_values + [brand_values[0]],
            theta=metrics + [metrics[0]],
            fill='toself',
            name=brand_name,
            line=dict(color='#7C3AED', width=3),
            fillcolor='rgba(124, 58, 237, 0.15)',
        ))

        colors = ['#3B82F6', '#10B981', '#F59E0B']
        for i, comp in enumerate(competitors[:3]):
            comp_scores = comp.get("scores", {})
            comp_values = [comp_scores.get(k, 0) for k in metric_keys]
            color = colors[i % len(colors)]
            fig.add_trace(go.Scatterpolar(
                r=comp_values + [comp_values[0]],
                theta=metrics + [metrics[0]],
                fill='toself',
                name=comp_scores.get("competitor", f"Competitor {i+1}"),
                line=dict(color=color, width=2),
                fillcolor=f"rgba({int(color[1:3],16)}, {int(color[3:5],16)}, {int(color[5:7],16)}, 0.05)",
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10, color="#64748B")),
                bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#1E293B"),
            height=400,
            margin=dict(l=60, r=60, t=40, b=40),
            showlegend=True,
            legend=dict(font=dict(size=12)),
        )
        render_chart_with_copilot(fig, "Competitive Radar", chart_data={"brand": brand_name, "competitors": [c.get("scores", {}).get("competitor") for c in competitors]}, key="competitive_radar")

    # Competitor cards
    st.markdown("#### 🏢 Competitor Breakdown")
    for comp in competitors:
        scores = comp.get("scores", {})
        explanations = comp.get("explanations", [])
        comp_name = scores.get("competitor", "Unknown")
        geo = scores.get("geo_score", 0)

        if geo >= 70:
            threat_color = "#EF4444"
            threat_label = "High Threat"
        elif geo >= 50:
            threat_color = "#F59E0B"
            threat_label = "Moderate"
        else:
            threat_color = "#10B981"
            threat_label = "Low Threat"

        with st.container(border=True):
            st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <h4 style="margin: 0 0 4px 0; font-weight: 700; color: #1E293B;">{comp_name}</h4>
                        <span style="font-size: 0.8rem; color: #64748B;">GEO Score: <strong style="color: #7C3AED;">{geo}%</strong></span>
                    </div>
                    <span style="background-color: {threat_color}15; color: {threat_color}; padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; border: 1px solid {threat_color}30;">{threat_label}</span>
                </div>
            """, unsafe_allow_html=True)

            score_cols = st.columns(4)
            score_items = [
                ("📝 Citation", scores.get("citation_rate", 0)),
                ("📚 Content", scores.get("content_depth", 0)),
                ("🔗 Schema", scores.get("schema_coverage", 0)),
                ("📱 Platforms", scores.get("platform_presence", 0)),
            ]
            for col, (label, val) in zip(score_cols, score_items):
                with col:
                    color = "#10B981" if val >= 70 else "#F59E0B" if val >= 50 else "#EF4444"
                    st.markdown(f"""
                        <div style="text-align: center; padding: 8px; background: rgba(124, 58, 237, 0.03); border-radius: 8px;">
                            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 4px;">{label}</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: {color};">{val}%</div>
                        </div>
                    """, unsafe_allow_html=True)

            if explanations:
                with st.expander("💡 Insights & Recommendations"):
                    for exp in explanations:
                        st.markdown(f"**{exp['area']}**: {exp['insight']}")
                        st.caption(f"→ {exp['recommendation']}")
