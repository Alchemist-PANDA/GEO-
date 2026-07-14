"""Operational evaluation dashboard backed by exported telemetry."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="BrandSight Evaluation", layout="wide")
st.title("System evaluation")
st.caption("Observed quality, cache, and latency telemetry")

source = Path(os.getenv("EVALUATION_METRICS_FILE", "data/evaluation_metrics.jsonl"))
if not source.exists():
    st.info(
        "No evaluation telemetry has been exported. Set EVALUATION_METRICS_FILE to a JSONL file containing "
        "timestamp, faithfulness_score, cache_hit, and latency_ms. No sample telemetry is generated."
    )
    st.stop()

rows = []
for line in source.read_text(encoding="utf-8").splitlines():
    if line.strip():
        rows.append(json.loads(line))
if not rows:
    st.warning("The telemetry file is empty. Metrics are unavailable.")
    st.stop()

frame = pd.DataFrame(rows)
required = {"timestamp", "faithfulness_score", "cache_hit", "latency_ms"}
missing = required - set(frame.columns)
if missing:
    st.error("Telemetry schema is missing: " + ", ".join(sorted(missing)))
    st.stop()

frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
frame = frame.sort_values("timestamp")
cols = st.columns(3)
cols[0].metric("Mean faithfulness", f"{frame['faithfulness_score'].mean():.2f}")
cols[0].caption(f"n={len(frame)}")
cols[1].metric("Cache hit rate", f"{frame['cache_hit'].astype(bool).mean():.1%}")
cols[1].caption(f"{frame['cache_hit'].astype(bool).sum()} / {len(frame)}")
cols[2].metric("p95 latency", f"{frame['latency_ms'].quantile(0.95):.0f} ms")
cols[2].caption(f"n={len(frame)}")
st.line_chart(frame.set_index("timestamp")[["faithfulness_score", "latency_ms"]])
