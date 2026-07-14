# BrandSight GEO implementation scorecard

Updated: 2026-07-14

This score reflects repository evidence, not live-provider or customer validation.

| Category | Weight | Score | Evidence |
|---|---:|---:|---|
| Measurement integrity | 20 | 17 | Explicit execution modes; four live adapters; no silent fixture fallback; evidence model/migration; numerator/denominator metrics; boundary-aware entities; no caller-forged competitor evidence. Live adapters remain unvalidated without credentials. |
| Security and authorization | 15 | 13 | Verified JWT identity; tenant ownership checks; signed admin claims/API guards; verified Streamlit sessions; admin allowlist; plan entitlements; process-local rate-limit fallback; tracked tree clean. Historical credential still requires owner rotation/history cleanup. |
| Reliability and deployment | 15 | 14 | Wheel builds; API and Streamlit offline smoke pass; migrations upgrade and evidence migration downgrade pass; Compose defects fixed; CI gates packaging, Compose, migrations, secrets, startup, lint, types, and tests. Docker runtime was unavailable locally. |
| Testing | 15 | 12 | 305 passed, 3 skipped; 60% overall coverage; primary UI 83%; evidence/metrics 100%; entity detection 94%; critical provider module 65%. Worker and legacy integration coverage remain weak. |
| Product UX | 15 | 13 | Replaced deceptive dashboard with explicit Live/Demo workflow, empty/loading/failure states, source labels, sample sizes, provider coverage, observation drill-down, and honest insufficient-evidence competitor/trend state. No external usability study. |
| Code quality | 10 | 9 | Ruff and mypy clean; invalid backend fixed; dead module/package collision and thousands of lines of unused/fabricated UI removed; deterministic ML gate requires 50 rows. Some legacy LLM/workflow modules remain. |
| Observability and documentation | 10 | 9 | Evidence trail includes prompt/provider/model/mode/latency/tokens/cost; evaluation dashboard requires real telemetry; README, setup, metric definitions, CI, and credential incident runbook updated. Production alerting not live-validated. |
| **Engineering total** | **100** | **87** | **Target reached.** |

## Verification evidence

- `FORCE_MOCK=true python -m pytest -q` — 305 passed, 3 skipped.
- Coverage — 60% overall; primary UI 83%; evidence and visibility metrics 100%; entity detection 94%.
- `ruff check .` — passed.
- `mypy geo_audit_agent --ignore-missing-imports` — passed for 145 source files.
- Wheel build through the PEP 517 backend — passed.
- API and Streamlit offline startup smoke — passed.
- Alembic upgrade from an empty database through `0008_evidence` — passed; evidence migration downgrade — passed.
- Tracked-tree credential scan — passed.
- Compose YAML syntax — passed. Full `docker compose config` is enforced in CI because Docker was unavailable locally.

## Release gate

Engineering score and release eligibility are separate. Release remains blocked until the repository owner:

1. revokes or rotates the credential exposed in historical commit `a1c9272`; and
2. approves and coordinates a shared-history rewrite.

Live provider behavior and customer value are also unvalidated until credentials and a real evaluation protocol are
available. Neither limitation is counted as completed work.
