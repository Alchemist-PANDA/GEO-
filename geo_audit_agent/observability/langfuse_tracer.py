"""Langfuse tracing. @trace_span wraps any node; falls back to no-op offline."""
from __future__ import annotations
import functools, os, time, uuid, logging

logger = logging.getLogger(__name__)
_client = None

def _lf():
    global _client
    if _client is not None:
        return _client
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return None
    try:
        from langfuse import Langfuse
        _client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception as e:
        logger.warning("Langfuse init failed: %s", e)
        _client = None
    return _client


def new_trace_id() -> str:
    return uuid.uuid4().hex


def trace_span(name: str, agent_id: str = "system"):
    """Decorator. Expects the wrapped fn to take an AgenticState-like object
    exposing `.trace_id`, `.tokens`, `.cost_usd` (optional)."""
    def deco(fn):
        @functools.wraps(fn)
        def wrap(state, *a, **kw):
            client = _lf()
            tid = getattr(state, "trace_id", None) or new_trace_id()
            if hasattr(state, "trace_id"):
                state.trace_id = tid
            t0 = time.time()
            span = None
            if client:
                try:
                    span = client.span(name=name, trace_id=tid,
                                       metadata={"agent_id": agent_id})
                except Exception:
                    span = None
            try:
                result = fn(state, *a, **kw)
                return result
            finally:
                dur = time.time() - t0
                if span:
                    try:
                        span.end(metadata={
                            "duration_s": round(dur, 3),
                            "tokens": getattr(state, "tokens", 0),
                            "cost_usd": getattr(state, "cost_usd", 0.0),
                        })
                    except Exception:
                        pass
                # Always emit a Prometheus duration sample (see §18)
                try:
                    from geo_audit_agent.observability.metrics import AGENT_NODE_DURATION
                    AGENT_NODE_DURATION.labels(node=name, agent=agent_id).observe(dur)
                except Exception:
                    pass
        return wrap
    return deco
