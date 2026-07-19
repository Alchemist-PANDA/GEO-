import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from geo_audit_agent.api.rate_limiter import RateLimitMiddleware, RedisRateLimiter
from geo_audit_agent.api.routes import agentic, audits, brands, competitors, copilot, feedback, health, stream
from geo_audit_agent.api.security_headers import MetricsAuthMiddleware, SecurityHeadersMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BrandSight GEO API",
    version="3.0.0",
    description="Generative Engine Optimization platform API",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.brandsightgeo.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, limiter=RedisRateLimiter(limit=100, window=3600))
# Security headers on every response; /metrics gated by METRICS_TOKEN if set.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsAuthMiddleware)

app.include_router(health.router, tags=["Health"])
app.include_router(brands.router, prefix="/v1", tags=["Brands"])
app.include_router(audits.router, prefix="/v1", tags=["Audits"])
app.include_router(feedback.router, prefix="/v1", tags=["Feedback"])
app.include_router(competitors.router, prefix="/v1", tags=["Competitors"])
app.include_router(stream.router, prefix="/v1", tags=["Streaming"])
app.include_router(agentic.router, prefix="/v1", tags=["Agentic"])
app.include_router(copilot.router, prefix="/v1", tags=["Copilot"])

try:
    from prometheus_client import make_asgi_app
    app.mount("/metrics", make_asgi_app())
except ImportError:
    logger.warning("prometheus_client not installed; /metrics endpoint disabled")
