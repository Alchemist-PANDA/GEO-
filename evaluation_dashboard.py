# evaluation_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Mock data generator simulating evaluation and cache logs
def generate_metric_logs():
    np.random.seed(42)
    dates = [datetime.utcnow() - timedelta(days=i) for i in range(30, 0, -1)]
    
    # G-Eval faithfulness scores (0.0 to 5.0) with custom regression drop on Day 20
    geval_scores = np.random.uniform(4.2, 4.8, size=30)
    geval_scores[20:25] = geval_scores[20:25] - 0.9  # Mock prompt modification error
    
    # Caching hit rate (percentage 0 to 100)
    cache_hit_rates = np.random.uniform(75, 92, size=30)
    cache_hit_rates[10:15] = cache_hit_rates[10:15] - 40 # Dynamic variable injection error
    
    # Latencies (p95 milliseconds)
    p95_latencies = np.random.uniform(1200, 1800, size=30)
    p95_latencies[10:15] = p95_latencies[10:15] + 2500  # Caching failure latency increase
    
    df = pd.DataFrame({
        "Date": dates,
        "G_Eval_Score": geval_scores,
        "Cache_Hit_Rate": cache_hit_rates,
        "Latency_p95_ms": p95_latencies
    })
    return df

st.set_page_config(page_title="GEO System Evaluation Dashboard", layout="wide")

st.title("📊 BrandSight GEO: Cognitive Systems Evaluation Dashboard")
st.markdown("Monitor rolling G-Eval scores, prompt caching metrics, p95 execution latencies, and active semantic drift alerts.")

df = generate_metric_logs()

# Primary metrics rows
col1, col2, col3 = st.columns(3)

latest = df.iloc[-1]
avg_geval = df["G_Eval_Score"].mean()
avg_cache = df["Cache_Hit_Rate"].mean()

with col1:
    st.metric(
        label="Rolling G-Eval Faithfulness (1-5)",
        value=f"{latest['G_Eval_Score']:.2f}",
        delta=f"{(latest['G_Eval_Score'] - avg_geval):.2f} vs Avg"
    )
with col2:
    st.metric(
        label="Prompt Cache Hit Rate",
        value=f"{latest['Cache_Hit_Rate']:.1f}%",
        delta=f"{(latest['Cache_Hit_Rate'] - avg_cache):.1f}% vs Avg"
    )
with col3:
    st.metric(
        label="p95 Latency (ms)",
        value=f"{int(latest['Latency_p95_ms'])} ms",
        delta=f"{int(latest['Latency_p95_ms'] - df['Latency_p95_ms'].mean())} ms"
    )

st.divider()

# Alert center for drift detection
st.subheader("🚨 Safety and Drift Alert Center")
drift_detected = df["G_Eval_Score"].rolling(window=5).mean().iloc[-1] < 4.0
cache_warning = df["Cache_Hit_Rate"].iloc[-1] < 60.0

if drift_detected:
    st.error("⚠️ **Systemic Accuracy Drift Flagged**: The 5-day rolling average G-Eval score has fallen below the 4.0 threshold. Review recent prompt updates.")
if cache_warning:
    st.warning("⚠️ **Prompt Caching Degradation Alert**: Prompt cache hit rate dropped below 60%. Check for dynamic timestamp variables invalidating headers.")
if not drift_detected and not cache_warning:
    st.success("✅ All system metrics are within normal operational limits. No drift detected.")

# Layout charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.write("### Rolling G-Eval Quality Trend")
    fig_geval = go.Figure()
    fig_geval.add_trace(go.Scatter(x=df["Date"], y=df["G_Eval_Score"], mode="lines+markers", name="G-Eval Score", line=dict(color="#3b82f6", width=3)))
    fig_geval.add_trace(go.Scatter(x=df["Date"], y=[4.0]*30, mode="lines", name="Target Gate", line=dict(color="red", dash="dash")))
    fig_geval.update_layout(yaxis=dict(range=[1.0, 5.0]), margin=dict(l=20, r=20, t=20, b=20), height=350)
    st.plotly_chart(fig_geval, use_container_width=True)

with chart_col2:
    st.write("### Prompt Cache Hit Rates & Latency Correlation")
    fig_cache = go.Figure()
    fig_cache.add_trace(go.Bar(x=df["Date"], y=df["Cache_Hit_Rate"], name="Cache Hit %", marker_color="#10b981"))
    fig_cache.update_layout(yaxis=dict(range=[0, 100]), margin=dict(l=20, r=20, t=20, b=20), height=350)
    st.plotly_chart(fig_cache, use_container_width=True)
