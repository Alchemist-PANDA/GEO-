# BrandSight GEO

BrandSight GEO measures whether named brands appear in AI-provider recommendation responses. The product separates
live observations, cached observations, demo fixtures, and failed requests; fixture data is never included in
authoritative metrics.

## What the numbers mean

- **Mention rate:** responses with a boundary-verified brand mention / successful live or cached responses.
- **Recommendation rate:** responses recommending the entity / successful live or cached responses.
- **Citation rate:** responses containing at least one source URL / successful live or cached responses.
- **Provider coverage:** providers successfully observed / providers requested.
- **Prompt coverage:** prompt templates observed / prompt templates requested.

Every metric carries its numerator, denominator, and sample size. No observations produces “insufficient evidence,”
not a zero. Competitor rankings require like-for-like evidence for every entity. Trends require at least two comparable
real periods.

## Local setup

Requires Python 3.10 or newer.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run dashboard.py
```

With no Supabase or provider credentials, the Streamlit application starts in local evaluation mode and exposes only
explicit demo fixtures. Configure `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_JWT_SECRET` before enabling an
authenticated deployment. Live adapters use `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, and
`PERPLEXITY_API_KEY`; missing or failed providers remain failed and never fall back to fixtures.

Run the API separately:

```bash
uvicorn geo_audit_agent.api.app:app --host 0.0.0.0 --port 8000
```

API documentation is available at `/v1/docs`; liveness is `/health`, and database readiness is `/ready`.

## Verification

```bash
FORCE_MOCK=true pytest
ruff check .
python -m build
python scripts/check_secrets.py
python scripts/smoke_startup.py
```

Docker Compose requires the passwords and Langfuse secrets shown in `.env.example`:

```bash
docker compose config
docker compose up --build
```

CI runs packaging, tracked-tree credential scanning, Compose validation, migrations, offline startup smoke tests,
linting, type checking, tests, and coverage.

## Security

API identity comes only from verified Supabase JWT claims. Tenant-owned brand and audit routes filter by the signed
`sub`; administrative inspector and improvement routes require a signed admin role. Caller-supplied identity headers
are not trusted by the rate limiter.

Never commit credentials. If one enters Git history, follow [the credential incident runbook](docs/CREDENTIAL_INCIDENT.md).
