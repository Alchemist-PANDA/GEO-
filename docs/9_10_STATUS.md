# BrandSight GEO — 9/10 milestone status

This document separates implemented product capability from unvalidated claims.

## Implemented in this phase

- Bounded server-side public HTML evidence collection with SSRF protection, response-size limits, provenance, metadata, headings, contact signals, social links, and JSON-LD types.
- Query-specific keyword metrics that exclude fixtures and failed requests.
- Repeatability calculations that require at least two successful comparable observations.
- Recommendation evidence attachment that marks unsupported advice as `unverified` instead of presenting it as fact.
- Regression tests covering these rules.

## Deliberately not claimed

- A crawl does not prove rankings, traffic, review authenticity, domain authority, or customer outcomes.
- The Gemini Pakistan case study proves a working Gemini provider boundary and a repeatable workflow; it does not prove multi-provider visibility.
- OpenAI validation is intentionally deferred to the next phase.
- Before/after customer outcomes are not claimed until a real client supplies a baseline and a follow-up run.

## Remaining path to 9/10

1. Expose public-evidence collection in the authenticated API and UI.
2. Persist keyword and repeatability observations per audit.
3. Run the same corpus over multiple dates and providers.
4. Add source URLs to every generated action in the final report.
5. Complete OpenAI validation and provider-separated reporting.
6. Obtain one real before/after SME case study with consent.
