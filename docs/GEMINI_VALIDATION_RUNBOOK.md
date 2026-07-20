# Gemini validation runbook (BrandSight GEO)

This is the Gemini-only validation phase. OpenAI validation is intentionally deferred to the next session.

## What this phase can prove

It can prove that the Gemini provider boundary works for the configured model, that the app receives non-empty responses, that usage/latency/error states are recorded, and that the response can enter BrandSight's evidence/observation pipeline.

It cannot prove a statistically stable GEO visibility score from four free-tier calls. That requires repeated observations over time and a fixed prompt corpus. Any score from this run must remain an observation, not a market truth.

## Credential rules

1. Put keys only in a local ignored `.env` or shell environment. Never paste them into chat, GitHub, logs, screenshots, or validation reports.
2. Use `GOOGLE_API_KEY` as the primary slot. `GOOGLE_API_KEY_1` through `_7` are ordered backups. The live adapter automatically advances to the next key only after a quota/rate-limit response.
3. Do not rotate keys to evade a quota or rate limit. Every configured key must be separately authorized and belong to a project you are allowed to use. [Inference: seven keys may still share a project-level quota, so key count does not guarantee seven times the allowance.]
4. Restrict each key to the Gemini API and treat it like a password. Google recommends environment variables/Secret Manager and warns against source-control or client-side exposure.

## Staged execution budget

| Stage | Live requests | Purpose | Gate |
|---|---:|---|---|
| 0 | 0 | Install/configuration, offline tests, inspect model setting | No secrets tracked; model is supported |
| 1 | 1 | Primary-key smoke test | Non-empty response, no auth/quota failure |
| 2 | 3 | Fixed SME/agency prompt corpus | All responses captured as metadata; no raw response required |
| 3 | 0 | Offline replay into observation/evidence scoring | Correct mention/recommendation/citation fields; no fixture pollution |
| 4 | 0 | Failure, empty, malformed, and quota tests with mocks | Explicit FAILED state and safe redaction |
| 5 | 0 | App/API/UI smoke using the captured result | User-visible source/mode/quality disclosure works |

Start with one key and the default four-request cap:

```bash
python scripts/validate_gemini.py --max-requests 1
python scripts/validate_gemini.py --max-requests 3
```

If the primary key reaches its quota, the validator automatically advances to the next separately authorized key:

```bash
python scripts/validate_gemini.py --max-requests 1
```

Use `--no-key-failover` only for a primary-key-only diagnostic.

For a local, private review of generated text, opt in explicitly with `--save-responses`; do not commit that report.

## Acceptance criteria

- Provider mode is `LIVE` on successful calls and `FAILED` on failures; no silent fixture fallback.
- Model is configured through `GEMINI_MODEL`; the repository default is `gemini-3.1-flash-lite` because the older Gemini 2.0 Flash-Lite model is shut down.
- At least one live response is non-empty and has a model, latency, request count, and response hash.
- A replayed response produces independent mention, recommendation, sentiment, position, citation, and confidence fields.
- A quota/auth/malformed response never exposes the key or raw exception body in the report.
- The report explicitly says this is integration evidence, not statistically reliable visibility measurement.

## Tomorrow

Reuse the same corpus, caps, report schema, and acceptance criteria for OpenAI. Do not compare Gemini and OpenAI scores until both sides have passed their provider-boundary checks and the prompt corpus is held constant.
