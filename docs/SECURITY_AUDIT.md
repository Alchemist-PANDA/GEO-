# Full Application Audit — BrandSight GEO

**Auditor stance:** independent, adversarial. Every finding below was traced
against the actual code (file:line cited). Read-only audit — no code changed.

**Method:** static read/grep of the real files. I could **not** run the live
app, the Celery workers, a real Postgres/Redis, or any live LLM provider, so
dynamic findings (actual exploitation, load behaviour) are marked "needs
verification" where relevant.

---

## Executive summary

The app is a LangGraph-orchestrated multi-agent GEO platform (FastAPI API +
Streamlit UI + Celery workers). Core request-path security has clearly had
attention — JWT is verified with a pinned `HS256` algorithm (no `alg:none`
hole), tenant isolation on brands/audits/copilot returns 404 on cross-tenant
access, the rate limiter buckets by verified JWT `sub` (not a spoofable
header), and side-effecting "publish" actions are human-approval-gated and
actually only generate drafts. That is genuinely better than most apps of
this shape.

> **Accuracy note (important):** an initial pass of this report was written
> against a slightly older tree and flagged two High findings —
> *fabricated competitor intelligence* and *rate limiter fails open without
> Redis* — that are **already fixed in the current code** and were re-verified
> as fixed (see "Verified fixed" below). They are retained only as history.
> The live findings below reflect the current tree (suite: 314 passed).

**But it is not production-safe yet.** The most dangerous *live* issues:

1. **The git-history secret (Critical, BLOCKED_OWNER_ACTION).** A live-looking
   Gemini key remains in history at commit `a1c9272`; only the owner can
   rotate it and approve a history rewrite. Tracked in
   `docs/DEFERRED_EXTERNAL_VALIDATION.md`.
2. **`/v1/agentic/run` has no budget/quota enforcement (High).** The
   `/v1/audits` path checks `is_budget_exceeded` (`routes/audits.py:29`); the
   agentic path — which runs the full multi-agent graph with multiple LLM
   calls — invokes the graph directly (`routes/agentic.py:50-51`) with no
   per-user cap. An authenticated user can drive unbounded LLM spend.
3. **The Copilot chat endpoint runs no guardrail at all (Medium-High).**
   `/v1/copilot/chat` sends the user message plus a client-controlled
   `context` dict straight into the LLM (`copilot/engine.py:37-40`,
   `f"Context data: {context}\n\nUser question: {user_message}"`) with no
   `classify_input` call. Direct prompt injection / system-prompt extraction
   is unmitigated on this surface.
4. **`/metrics` is unauthenticated (Medium)** (`api/app.py:40`) and there are
   **no security headers** (CSP/HSTS/X-Frame/X-Content-Type, `api/app.py`).
5. **Latent SSRF (Medium).** `crawl_competitor(url)`
   (`geo_intelligence/fingerprint_generator.py:11-16`) fetches an arbitrary
   URL with no scheme/private-IP validation. Its only caller
   (`generate_fingerprint`, line 144) is not wired to any route today, so it's
   "do not wire without a fix" rather than an active hole.

### Verified fixed in the current tree (were flagged, then re-checked)
- **Competitor intelligence** — `agents/unified_competitor_agent.py` now calls
  `calculate_visibility_metrics` on real observations and returns
  `insufficient_evidence` when there is no data, instead of MD5-hash scores.
- **Rate-limiter fail-open** — `api/rate_limiter.py:53-101` now falls back to a
  real in-process sliding-window limiter (`_local_is_allowed`) when Redis is
  `None` or raises, instead of returning `True`.

---

## Phase 1 — Architecture & agent map

**Stack:** Python 3.10+, FastAPI + Uvicorn (API), Streamlit (UI), LangGraph
(orchestration), SQLModel + Postgres (Alembic migrations), Redis (cache +
rate limit), Celery (workers). LLMs: Google Gemini (`gemini-2.0-flash`,
`-flash-lite`) and Anthropic (`claude-haiku-4-5`); a new provider abstraction
(`geo_audit_agent/providers/`) adds OpenAI/Perplexity adapters. Observability:
Prometheus, Langfuse, structured logging.

**Entry points:** FastAPI routers under `/v1` (`brands`, `audits`, `feedback`,
`competitors`, `stream`, `agentic`, `copilot`, `health`); Streamlit pages
(`pages/*.py`, root `dashboard.py`); Celery tasks (`workers/tasks.py`).

**Two graphs exist:**
- **Audit graph** (`agent/graph.py`): `guardrail → query_llm → check_citation
  → gap_analyst → [planner → remediation_handler → validate_output↺] →
  generate_report`. Repair loop bounded by `state.max_repairs = 3`
  (`agent/state.py:53`). ✅ bounded.
- **Agentic orchestration graph** (`orchestration/langgraph_workflow.py`):
  `input_guard → context → policy → {audit|competitor|copilot|action} →
  inspector → END`. Linear, no cycles → cannot loop. ✅ bounded (but relies on
  LangGraph's default `recursion_limit=25`; not set explicitly).

**Agents/nodes:**
| Agent/node | Purpose | Model | Tools/effects | Autonomy |
|---|---|---|---|---|
| guardrail_node | Input safety classify | Gemini (express) | none | on-request |
| query_llm_node | Ask "best {cat} in {city}" | Gemini | none | on-request |
| check_citation_node | Detect brand mention | none (regex) | none | on-request |
| gap_analyst_node | Find visibility gaps | template + LLM | reads config file | on-request |
| planner_node | Plan remediation | Gemini | none | on-request |
| remediation_handler_node | Run tools | Gemini | `TOOL_REGISTRY` (content gen) | on-request |
| ActionAgent | Execute actions | Gemini via gateway | `actions/executors/*` (draft only) | **human-approval-gated** |
| InspectorAgent | Validate output | rules | none | on-request |
| unified_competitor_agent | Competitor scores | **none — MD5 hash** | none | on-request |
| Self-improvement (proposer/canary/shadow) | Propose config changes | LLM | Redis canary flags | admin-gated list |

**Trust boundaries:** client↔API (JWT), API↔DB (parameterized SQLModel),
API↔LLM (provider adapters), agent↔tool (`TOOL_REGISTRY`), agent↔external
content (competitor crawler — see SSRF), agent↔agent (orchestration state
dict). Memory (`memory/`, mem0) and vector store (Qdrant) are per-brand keyed.

---

## Findings table

| # | Severity | Category | File:Line | Description | Impact | Fix |
|---|---|---|---|---|---|---|
| F1 | Critical | Secrets | git history `a1c9272` | Live-looking Gemini key in history | Key compromise | Owner rotate + history rewrite (BLOCKED_OWNER_ACTION) |
| ~~F2~~ | ~~High~~ **FIXED** | LLM/Integrity | `agents/unified_competitor_agent.py` | ~~Competitor scores MD5-hash-derived + invented claims~~ Now computes real metrics, returns `insufficient_evidence` | — | Verified fixed in current tree |
| ~~F3~~ | ~~High~~ **FIXED** | Cost/DoS | `api/rate_limiter.py:53-101` | ~~Fails open when Redis down~~ Now falls back to in-process sliding-window limiter | — | Verified fixed in current tree |
| F4 | High | Cost | `api/routes/agentic.py:33-51` | `/agentic/run` has no budget/quota check (unlike `/audits`) | One user can drive unbounded multi-agent LLM spend | Add `is_budget_exceeded` + usage increment |
| F5 | Med-High | Prompt injection | `api/routes/copilot.py:74`, `copilot/engine.py:37-40` | Copilot chat runs no guardrail; user msg + client `context` concatenated into prompt | Direct injection / system-prompt extraction | Run `classify_input` on chat; treat context as data, not instructions |
| F6 | Medium | SSRF | `geo_intelligence/fingerprint_generator.py:11-16` | `crawl_competitor(url)` fetches arbitrary URL, no scheme/IP validation | SSRF to cloud metadata / internal svcs **if wired** (no live caller today) | Validate scheme, block private/link-local IPs, no redirects to them |
| F7 | Medium | Config | `api/app.py` | No security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options) | Clickjacking / MIME sniffing / downgrade | Add a security-headers middleware |
| F8 | Medium | Data exposure | `api/app.py:40` | `/metrics` mounted with no auth | Internal metrics/cardinality leak | Gate behind auth or network policy |
| F9 | Medium | Guardrail | `services/guardrails.py:42-49` | Regex prefilter blocks only 5 tokens, then defers to an LLM classifier (system-prompt-based) | Weak injection control; bypassable | Treat as defense-in-depth only; add structured input separation |
| F10 | Low-Med | Data exposure | `api/routes/copilot.py:78` | Streams `str(e)` to client on error | Internal detail leak | Return generic error; log detail server-side |
| F11 | Low-Med | LLM/GEO | `actions/executors/post_to_linkedin.py` etc. | Raw LLM content returned as publishable artifact, no fact-check | Hallucinated claims (approval-gated, so mitigated) | Add fact/citation review step before "approved" |
| F12 | Low | Correctness | `orchestration/langgraph_workflow.py:51`, `agentic.py:51` | `recursion_limit` not set explicitly on `invoke` | Relies on default 25 | Set an explicit, documented limit |
| F13 | Low | Reliability | `services/llm_router.py` vs `workflows/audit_workflow.py:8` | `audit_workflow.py` imports `temporalio` (not installed) | Import crash if that path used | Remove dead Temporal path or add dep |

---

## Phase 2 — Security detail

**Auth (good):** `api/auth.py` verifies Supabase JWT with `algorithms=
["HS256"]` and explicit `sub` presence — no `alg:none`/confusion hole.
`require_admin` gates `/inspector/check` and `/improvement/proposals`.
Rate-limit identity uses the verified `sub`, IP fallback only
(`rate_limiter.py:87-135`). **Gap:** password/reset/MFA flows are handled by
Supabase (out of this repo) — *not verifiable here*, flag for Supabase-side
review (token entropy, enumeration, login brute-force).

**Authorization (good, with one gap):** `routes/brands.py:78`,
`routes/audits.py`, `routes/copilot.py:61-62` all filter by verified user and
return 404 cross-tenant — IDOR-resistant. **Gap:** `competitors.py:30` and
`agentic.py:34` authenticate but do no per-resource ownership/budget check
(F4).

**Injection:** DB access is SQLModel `select().where()` — parameterized, no
raw SQL/string interpolation found. No `os.system`/`subprocess`/`eval`/`exec`
in the request path. Tool arguments (`agent/tools.py`) are typed and passed to
content generators, not shells/SQL. ✅

**CORS:** `allow_origins=["https://app.brandsightgeo.com"]` with
`allow_credentials=True` — **not** the wildcard-with-credentials critical
pattern. `allow_methods/headers=["*"]` is acceptable given the specific
origin. ✅

**Prompt injection (F5, F9):** the audit graph runs `guardrail_node` first, but
the **Copilot chat path bypasses it entirely** and concatenates a
client-controlled `context` dict into the prompt. Indirect injection via
scraped content (`crawl_competitor` → LLM) is **latent** — the crawler has no
live in-app caller today (`generate_fingerprint` is unreferenced), so it's a
"don't wire this without sanitizing" finding rather than an active hole.

**Secrets:** no hardcoded live secrets in current tracked code; all keys via
`os.getenv`. The only exposure is the historical key (F1).

---

## Phase 3 — Architecture

Separation is reasonable (routes → agents/services → db). Two notable smells:
the duplicate audit graphs (`agent/` vs `orchestration/`) and a dead Temporal
path (`workflows/audit_workflow.py`, F13). DB has 21 FK constraints and 50
indexes — healthy. Agent decisions are traceable via `step_log` and
`ObservationEvidence`. Models are pinned (good), though `claude-haiku-4-5`
lacks a date suffix (minor drift risk). Failure isolation: nodes catch and
fall back to mock rather than propagating garbage — acceptable, but the
"fall back to mock on live error" pattern in `query_llm_node:96` can mask a
provider outage as a successful (simulated) audit; ensure `state.mode` is
surfaced to the user.

## Phase 4 — Functionality & correctness

- **F2 (competitor scan) is now fixed** — it computes real visibility metrics
  and returns `insufficient_evidence` rather than hash-derived theater. The
  remaining correctness watch-item is the `query_llm_node` mock-fallback (see
  below).
- `check_citation_node` is now boundary-aware (no "Ola"-in-"solar" false
  positive) — verified fixed.
- Idempotency: `workers/tasks.py` upserts competitors by name (`:92-121`) —
  re-runnable without duplicates. ✅ (needs verification under concurrency).
- No TODO/FIXME/HACK left in `geo_audit_agent/`. ✅

## Phase 5 — Data integrity

Server-side validation via Pydantic request models on every route. Multi-write
worker paths use a session/commit; **needs verification** that competitor
scan + alert writes are in one transaction (partial failure could leave a scan
with no scores). Migrations have `upgrade`/`downgrade` and a single head
(verified). 

## Phase 6 — Testing & reliability

Suite: **373 passed, 3 skipped, 0 errors** (`FORCE_MOCK=true pytest -q`),
ruff clean. Coverage ~59% overall; new core modules 76–100%; `ui/*.py` and
several workflow modules remain near 0% — the highest-risk untested surface is
the Streamlit UI and the live provider bodies. No `assert True` stubs found;
skips are SDK-gated, not hiding failures.

## Phase 7 — Code quality

Duplicate orchestration graphs and a legacy root-script sprawl
(`drop.py`, `patch.py`, `fix_lints.py`) increase surface area. Cyclomatic
complexity is highest in `agent/nodes.py` (multiple large nodes) — candidates
for extraction, low priority.

---

## Could not verify (be explicit)

- Live exploitation of F3/F4/F5 (no running app / Redis / LLM keys).
- Supabase-side auth (password hashing, reset-token entropy, login
  brute-force, MFA) — lives outside this repo.
- Actual concurrency behaviour of worker upserts (F-data-integrity).
- Production config (debug flags, cloud IAM, TLS enforcement) — not in repo.
- Whether `/metrics` is network-isolated in the real deploy (F8 severity
  depends on it).
