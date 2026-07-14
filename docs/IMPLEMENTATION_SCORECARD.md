# BrandSight GEO implementation scorecard

Updated: 2026-07-14

This score reflects repository evidence, not live-provider or customer validation. It deliberately separates offline
implementation completeness from whether the product has proven customer value.

| Category | Weight | Score | Evidence |
|---|---:|---:|---|
| Measurement integrity | 20 | 17 | Explicit execution modes; four live adapters; no silent fixture fallback; evidence model/migration; numerator/denominator metrics; boundary-aware entities; no caller-forged competitor evidence. Live adapters remain unvalidated without credentials. |
| Security and authorization | 15 | 14 | Verified JWT identity; tenant ownership checks; signed admin claims/API guards; verified Streamlit sessions; admin allowlist; plan entitlements; process-local rate-limit fallback; tracked tree clean; exposed credential removed from every live branch. Owner rotation is still mandatory. |
| Reliability and deployment | 15 | 14 | Wheel builds; API and Streamlit offline smoke pass; migrations upgrade and evidence migration downgrade pass; Compose defects fixed; CI gates packaging, Compose, migrations, secrets, startup, lint, types, and tests. Docker runtime was unavailable locally. |
| Testing | 15 | 13 | 314 passed, 3 skipped; cross-page AppTests cover empty and populated offline states; canonical audit context, fixture disclosure, exports, evidence/metrics, provider boundaries, auth, and guardrails have regression coverage. Worker and legacy integration coverage remain weaker. |
| Product UX | 15 | 13 | Explicit Live/Demo workflow, onboarding, empty/loading/failure states, source labels, session audit selection, cross-workspace context, three export formats, evidence drill-down, and honest insufficient-evidence states. History is session-local without the external auth/database stack; no usability study exists. |
| Code quality | 10 | 9 | Ruff and mypy clean; invalid backend fixed; dead module/package collision and thousands of lines of unused/fabricated UI removed; deterministic ML gate requires 50 rows. Some legacy LLM/workflow modules remain. |
| Observability and documentation | 10 | 8 | Evidence trail includes prompt/provider/model/mode/latency/tokens/cost; evaluation dashboard requires real telemetry; README documents the no-key workflow and limitations. Production alerting and runbooks are not live-validated. |
| **Offline implementation total** | **100** | **88** | **The no-key implementation target is reached.** |

## Verification evidence

- `FORCE_MOCK=true python -m pytest -q` — 314 passed, 3 skipped.
- Coverage — 60% overall; primary UI 83%; evidence and visibility metrics 100%; entity detection 94%.
- `ruff check .` — passed.
- `mypy geo_audit_agent --ignore-missing-imports` — passed for 144 source files.
- Wheel build through the PEP 517 backend — passed.
- API and Streamlit offline startup smoke — passed.
- Alembic upgrade from an empty database through `0008_evidence` — passed; evidence migration downgrade — passed.
- Tracked-tree credential scan — passed.
- Compose YAML syntax — passed. Full `docker compose config` is enforced in CI because Docker was unavailable locally.

## Release gate

Implementation score and product readiness are separate. The old credential was removed from all live branches, but
the repository owner must still revoke it at the provider because deleting Git history cannot invalidate a secret.

The honest overall product-readiness score remains **82/100** until live adapters are exercised, authenticated durable
history is demonstrated in deployment, and real users show that the recommendations improve decisions. Customer value
cannot be manufactured by adding more code, and it is not counted as completed work here.
