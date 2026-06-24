from prometheus_client import Counter, Histogram, Gauge, Info

AUDIT_REQUESTS = Counter(
    "geo_audit_requests_total",
    "Total audit requests",
    ["tier", "status"],
)

AUDIT_DURATION = Histogram(
    "geo_audit_duration_seconds",
    "Audit pipeline execution duration",
    ["tier"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

LLM_REQUESTS = Counter(
    "geo_llm_requests_total",
    "Total LLM provider requests",
    ["provider", "model", "cache_hit"],
)

LLM_LATENCY = Histogram(
    "geo_llm_latency_seconds",
    "LLM request latency",
    ["provider"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

LLM_TOKENS = Counter(
    "geo_llm_tokens_total",
    "Total LLM tokens consumed",
    ["provider", "direction"],  # direction: input/output
)

LLM_COST = Counter(
    "geo_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["provider", "tier"],
)

GUARDRAIL_EVENTS = Counter(
    "geo_guardrail_events_total",
    "Guardrail classification events",
    ["classification"],  # safe/unsafe
)

CACHE_OPERATIONS = Counter(
    "geo_cache_operations_total",
    "Cache hit/miss events",
    ["operation"],  # hit/miss/error
)

ACTIVE_AUDITS = Gauge(
    "geo_active_audits",
    "Currently running audits",
)

VALIDATION_REPAIRS = Counter(
    "geo_validation_repairs_total",
    "Output validation repair attempts",
    ["result"],  # success/failure
)

BUILD_INFO = Info(
    "geo_build",
    "Build information",
)
