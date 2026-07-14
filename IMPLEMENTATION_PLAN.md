# BrandSight GEO — Complete Implementation Plan

**Version**: 4.0 — Unified Agent Edition
**Generated**: 2026-06-25
**Status**: Production-Ready Engineering Blueprint

---

## 1. Executive Summary

### Current State Assessment

BrandSight GEO has a functional prototype with:
- A working LangGraph-based audit pipeline (`geo_audit_agent/agent/graph.py`) with 8 nodes (guardrail → query_llm → check_citation → gap_analyst → planner → remediation_handler → validate_output → generate_report).
- A Streamlit dashboard (`dashboard.py`) with 7 tabs (Overview, Gap Analysis, Remediation Hub, What-If Simulator, Compare & Benchmark, Keyword Monitoring, Brand Visibility).
- Dual LLM routing via Google Gemini (primary) and a proxy fallback (`llm_router.py`, `llm_client.py`).
- Redis caching with in-memory fallback (`services/cache.py`).
- SQLModel ORM schema for `user_profiles`, `brands`, `audits` (`db/models.py`).
- Industry templates for restaurant, dental, fitness, ecommerce.
- Simulated multi-model audit (`multi_model.py`) covering ChatGPT, Gemini, Meta.ai, Claude.ai, DeepSeek.

### What Needs to Be Built

The Unified Competitor Intelligence Agent (Module 2) is the flagship feature. It requires:
1. Competitor discovery (LLM + SerpAPI)
2. Async website crawling (Playwright + ScraperAPI)
3. Multi-dimensional scoring (Authority, Schema, Content, Reviews, Entities, Citations, Brand)
4. AI-powered intelligence generation (why competitors win)
5. Executive summaries with actionable recommendations

### Recommended Approach

Build incrementally on top of the existing LangGraph infrastructure. Don't replace what works — extend it. Ship in 4 phases over 12 weeks, with a usable MVP by Week 4.

---

## 2. Encyclopedia Alignment Scorecard

| Principle | Score | Commentary |
|-----------|-------|------------|
| **Agent-OS Pattern** | 6/10 | LangGraph graph exists and works. Missing: agent registry, inter-agent communication, lifecycle management. The unified agent approach sidesteps multi-agent complexity, which is correct for this stage. |
| **12-Factor Agents** | 5/10 | Good: config via env vars, stateless LLM calls, in-memory fallbacks. Missing: structured logging (using basic `logging`), no correlation IDs end-to-end, no proper health checks, no graceful shutdown, no idempotent task execution. |
| **AI Design Patterns** | 7/10 | Strong: LangGraph DAG with conditional routing, retry/repair loop (max 3 attempts), guardrail node at entry. Missing: human-in-the-loop breakpoints, streaming output, tool-use pattern for crawling. |
| **Principal Engineer** | 4/10 | The prototype works but lacks production topology: no circuit breakers, no backpressure, no rate limiting, no resource isolation between tenants. Normal for this stage. |
| **PEAS Framework** | 6/10 | Performance: GEO score measured. Environment: partially observable (simulated mode works, live mode depends on API availability). Actuators: generates reports and remediations. Sensors: basic (LLM response + citation check). Missing: competitor change detection sensors, market signal sensors. |

### Key Gaps (Priority Order)

1. **No competitor crawling infrastructure** — the entire Module 2 pipeline is missing.
2. **No async task execution** — Celery is in `requirements.txt` but not wired up. Long-running crawls will block Streamlit.
3. **No tenant isolation** — single-user prototype; `user_id` is in the schema but not enforced.
4. **No structured observability** — `logging.info()` scattered, no metrics, no tracing.
5. **No API layer for competitor intelligence** — FastAPI exists in requirements but isn't serving competitor endpoints.

---

## 3. Gap Analysis

| Gap | Severity | Recommendation | Effort |
|-----|----------|----------------|--------|
| No competitor discovery | **Critical** | Build `discover_competitors()` using Gemini + SerpAPI | 1 week |
| No website crawler | **Critical** | Build async Playwright crawler with ScraperAPI proxy | 1 week |
| No competitor scoring | **Critical** | Build analyzer using existing `audit.py` patterns | 1 week |
| No intelligence generation | **High** | LLM-powered explanation pipeline | 1 week |
| No background task runner | **High** | Wire up Celery + Redis (already in deps) | 3 days |
| No competitor DB tables | **High** | Add SQLModel models + Alembic migration | 2 days |
| No API endpoints | **Medium** | FastAPI routes for competitor CRUD + analysis | 3 days |
| No rate limiting | **Medium** | Token bucket per user/API | 2 days |
| No correlation IDs | **Medium** | UUID per request, propagate through pipeline | 1 day |
| No health checks | **Low** | `/health` endpoint with dependency checks | 0.5 day |
| No streaming output | **Low** | SSE for long-running analysis progress | 1 week |

---

## 4. Refined Architecture

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │  Streamlit    │    │  FastAPI      │    │  Celery Beat         │   │
│  │  Dashboard    │───▶│  Gateway      │    │  Scheduler           │   │
│  │  (7 tabs)     │    │  /api/v1/*    │    │  (weekly/daily)      │   │
│  └──────────────┘    └──────┬───────┘    └──────────┬───────────┘   │
│                              │                       │               │
├──────────────────────────────┼───────────────────────┼───────────────┤
│                        TASK QUEUE                    │               │
│                     ┌────────▼───────┐               │               │
│                     │  Redis Queue   │◀──────────────┘               │
│                     │  (Celery)      │                               │
│                     └────────┬───────┘                               │
│                              │                                       │
├──────────────────────────────┼───────────────────────────────────────┤
│                     UNIFIED AGENT                                    │
│  ┌───────────────────────────▼──────────────────────────────────┐   │
│  │  UnifiedCompetitorIntelligenceAgent                          │   │
│  │                                                               │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌───────┐ │   │
│  │  │Discover│─▶│ Crawl  │─▶│Analyze │─▶│ Intel  │─▶│Summary│ │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘  └───────┘ │   │
│  │       │           │           │           │           │      │   │
│  │       ▼           ▼           ▼           ▼           ▼      │   │
│  │   SerpAPI    Playwright   Scoring     Gemini LLM   Gemini   │   │
│  │   + LLM      + Scraper    Engine                    LLM     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
├──────────────────────────────┼───────────────────────────────────────┤
│                        DATA LAYER                                    │
│  ┌──────────┐    ┌───────────┐    ┌────────────┐                    │
│  │PostgreSQL│    │  Redis     │    │ S3 / Local │                    │
│  │(SQLModel)│    │  Cache     │    │  Storage   │                    │
│  └──────────┘    └───────────┘    └────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow

```
User clicks "Analyze Competitors"
  │
  ▼
FastAPI receives POST /api/v1/competitors/analyze
  │
  ▼
Celery task queued (returns task_id immediately)
  │
  ▼
Worker picks up task, instantiates UnifiedCompetitorIntelligenceAgent
  │
  ├─1─▶ discover_competitors(brand, category, city)
  │      └── Gemini: "List top 10 {category} brands in {city}"
  │      └── SerpAPI: validate discovered brands have websites
  │      └── Returns: [{name, website, source}]
  │
  ├─2─▶ crawl_websites(competitors)  [async, parallel]
  │      └── For each competitor:
  │          ├── Playwright: render JS, extract DOM
  │          ├── ScraperAPI: proxy for blocked sites
  │          ├── BeautifulSoup: parse HTML
  │          └── Extruct: extract structured data (JSON-LD, microdata)
  │      └── Returns: [{url, html, structured_data, meta, status}]
  │
  ├─3─▶ analyze_competitors(crawl_data)
  │      └── For each competitor:
  │          ├── Authority score (backlinks via Moz/Ahrefs API or estimation)
  │          ├── Schema score (JSON-LD completeness)
  │          ├── Content score (page count, FAQ presence, landing pages)
  │          ├── Review score (aggregate from Google/Yelp)
  │          ├── Entity score (named entities, knowledge graph)
  │          ├── Citation score (cross-reference with AI responses)
  │          └── Brand score (social presence, domain age)
  │      └── Returns: [{competitor, scores, details}]
  │
  ├─4─▶ generate_intelligence(scores, user_brand)
  │      └── Gemini: "Given these scores, explain why {competitor}
  │          is outperforming {user_brand} in AI visibility"
  │      └── Returns: [{competitor, explanation, strategy}]
  │
  └─5─▶ generate_summaries(intelligence)
         └── Gemini: "Produce an executive summary for {user_brand}"
         └── Returns: {leaderboard, insights, recommendations, projected_growth}
  │
  ▼
Results stored in PostgreSQL (competitor_scans, competitor_scores, competitor_explanations)
  │
  ▼
Dashboard polls task status, renders results when complete
```

---

## 5. Detailed Implementation Plan

### 5.1 Database Schema — New Tables

Add these to `geo_audit_agent/db/models.py`:

```python
# geo_audit_agent/db/models.py — append after existing models

class Competitor(SQLModel, table=True):
    __tablename__ = "competitors"
    __table_args__ = (
        Index("idx_competitors_brand_id", "brand_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brands.id", index=True)
    name: str = Field(max_length=255)
    website: Optional[str] = Field(default=None, max_length=500)
    category: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    is_auto_discovered: bool = Field(default=True)
    added_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CompetitorScan(SQLModel, table=True):
    __tablename__ = "competitor_scans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    competitor_id: uuid.UUID = Field(foreign_key="competitors.id", index=True)
    scan_type: str = Field(default="weekly", max_length=20)
    status: str = Field(default="pending", max_length=20)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    crawl_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn("crawl_data", JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CompetitorScore(SQLModel, table=True):
    __tablename__ = "competitor_scores"
    __table_args__ = (
        Index("idx_scores_competitor_scan", "competitor_id", "scan_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    competitor_id: uuid.UUID = Field(foreign_key="competitors.id", index=True)
    scan_id: uuid.UUID = Field(foreign_key="competitor_scans.id", index=True)
    dimension: str = Field(max_length=50)  # authority, schema, content, reviews, entities, citations, brand
    score: float = Field(default=0.0)
    details: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn("details", JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CompetitorExplanation(SQLModel, table=True):
    __tablename__ = "competitor_explanations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    competitor_id: uuid.UUID = Field(foreign_key="competitors.id", index=True)
    scan_id: uuid.UUID = Field(foreign_key="competitor_scans.id", index=True)
    explanation_type: str = Field(max_length=50)  # winning_factors, strategy, summary
    content: str = ""
    confidence: float = Field(default=0.0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    competitor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="competitors.id")
    alert_type: str = Field(max_length=50)  # visibility_change, competitor_update, new_opportunity
    severity: str = Field(default="info", max_length=20)  # critical, high, medium, info
    message: str = ""
    is_read: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )
```

### Alembic Migration

```python
# alembic/versions/xxxx_add_competitor_tables.py

def upgrade():
    op.create_table(
        'competitors',
        sa.Column('id', sa.dialects.postgresql.UUID, primary_key=True),
        sa.Column('brand_id', sa.dialects.postgresql.UUID, sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('website', sa.String(500)),
        sa.Column('category', sa.String(100), server_default=''),
        sa.Column('city', sa.String(100), server_default=''),
        sa.Column('is_auto_discovered', sa.Boolean, server_default='true'),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('idx_competitors_brand_id', 'competitors', ['brand_id'])

    op.create_table(
        'competitor_scans',
        sa.Column('id', sa.dialects.postgresql.UUID, primary_key=True),
        sa.Column('competitor_id', sa.dialects.postgresql.UUID, sa.ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scan_type', sa.String(20), server_default='weekly'),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text),
        sa.Column('crawl_data', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        'competitor_scores',
        sa.Column('id', sa.dialects.postgresql.UUID, primary_key=True),
        sa.Column('competitor_id', sa.dialects.postgresql.UUID, sa.ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scan_id', sa.dialects.postgresql.UUID, sa.ForeignKey('competitor_scans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dimension', sa.String(50), nullable=False),
        sa.Column('score', sa.Float, server_default='0'),
        sa.Column('details', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('idx_scores_competitor_scan', 'competitor_scores', ['competitor_id', 'scan_id'])

    op.create_table(
        'competitor_explanations',
        sa.Column('id', sa.dialects.postgresql.UUID, primary_key=True),
        sa.Column('competitor_id', sa.dialects.postgresql.UUID, sa.ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scan_id', sa.dialects.postgresql.UUID, sa.ForeignKey('competitor_scans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('explanation_type', sa.String(50)),
        sa.Column('content', sa.Text, server_default=''),
        sa.Column('confidence', sa.Float, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        'alerts',
        sa.Column('id', sa.dialects.postgresql.UUID, primary_key=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID, sa.ForeignKey('user_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('competitor_id', sa.dialects.postgresql.UUID, sa.ForeignKey('competitors.id')),
        sa.Column('alert_type', sa.String(50)),
        sa.Column('severity', sa.String(20), server_default='info'),
        sa.Column('message', sa.Text, server_default=''),
        sa.Column('is_read', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('idx_alerts_user_id', 'alerts', ['user_id'])


def downgrade():
    op.drop_table('alerts')
    op.drop_table('competitor_explanations')
    op.drop_table('competitor_scores')
    op.drop_table('competitor_scans')
    op.drop_table('competitors')
```

---

### 5.2 Unified Competitor Intelligence Agent

```python
# agents/unified_competitor_agent.py

import os
import json
import uuid
import asyncio
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class UnifiedCompetitorIntelligenceAgent:
    """
    Single-class agent that discovers, crawls, analyzes, and explains competitors.
    All five stages run in sequence within one async `run()` call.
    """

    DIMENSIONS = ["authority", "schema", "content", "reviews", "entities", "citations", "brand"]

    def __init__(self, llm_provider=None, scraper_api_key: str = None, serp_api_key: str = None):
        self.llm = llm_provider  # expects a callable(prompt: str) -> str
        self.scraper_api_key = scraper_api_key or os.getenv("SCRAPER_API_KEY", "")
        self.serp_api_key = serp_api_key or os.getenv("SERP_API_KEY", "")
        self.correlation_id = str(uuid.uuid4())[:8]

    # ── Stage 1: Discovery ─────────────────────────────────────────────

    async def discover_competitors(self, brand: str, category: str, city: str, limit: int = 10) -> List[Dict]:
        """Find competitors using LLM + optional SerpAPI validation."""
        logger.info(f"[{self.correlation_id}] Discovering competitors for {brand} in {category}/{city}")

        prompt = (
            f"List the top {limit} {category} brands/businesses in {city} that compete with {brand}. "
            f"Return ONLY a JSON array of objects with 'name' and 'website' keys. "
            f"Do not include {brand} itself. Example: "
            f'[{{"name": "Brand A", "website": "https://branda.com"}}]'
        )

        try:
            raw = self.llm(prompt) if self.llm else "[]"
            # Extract JSON array from response
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                competitors = json.loads(raw[start:end])
            else:
                competitors = []
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[{self.correlation_id}] LLM discovery parse error: {e}")
            competitors = []

        # Validate and normalize
        validated = []
        for c in competitors[:limit]:
            if isinstance(c, dict) and "name" in c:
                validated.append({
                    "name": c["name"],
                    "website": c.get("website", ""),
                    "source": "llm_discovery",
                    "discovered_at": datetime.utcnow().isoformat(),
                })

        # Optional: enrich with SerpAPI
        if self.serp_api_key and len(validated) < limit:
            serp_results = await self._serp_search(f"best {category} in {city}", limit - len(validated))
            for sr in serp_results:
                if sr["name"].lower() != brand.lower():
                    validated.append(sr)

        logger.info(f"[{self.correlation_id}] Discovered {len(validated)} competitors")
        return validated[:limit]

    async def _serp_search(self, query: str, limit: int) -> List[Dict]:
        """Search SerpAPI for additional competitor signals."""
        if not self.serp_api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={"q": query, "api_key": self.serp_api_key, "num": limit, "engine": "google"},
                )
                resp.raise_for_status()
                data = resp.json()
                results = []
                for r in data.get("organic_results", [])[:limit]:
                    results.append({
                        "name": r.get("title", "").split(" - ")[0].split(" | ")[0].strip(),
                        "website": r.get("link", ""),
                        "source": "serp_api",
                        "discovered_at": datetime.utcnow().isoformat(),
                    })
                return results
        except Exception as e:
            logger.warning(f"[{self.correlation_id}] SerpAPI search failed: {e}")
            return []

    # ── Stage 2: Crawling ──────────────────────────────────────────────

    async def crawl_website(self, url: str) -> Dict[str, Any]:
        """Crawl a single website. Falls back to ScraperAPI if direct fetch fails."""
        logger.info(f"[{self.correlation_id}] Crawling {url}")
        result = {"url": url, "status": "failed", "html": "", "structured_data": {}, "meta": {}}

        # Attempt 1: Direct httpx fetch (fast, free)
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "BrandSightBot/1.0"})
                if resp.status_code == 200:
                    result["html"] = resp.text[:500_000]  # cap at 500KB
                    result["status"] = "success"
                    result = self._parse_html(result)
                    return result
        except Exception as e:
            logger.debug(f"[{self.correlation_id}] Direct fetch failed for {url}: {e}")

        # Attempt 2: ScraperAPI proxy
        if self.scraper_api_key:
            try:
                proxy_url = f"http://api.scraperapi.com?api_key={self.scraper_api_key}&url={url}&render=true"
                async with httpx.AsyncClient(timeout=45) as client:
                    resp = await client.get(proxy_url)
                    if resp.status_code == 200:
                        result["html"] = resp.text[:500_000]
                        result["status"] = "success_via_proxy"
                        result = self._parse_html(result)
                        return result
            except Exception as e:
                logger.warning(f"[{self.correlation_id}] ScraperAPI failed for {url}: {e}")

        return result

    async def crawl_websites(self, competitors: List[Dict], concurrency: int = 5) -> List[Dict]:
        """Crawl multiple websites concurrently with bounded parallelism."""
        sem = asyncio.Semaphore(concurrency)

        async def _bounded_crawl(comp):
            async with sem:
                website = comp.get("website", "")
                if not website:
                    return {**comp, "crawl": {"url": "", "status": "no_url"}}
                crawl = await self.crawl_website(website)
                return {**comp, "crawl": crawl}

        tasks = [_bounded_crawl(c) for c in competitors]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def _parse_html(self, result: Dict) -> Dict:
        """Extract structured data and metadata from crawled HTML."""
        html = result.get("html", "")
        if not html:
            return result

        soup = BeautifulSoup(html, "html.parser")

        # Meta tags
        result["meta"] = {
            "title": (soup.title.string if soup.title else ""),
            "description": "",
            "canonical": "",
        }
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag:
            result["meta"]["description"] = desc_tag.get("content", "")
        canon_tag = soup.find("link", attrs={"rel": "canonical"})
        if canon_tag:
            result["meta"]["canonical"] = canon_tag.get("href", "")

        # Structured data (JSON-LD)
        json_ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        structured = []
        for script in json_ld_scripts:
            try:
                structured.append(json.loads(script.string))
            except (json.JSONDecodeError, TypeError):
                pass
        result["structured_data"] = {"json_ld": structured}

        # Page stats
        result["meta"]["h1_count"] = len(soup.find_all("h1"))
        result["meta"]["h2_count"] = len(soup.find_all("h2"))
        result["meta"]["link_count"] = len(soup.find_all("a"))
        result["meta"]["img_count"] = len(soup.find_all("img"))
        result["meta"]["word_count"] = len(soup.get_text(separator=" ").split())

        # FAQ detection
        faq_signals = soup.find_all(attrs={"itemtype": "https://schema.org/FAQPage"})
        faq_headings = [h for h in soup.find_all(["h2", "h3"]) if "faq" in (h.text or "").lower()]
        result["meta"]["has_faq"] = len(faq_signals) > 0 or len(faq_headings) > 0

        return result

    # ── Stage 3: Analysis ──────────────────────────────────────────────

    def analyze_competitor(self, competitor_data: Dict, external: Dict = None) -> Dict:
        """Compute multi-dimensional scores for a single competitor."""
        crawl = competitor_data.get("crawl", {})
        meta = crawl.get("meta", {})
        structured = crawl.get("structured_data", {})
        ext = external or {}

        scores = {}

        # Authority (0-100) — estimated from crawl signals + external data
        backlinks = ext.get("backlinks", 0)
        domain_authority = ext.get("domain_authority", 0)
        if domain_authority > 0:
            scores["authority"] = min(100, domain_authority)
        else:
            link_count = meta.get("link_count", 0)
            scores["authority"] = min(100, int(30 + (link_count / 10)))

        # Schema (0-100) — JSON-LD completeness
        json_ld = structured.get("json_ld", [])
        schema_types = set()
        for item in json_ld:
            if isinstance(item, dict):
                schema_types.add(item.get("@type", ""))
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, dict):
                        schema_types.add(sub.get("@type", ""))
        schema_types.discard("")
        scores["schema"] = min(100, len(schema_types) * 12)

        # Content (0-100)
        word_count = meta.get("word_count", 0)
        h_count = meta.get("h1_count", 0) + meta.get("h2_count", 0)
        has_faq = 1 if meta.get("has_faq") else 0
        scores["content"] = min(100, int((word_count / 50) + (h_count * 3) + (has_faq * 20)))

        # Reviews (0-100) — from external data
        review_count = ext.get("review_count", 0)
        avg_rating = ext.get("avg_rating", 0)
        if review_count > 0:
            scores["reviews"] = min(100, int((avg_rating / 5) * 60 + min(40, review_count / 25)))
        else:
            scores["reviews"] = 0

        # Entities (0-100) — named entity density from page text
        scores["entities"] = min(100, int(word_count / 30) + len(schema_types) * 5)

        # Citations (0-100) — from AI platform mentions (external data)
        ai_mentions = ext.get("ai_mention_count", 0)
        scores["citations"] = min(100, ai_mentions * 15)

        # Brand (0-100) — social signals + domain age
        social_profiles = ext.get("social_profile_count", 0)
        scores["brand"] = min(100, 20 + social_profiles * 10)

        # Overall score (weighted average)
        weights = {"authority": 0.20, "schema": 0.15, "content": 0.20, "reviews": 0.15,
                    "entities": 0.10, "citations": 0.10, "brand": 0.10}
        overall = sum(scores[d] * weights[d] for d in self.DIMENSIONS)

        return {
            "name": competitor_data.get("name", ""),
            "website": competitor_data.get("website", ""),
            "scores": scores,
            "overall": round(overall, 1),
            "meta": meta,
            "schema_types": list(schema_types),
        }

    # ── Stage 4: Intelligence ──────────────────────────────────────────

    def generate_intelligence(self, competitor: Dict, market_avg: Dict, user_brand: Dict) -> Dict:
        """Generate AI explanation of why this competitor is winning/losing."""
        name = competitor["name"]
        scores = competitor["scores"]
        user_scores = user_brand.get("scores", {})

        winning_dims = [d for d in self.DIMENSIONS if scores.get(d, 0) > user_scores.get(d, 0)]
        losing_dims = [d for d in self.DIMENSIONS if scores.get(d, 0) < user_scores.get(d, 0)]

        prompt = (
            f"You are a GEO (Generative Engine Optimization) expert. "
            f"Analyze why '{name}' (overall score: {competitor['overall']}%) "
            f"is {'outperforming' if competitor['overall'] > user_brand.get('overall', 0) else 'underperforming'} "
            f"'{user_brand.get('name', 'the user brand')}' (overall: {user_brand.get('overall', 0)}%).\n\n"
            f"Competitor scores: {json.dumps(scores)}\n"
            f"User brand scores: {json.dumps(user_scores)}\n"
            f"Market averages: {json.dumps(market_avg)}\n\n"
            f"Competitor wins on: {', '.join(winning_dims) or 'nothing'}\n"
            f"User wins on: {', '.join(losing_dims) or 'nothing'}\n\n"
            f"Provide:\n"
            f"1. Top 3 reasons for {name}'s performance (cite specific score differences)\n"
            f"2. One concrete strategy the user can implement to close the gap\n"
            f"3. Estimated effort (hours) and projected GEO score gain (%)\n\n"
            f"Be specific and actionable. Use numbers."
        )

        try:
            explanation = self.llm(prompt) if self.llm else f"{name} analysis unavailable — no LLM configured."
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Intelligence generation failed for {name}: {e}")
            explanation = f"Analysis for {name} could not be generated."

        return {
            "name": name,
            "overall": competitor["overall"],
            "winning_dimensions": winning_dims,
            "losing_dimensions": losing_dims,
            "explanation": explanation,
            "scores": scores,
        }

    # ── Stage 5: Summary ───────────────────────────────────────────────

    def generate_summary(self, all_intelligence: List[Dict], user_brand: Dict) -> str:
        """Produce an executive summary from all competitor intelligence."""
        leaderboard = sorted(all_intelligence, key=lambda x: x["overall"], reverse=True)
        top3 = leaderboard[:3]
        user_rank = 1
        for i, c in enumerate(leaderboard):
            if c["overall"] <= user_brand.get("overall", 0):
                user_rank = i + 1
                break
        else:
            user_rank = len(leaderboard) + 1

        prompt = (
            f"Generate an executive summary for '{user_brand.get('name', 'Brand')}' "
            f"who ranks #{user_rank} out of {len(leaderboard) + 1} competitors.\n\n"
            f"Top competitors:\n"
        )
        for c in top3:
            prompt += f"  - {c['name']}: {c['overall']}% (wins on {', '.join(c['winning_dimensions'])})\n"

        prompt += (
            f"\nUser brand overall: {user_brand.get('overall', 0)}%\n\n"
            f"Produce a 4-section summary:\n"
            f"1. MARKET POSITION — rank and comparison to leader\n"
            f"2. WHY LEADERS WIN — top 3 factors with numbers\n"
            f"3. HIGHEST ROI IMPROVEMENTS — 3 actions with effort + impact estimates\n"
            f"4. PROJECTED GROWTH — 30/60/90 day visibility projections\n"
        )

        try:
            return self.llm(prompt) if self.llm else "Executive summary unavailable — no LLM configured."
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Summary generation failed: {e}")
            return "Summary generation failed."

    # ── Orchestrator ───────────────────────────────────────────────────

    async def run(self, brand: str, category: str, city: str, limit: int = 10) -> Dict[str, Any]:
        """Full pipeline: discover → crawl → analyze → intelligence → summary."""
        logger.info(f"[{self.correlation_id}] Starting full competitor analysis for {brand}")
        start_time = datetime.utcnow()

        try:
            # 1. Discover
            competitors = await self.discover_competitors(brand, category, city, limit)
            if not competitors:
                return {"status": "no_competitors_found", "competitors": [], "summary": ""}

            # 2. Crawl (async, parallel)
            crawled = await self.crawl_websites(competitors)

            # 3. Analyze
            analyzed = [self.analyze_competitor(c) for c in crawled]
            market_avg = self._compute_market_avg(analyzed)

            # Analyze user brand (placeholder — in production, use their actual audit data)
            user_brand = {
                "name": brand,
                "overall": 0,
                "scores": {d: 0 for d in self.DIMENSIONS},
            }

            # 4. Intelligence
            intelligence = [self.generate_intelligence(a, market_avg, user_brand) for a in analyzed]

            # 5. Summary
            summary = self.generate_summary(intelligence, user_brand)

            # Build leaderboard
            leaderboard = sorted(analyzed, key=lambda x: x["overall"], reverse=True)

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"[{self.correlation_id}] Analysis complete in {elapsed:.1f}s")

            return {
                "status": "success",
                "correlation_id": self.correlation_id,
                "brand": brand,
                "category": category,
                "city": city,
                "competitors_found": len(competitors),
                "leaderboard": [{"rank": i + 1, "name": c["name"], "overall": c["overall"], "scores": c["scores"]}
                                for i, c in enumerate(leaderboard)],
                "intelligence": intelligence,
                "summary": summary,
                "market_avg": market_avg,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            logger.error(f"[{self.correlation_id}] Pipeline failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e), "correlation_id": self.correlation_id}

    def _compute_market_avg(self, analyzed: List[Dict]) -> Dict:
        if not analyzed:
            return {d: 0 for d in self.DIMENSIONS}
        avg = {}
        for d in self.DIMENSIONS:
            vals = [a["scores"].get(d, 0) for a in analyzed]
            avg[d] = round(sum(vals) / len(vals), 1) if vals else 0
        return avg
```

---

### 5.3 Celery Task Runner

```python
# geo_audit_agent/workers/tasks.py

import asyncio
import logging
from celery import Celery

logger = logging.getLogger(__name__)

app = Celery("brandsight", broker="redis://localhost:6379/0", backend="redis://localhost:6379/1")

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_time_limit=600,        # 10 min hard limit
    task_soft_time_limit=540,   # 9 min soft limit
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)


@app.task(bind=True, name="competitor_analysis")
def run_competitor_analysis(self, brand: str, category: str, city: str, limit: int = 10):
    """Celery task wrapper for the unified competitor agent."""
    from agents.unified_competitor_agent import UnifiedCompetitorIntelligenceAgent
    from geo_audit_agent.services.llm_router import query_provider

    def llm_call(prompt: str) -> str:
        resp = query_provider(prompt, tier="balanced", correlation_id=self.request.id or "")
        return resp.text

    agent = UnifiedCompetitorIntelligenceAgent(llm_provider=llm_call)
    result = asyncio.run(agent.run(brand, category, city, limit))
    return result


# Celery Beat schedule for recurring scans
app.conf.beat_schedule = {
    "weekly-competitor-scan": {
        "task": "competitor_analysis",
        "schedule": 604800.0,  # 7 days in seconds
        "args": [],  # populated per-brand from DB at runtime
    },
}
```

---

### 5.4 FastAPI Endpoints

```python
# geo_audit_agent/api/competitor_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/competitors", tags=["competitors"])


class DiscoverRequest(BaseModel):
    brand: str
    category: str
    city: str
    limit: int = 10


class AnalyzeResponse(BaseModel):
    task_id: str
    status: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_competitors(req: DiscoverRequest):
    """Kick off async competitor analysis. Returns task_id for polling."""
    from geo_audit_agent.workers.tasks import run_competitor_analysis

    task = run_competitor_analysis.delay(
        brand=req.brand,
        category=req.category,
        city=req.city,
        limit=req.limit,
    )
    return AnalyzeResponse(task_id=task.id, status="queued")


@router.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    """Poll task status."""
    from geo_audit_agent.workers.tasks import app as celery_app

    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif result.state == "STARTED":
        return {"task_id": task_id, "status": "running"}
    elif result.state == "SUCCESS":
        return {"task_id": task_id, "status": "complete", "result": result.result}
    elif result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(result.result)}
    return {"task_id": task_id, "status": result.state}


@router.get("/leaderboard/{brand}")
async def get_leaderboard(brand: str):
    """Get the latest leaderboard for a brand."""
    # In production: query PostgreSQL for latest competitor_scores
    return {"brand": brand, "leaderboard": [], "message": "Query DB for latest scan results"}
```

---

### 5.5 LLM Integration Strategy

| Task | Model | Why | Estimated Cost/Call |
|------|-------|-----|---------------------|
| Competitor discovery | `gemini-2.0-flash-lite` | Simple list generation, low cost | ~$0.0001 |
| Intelligence generation | `gemini-2.0-flash` | Needs reasoning about scores | ~$0.001 |
| Executive summary | `gemini-2.0-flash` | Structured output, reasoning | ~$0.001 |
| Schema/FAQ generation | `gemini-2.0-flash` | Code generation quality | ~$0.002 |

**Cost for 50 competitors/week**: ~$0.15/week in LLM calls (Gemini pricing).

### Caching Strategy

```
Cache Layer 1: Redis (TTL = 24h)
  - LLM responses keyed by (prompt_hash, model, temperature)
  - Crawl results keyed by (url, date)

Cache Layer 2: PostgreSQL (permanent)
  - Competitor scores (historical)
  - Explanations (per scan)

Cache Layer 3: In-memory (session)
  - Dashboard-computed aggregates
  - Leaderboard rankings
```

---

### 5.6 Dashboard Integration

Add the competitor analysis UI as a new Streamlit tab or integrate into the existing "Compare & Benchmark" tab:

```python
# In dashboard.py — inside the Compare tab or a new Competitors tab

if st.button("🔍 Auto-Discover Competitors"):
    with st.spinner("Discovering competitors..."):
        # For MVP: call agent synchronously (blocking but simple)
        # For production: use Celery task + polling
        from agents.unified_competitor_agent import UnifiedCompetitorIntelligenceAgent
        from geo_audit_agent.services.llm_router import query_provider

        def llm_call(prompt):
            return query_provider(prompt, tier="balanced").text

        agent = UnifiedCompetitorIntelligenceAgent(llm_provider=llm_call)
        result = asyncio.run(agent.run(brand_name, category, city, limit=10))

        if result["status"] == "success":
            st.session_state.competitor_analysis = result
            st.success(f"Found {result['competitors_found']} competitors!")
        else:
            st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")

# Display leaderboard
if st.session_state.get("competitor_analysis"):
    analysis = st.session_state.competitor_analysis
    st.markdown("### 🏆 AI Visibility Leaderboard")

    for entry in analysis["leaderboard"]:
        cols = st.columns([0.5, 2, 1, 1, 1, 1, 1, 1, 1])
        cols[0].write(f"**#{entry['rank']}**")
        cols[1].write(f"**{entry['name']}**")
        cols[2].metric("Overall", f"{entry['overall']}%")
        for i, dim in enumerate(["authority", "schema", "content", "reviews", "entities"]):
            cols[3 + i].metric(dim.title(), f"{entry['scores'].get(dim, 0)}%")
```

---

### 5.7 Testing Strategy

```python
# tests/test_unified_agent.py

import pytest
import asyncio
from agents.unified_competitor_agent import UnifiedCompetitorIntelligenceAgent


def mock_llm(prompt: str) -> str:
    """Deterministic mock LLM for testing."""
    if "List the top" in prompt:
        return '[{"name": "Test Brand A", "website": "https://example-a.com"}, {"name": "Test Brand B", "website": "https://example-b.com"}]'
    if "Analyze why" in prompt:
        return "Test Brand A wins because of superior schema coverage (95% vs 30%). Strategy: Add JSON-LD."
    if "executive summary" in prompt:
        return "MARKET POSITION: #3 of 3. WHY LEADERS WIN: Schema. ROI: Add FAQ schema +12%. GROWTH: 55% in 30 days."
    return "Mock response"


@pytest.fixture
def agent():
    return UnifiedCompetitorIntelligenceAgent(llm_provider=mock_llm)


def test_discover_competitors(agent):
    result = asyncio.run(agent.discover_competitors("My Brand", "restaurant", "NYC", limit=5))
    assert len(result) == 2
    assert result[0]["name"] == "Test Brand A"


def test_analyze_competitor(agent):
    competitor_data = {
        "name": "Test Brand",
        "website": "https://example.com",
        "crawl": {
            "status": "success",
            "html": "<html><head><title>Test</title></head><body><h1>Hello</h1><script type='application/ld+json'>{\"@type\": \"Restaurant\"}</script></body></html>",
            "meta": {"title": "Test", "word_count": 500, "h1_count": 1, "h2_count": 3, "link_count": 50, "img_count": 10, "has_faq": True},
            "structured_data": {"json_ld": [{"@type": "Restaurant"}]},
        },
    }
    result = agent.analyze_competitor(competitor_data)
    assert result["overall"] > 0
    assert "schema" in result["scores"]
    assert result["scores"]["schema"] > 0  # has Restaurant type


def test_full_pipeline(agent):
    result = asyncio.run(agent.run("My Brand", "restaurant", "NYC", limit=2))
    assert result["status"] == "success"
    assert len(result["leaderboard"]) == 2
    assert result["summary"] != ""


def test_parse_html(agent):
    result = {"html": '<html><head><title>Test Page</title><meta name="description" content="A test page"></head><body><h1>Main</h1><h2>Sub1</h2><h2>Sub2</h2></body></html>', "meta": {}, "structured_data": {}}
    parsed = agent._parse_html(result)
    assert parsed["meta"]["title"] == "Test Page"
    assert parsed["meta"]["h1_count"] == 1
    assert parsed["meta"]["h2_count"] == 2
```

---

### 5.8 Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers for crawling
RUN pip install playwright && playwright install chromium --with-deps

COPY . .

EXPOSE 8501 8000

# Default: run Streamlit dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.headless=true"]
```

#### docker-compose.yml

```yaml
version: "3.8"

services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    env_file: .env
    depends_on:
      - redis
      - postgres
    command: streamlit run dashboard.py --server.port=8501 --server.headless=true

  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - redis
      - postgres
    command: uvicorn geo_audit_agent.api.main:app --host 0.0.0.0 --port 8000

  worker:
    build: .
    env_file: .env
    depends_on:
      - redis
      - postgres
    command: celery -A geo_audit_agent.workers.tasks worker --loglevel=info --concurrency=4

  beat:
    build: .
    env_file: .env
    depends_on:
      - redis
      - postgres
    command: celery -A geo_audit_agent.workers.tasks beat --loglevel=info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: brandsight
      POSTGRES_USER: brandsight
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  redis_data:
  pg_data:
```

#### .env Template

```bash
# LLM
GOOGLE_API_KEY=your_gemini_api_key
ANTHROPIC_BASE_URL=http://localhost:20128/v1
ANTHROPIC_AUTH_TOKEN=your_token

# Crawling
SCRAPER_API_KEY=your_scraperapi_key
SERP_API_KEY=your_serpapi_key

# Database
DATABASE_URL=postgresql://brandsight:changeme@postgres:5432/brandsight

# Redis
REDIS_URL=redis://redis:6379/0

# Dashboard auth
DASHBOARD_USER=admin
DASHBOARD_PASS=admin123
```

---

## 6. Cost Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| **Cache LLM responses** (24h TTL) | 60-80% of LLM costs | Already partially implemented in `cache.py` |
| **Use `gemini-flash-lite` for discovery** | 10x cheaper than flash | Already in `llm_router.py` |
| **Direct httpx before ScraperAPI** | $0 vs $0.001/call | Built into crawler above |
| **Batch crawls nightly** | Avoid peak pricing | Celery Beat schedule |
| **Store HTML snapshots in S3** | Avoid re-crawling | Add S3 upload after crawl |
| **Skip unchanged pages** | Skip crawl if Last-Modified < last_scan | ETag/If-Modified-Since header |

**Projected cost at scale**:
- 50 competitors, weekly scans: ~$45/month (ScraperAPI $30, LLM $5, infra $10)
- 500 competitors, weekly scans: ~$250/month
- 1000 competitors, daily scans: ~$800/month

---

## 7. Security & Compliance

| Concern | Mitigation |
|---------|------------|
| API key storage | `.env` files, never committed. In production: use AWS Secrets Manager / GCP Secret Manager. |
| Tenant isolation | All DB queries filter by `user_id`. Add Row-Level Security (RLS) in PostgreSQL. |
| Rate limiting | FastAPI middleware: 100 req/min for free tier, 1000 for Pro. Use `slowapi` or Redis-backed token bucket. |
| Crawling ethics | Respect `robots.txt` — check before crawling. Set a proper User-Agent. Add `Crawl-Delay` support. |
| GDPR/CCPA | Competitor data is public business info (websites, reviews). User PII stored in Supabase with deletion API. |
| Input sanitization | All user inputs (brand, category, city) sanitized before LLM prompts. Existing `guardrail_node` pattern. |
| Secrets in logs | Never log API keys. Existing `logger.info()` calls are clean; add a log filter for production. |

---

## 8. Monitoring & Observability

### Metrics to Track

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| Crawler success rate | Custom counter | < 90% over 1 hour |
| LLM response latency (P95) | Timer | > 10 seconds |
| Celery queue depth | Redis LLEN | > 50 pending tasks |
| API error rate (5xx) | FastAPI middleware | > 1% over 5 min |
| Scan completion rate | DB query | < 95% over 24h |
| LLM cost per day | Cost tracker | > $10/day (alert at 2x budget) |

### Implementation

```python
# geo_audit_agent/observability/metrics.py — extend existing

from prometheus_client import Counter, Histogram, Gauge

CRAWL_TOTAL = Counter("crawl_total", "Total crawl attempts", ["status"])
CRAWL_DURATION = Histogram("crawl_duration_seconds", "Crawl duration", buckets=[1, 5, 10, 30, 60])
LLM_CALL_TOTAL = Counter("llm_call_total", "LLM API calls", ["model", "status"])
LLM_LATENCY = Histogram("llm_latency_seconds", "LLM response time", ["model"])
ANALYSIS_QUEUE_SIZE = Gauge("analysis_queue_size", "Pending analysis tasks")
```

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Websites block crawler** | High | Medium | ScraperAPI proxy, rotating User-Agents, respect rate limits |
| **LLM API outage** | Medium | High | Multi-provider fallback (Gemini → proxy → cached response) |
| **LLM hallucination in discovery** | High | Medium | Validate discovered competitors with SerpAPI/web search |
| **Cost overrun from LLM calls** | Medium | Medium | Aggressive caching, cost tracking, hard budget limits |
| **Stale data** | Medium | Low | Weekly automated re-scans, timestamp all data |
| **Scope creep** | High | High | Ship MVP first (discovery + crawl + leaderboard), iterate |
| **Single point of failure (Redis)** | Low | High | Redis Sentinel for HA, in-memory fallback exists |

---

## 10. Implementation Roadmap — 12 Weeks

### Phase 1: Foundation (Weeks 1-2)

| Week | Deliverable | Owner |
|------|-------------|-------|
| 1 | Database schema migration (competitors, scans, scores, explanations, alerts) | Backend |
| 1 | Celery + Redis worker setup, health check endpoint | Backend/DevOps |
| 1 | `UnifiedCompetitorIntelligenceAgent` class skeleton with discovery module | AI Engineer |
| 2 | Async Playwright crawler with ScraperAPI fallback | Backend |
| 2 | Unit tests for discovery + crawl | Backend |
| 2 | Basic "Discover Competitors" button in dashboard | Frontend |

**Milestone**: Can discover and list competitors for a brand.

### Phase 2: Analysis (Weeks 3-4)

| Week | Deliverable | Owner |
|------|-------------|-------|
| 3 | Analyzer module: 7-dimension scoring | AI Engineer |
| 3 | FastAPI endpoints: `/analyze`, `/status/{id}`, `/leaderboard/{brand}` | Backend |
| 4 | AI Visibility Leaderboard UI in dashboard | Frontend |
| 4 | Integration tests (discovery → crawl → analyze pipeline) | Backend |

**Milestone (MVP)**: Full pipeline works end-to-end. Leaderboard visible in dashboard.

### Phase 3: Intelligence (Weeks 5-7)

| Week | Deliverable | Owner |
|------|-------------|-------|
| 5 | Intelligence generation module (LLM explanations per competitor) | AI Engineer |
| 5 | Executive summary generation | AI Engineer |
| 6 | "Why They Win" detail page in dashboard | Frontend |
| 6 | Competitor comparison view (side-by-side scores) | Frontend |
| 7 | Cost tracking, caching optimization, prompt engineering refinement | AI Engineer |

**Milestone**: Users can see WHY competitors are winning with actionable strategies.

### Phase 4: Monitoring & Polish (Weeks 8-10)

| Week | Deliverable | Owner |
|------|-------------|-------|
| 8 | Celery Beat scheduler for weekly automated re-scans | Backend |
| 8 | Alert system (visibility changes, new competitors) | Backend |
| 9 | Alert notification UI in dashboard + sidebar badge | Frontend |
| 9 | Historical trend charts (score over time per competitor) | Frontend |
| 10 | Performance testing (100 competitors), load testing | DevOps |

**Milestone**: Automated weekly scanning with alerts. Users never manually re-audit.

### Phase 5: Remediation (Weeks 11-12)

| Week | Deliverable | Owner |
|------|-------------|-------|
| 11 | Auto-generate schema (JSON-LD) from competitor best practices | AI Engineer |
| 11 | Auto-generate FAQ pages based on gaps | AI Engineer |
| 12 | Deploy integration (WordPress/Shopify API) | Backend |
| 12 | Executive PDF report generation | Frontend |

**Milestone**: Platform can fix problems, not just find them.

---

## 11. Success Metrics

### Week 4 (MVP)

- [ ] Can discover 10 competitors in < 30 seconds
- [ ] Crawl success rate > 85%
- [ ] Leaderboard renders correctly for 3+ test brands
- [ ] End-to-end pipeline completes in < 5 minutes

### Week 8 (Intelligence)

- [ ] Intelligence explanations rated "useful" by 5+ test users
- [ ] LLM cost per full analysis < $0.05
- [ ] Automated weekly scans running for 10+ brands

### Week 12 (Production)

- [ ] 100 competitor scale test passes
- [ ] < 1% error rate over 7-day period
- [ ] 3+ users actively using competitor intelligence
- [ ] Schema/FAQ generation working for 2+ industries

---

## 12. What NOT to Build (Yet)

These are tempting but premature for the current stage:

| Feature | Why Skip | When to Add |
|---------|----------|-------------|
| Multi-tenant SSO | No paying customers yet | After 50+ paying users |
| Real-time streaming updates | Adds complexity for marginal UX gain | After MVP validated |
| Custom ML models for scoring | Gemini scoring is good enough to start | After 1000+ data points collected |
| White-label / API marketplace | Premature optimization | After $10K MRR |
| Mobile app | Streamlit works on mobile browsers | After product-market fit |

---

## Quick-Start Checklist

1. `pip install httpx beautifulsoup4 playwright celery redis`
2. `playwright install chromium`
3. Create `agents/unified_competitor_agent.py` (code above)
4. Add competitor DB tables via Alembic migration
5. Wire up Celery worker (`celery -A geo_audit_agent.workers.tasks worker`)
6. Add "Discover Competitors" button to dashboard
7. Test with your own brand
8. Iterate

---

*This plan is designed for a startup building its first production version. Every recommendation is sized for a team of 5-6 engineers over 12 weeks. Scale decisions (Kubernetes, multi-region, etc.) are intentionally deferred until the product has paying customers.*
