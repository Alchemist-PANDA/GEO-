import streamlit as st
import plotly.graph_objects as go

def render_lift_simulator(current_score, gaps):
    """Render the interactive strategic lift simulator with checklist and progression line chart."""
    if not gaps:
        st.success("Your brand performance is already optimized for Generative Search.")
        return
        
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.25rem;">📈 Strategic Lift Simulator</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 0; margin-bottom: 20px;">
                Simulate your projected GEO score lift by selecting which remediations to prioritize.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col_controls, col_visual = st.columns([1.2, 1])
    
    with col_controls:
        st.markdown("#### Remediation Roadmap")
        st.write("Toggle the items you plan to implement:")
        
        fixed_gaps = []
        for i, gap in enumerate(gaps):
            with st.container(border=True):
                c_check, c_label = st.columns([1, 8])
                with c_check:
                    # Align checkbox beautifully
                    is_checked = st.checkbox("", key=f"sim_check_{i}")
                    if is_checked:
                        fixed_gaps.append(gap)
                with c_label:
                    sev = gap.get('severity', 'Medium').title()
                    color = {"Critical": "#EF4444", "High": "#F59E0B", "Medium": "#3B82F6", "Low": "#10B981"}.get(sev, "#9CA3AF")
                    st.markdown(f"**{gap.get('gap_type', 'General Gap')}** <span style='font-size: 0.75rem; color: {color}; font-weight: 600;'>({sev})</span>", unsafe_allow_html=True)
                    st.caption(gap.get('description', ''))
                    
    with col_visual:
        # Calculate simulation score progression
        severity_weights = {"Critical": 0.15, "High": 0.10, "Medium": 0.05, "Low": 0.02}
        
        # Step-by-step progress list
        steps = ["Current"]
        scores = [current_score * 100]
        
        temp_score = current_score
        for gap in fixed_gaps:
            weight = severity_weights.get(gap.get('severity', 'Medium').title(), 0.05)
            # Diminishing returns factor
            lift = weight * (1.0 - temp_score)
            temp_score = min(1.0, temp_score + lift)
            steps.append(gap.get('gap_type', 'Fix'))
            scores.append(temp_score * 100)
            
        # Target representation (if all remaining gaps were fixed)
        all_remaining = [g for g in gaps if g not in fixed_gaps]
        for gap in all_remaining:
            weight = severity_weights.get(gap.get('severity', 'Medium').title(), 0.05)
            lift = weight * (1.0 - temp_score)
            temp_score = min(1.0, temp_score + lift)
        
        steps.append("Target (100% Fix)")
        scores.append(temp_score * 100)
        
        # Plotly Line Chart
        fig = go.Figure()
        
        # Line Path
        fig.add_trace(go.Scatter(
            x=steps,
            y=scores,
            mode='lines+markers+text',
            text=[f"{s:.0f}%" for s in scores],
            textposition="top center",
            line=dict(color='#7C3AED', width=4, shape='spline'),
            marker=dict(size=10, color='#3B82F6', line=dict(color='#FFFFFF', width=2)),
            fill='tozeroy',
            fillcolor='rgba(124, 58, 237, 0.08)'
        ))
        
        # Style details
        is_dark = st.session_state.get("theme", "Dark") == "Dark"
        bg_color = "rgba(0,0,0,0)"
        text_color = "#FFFFFF" if is_dark else "#0A0A0F"
        grid_color = "rgba(255, 255, 255, 0.06)" if is_dark else "rgba(0, 0, 0, 0.06)"
        
        fig.update_layout(
            height=280,
            margin=dict(l=40, r=40, t=30, b=30),
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font=dict(color=text_color, family="Inter"),
            xaxis=dict(
                gridcolor='rgba(0,0,0,0)',
                tickfont=dict(size=10, color="#94A3B8")
            ),
            yaxis=dict(
                gridcolor=grid_color,
                range=[0, 110],
                tickfont=dict(size=10, color="#94A3B8"),
                title=dict(text="Projected Score (%)", font=dict(size=11, color="#94A3B8"))
            ),

            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Summary metrics
        final_lift = scores[-2] - scores[0] if len(scores) > 1 else 0
        
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.metric("Current", f"{scores[0]:.0f}%")
        with s_col2:
            st.metric("Projected", f"{scores[-2]:.0f}%", delta=f"+{final_lift:.1f}%" if final_lift > 0 else None)
            
        if final_lift > 0:
            st.success(f"🎯 **Growth Opportunity:** Implementing these selected fixes yields a **+{final_lift:.1f}% lift** in brand presence!")
        else:
            st.info("Select one or more gaps on the left to simulate the lift projection.")
