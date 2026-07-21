# Gemini Pakistan SME Case Study

## Executive Summary

BrandSight GEO ran a Pakistan-focused Gemini-only validation across eight public SME and SME-adjacent businesses. The run tested whether Gemini could return useful generative engine optimization observations from public-facing business information only.

All eight business prompts passed in the full corpus run. The result is useful as a client-presentable case study for SME owners and SME marketing agencies, but it is not a statistically conclusive visibility study and should not be presented as an official audit of any named business.

## Why This Matters

Pakistani SMEs increasingly need to be understandable not only to search engines, but also to AI systems that summarize, compare, and recommend businesses. Gemini's responses consistently focused on whether each business has public, crawlable, cross-checkable evidence: service clarity, location clarity, professional credentials, reviews, structured data, category relevance, and third-party corroboration.

For SME marketing agencies, this creates a practical offer: improve the public evidence layer that helps AI systems identify what a business does, where it operates, who it serves, and why it is trustworthy.

## Businesses Tested

| Business | Category | Location / Market | Website |
|---|---|---|---|
| Dental Art | Dental clinic | Lahore, Pakistan | https://dentalart.net.pk/ |
| JS Engineers | HVAC and engineering services | Pakistan-wide, including Karachi, Lahore, Islamabad | https://jsengineers.pk/ |
| Virtual Accountants | Accounting and bookkeeping for SMEs | Pakistan | https://www.virtualaccountants.pk/ |
| Lawyers of Pakistan | Corporate and legal services | Pakistan | https://lawyersofpakistan.pk/ |
| OB Hospitality Group | Restaurant and hospitality group | Pakistan | https://obhospitalitygroup.com/ |
| Conatural | Skincare ecommerce brand | Pakistan | https://conaturalintl.com/ |
| CORE Karachi | Fitness studio and gym | Karachi, Pakistan | https://corekarachi.pk/ |
| WeProms Digital | SME digital marketing agency | Lahore, Pakistan; serves SMEs in Pakistan, UK, and UAE | https://weproms.com/ |

## Prompt Methodology

Each business received one GEO-style prompt asking Gemini to use only public-facing evidence and identify:

- What would make the business trustworthy enough for AI systems to mention or recommend.
- What public evidence gaps could reduce AI confidence.
- What a small marketing agency should improve in 30 days.

The prompts explicitly prohibited invented rankings, revenue, traffic, customer counts, private data, and citations.

## Gemini Run Evidence

- Model: `gemini-3.1-flash-lite`
- Full corpus live request count: `8`
- Full corpus pass/fail count: `8 passed`, `0 failed`
- Smoke-test requests before the full run: `4`
- Total validator request attempts for this case-study task: `12`
- Max output tokens: `256`
- Fixture mode: not used
- Machine-readable artifact: `validation_artifacts/gemini/pakistan_sme_case_study.json`

Evidence that live Gemini was used is retained in the machine-readable artifact through generated timestamp, model name, key-slot metadata, response character counts, token counts, and response hashes. Raw Gemini response text was removed from the committed artifact.

## Findings By Business

### Dental Art

Gemini treated Dental Art as a local healthcare entity where trust depends on consistent name, address, phone, location signals, dentist credentials, PMDC-verifiable professional identity, treatment-page clarity, patient-facing content, and review evidence. The 30-day improvement path is to strengthen service pages, practitioner proof, local schema, Google Business Profile consistency, and review visibility.

### JS Engineers

Gemini identified JS Engineers as a B2B engineering services entity where AI confidence depends on clear mapping of HVAC, plumbing, firefighting, and automation services to industrial and commercial sectors. The strongest improvement opportunities are project proof, sector-specific pages, client or case-study evidence, service-area clarity for Karachi, Lahore, and Islamabad, and structured organization/service data.

### Virtual Accountants

Gemini framed Virtual Accountants around SME bookkeeping, tax compliance, payroll, and financial reporting. It emphasized the need for service-market alignment with Pakistan-specific compliance needs, clear professional identity, startup and small-business positioning, trust pages, credentials, and explanatory content around FBR, tax, payroll, and reporting workflows.

### Lawyers of Pakistan

Gemini treated legal services as a high-trust category where professional verification matters. It highlighted consistent contact details, bar or professional credentials, attorney/service-area clarity, specific Pakistan legal and tax content, and stronger evidence around corporate, startup, and company-service use cases. The recommendation risk is highest where credentials or practice-area proof are thin.

### OB Hospitality Group

Gemini understood OB Hospitality Group as a parent hospitality entity rather than a single outlet. It focused on portfolio clarity, restaurant and cafe entity relationships, geographic anchoring in Pakistan, outlet-level pages, menu/location/review signals, and cross-platform consistency. The main GEO opportunity is making each brand and location easier for AI systems to connect to the group.

### Conatural

Gemini recognized Conatural as a skincare ecommerce brand in the natural and organic category. It emphasized brand consistency, product-category clarity, educational content, marketplace or third-party corroboration, ingredient transparency, product schema, review evidence, and clearer proof around claims such as natural, organic, anti-aging, skincare, body care, and hair care.

### CORE Karachi

Gemini treated CORE Karachi as a local fitness facility where AI recommendation confidence depends on location clarity, class and trainer information, pricing/timing visibility, review quality, and service match for TRX, HIIT, cycling, group training, and gym intent. The 30-day opportunity is to make schedules, trainers, reviews, local schema, and class pages more crawlable and consistent.

### WeProms Digital

Gemini identified WeProms Digital as a technical SME marketing agency with a clear Lahore base and broader Pakistan, UK, and UAE service market. It considered server-side tracking, CRM workflows, paid media, SEO, and AI-ready content as strong category signals. The improvement path is stronger case-study proof, client-result framing without unverifiable claims, service-page depth, process evidence, and clearer SME segment positioning.

## Common GEO Patterns Across Pakistani SMEs

- Entity clarity matters: AI systems need consistent business name, category, location, website, and service descriptions.
- Local proof matters: Google Business Profile, maps, directories, reviews, and location pages help reinforce market relevance.
- Professional proof matters in sensitive categories: healthcare, legal, accounting, and engineering need credentials, registrations, team identity, and compliance-oriented content.
- Service-page specificity matters: broad homepage claims are weaker than crawlable pages for each service, market, and use case.
- Third-party corroboration matters: marketplaces, directories, professional bodies, reviews, media, and partner/client proof help reduce uncertainty.
- Structured data matters: organization, local business, product, service, review, FAQ, person, and location schema can make public evidence easier for AI systems to parse.

## What BrandSight GEO Can Measure For SME Owners

BrandSight GEO can help SME owners understand whether public information makes their business easy for AI systems to identify, categorize, trust, and recommend. Useful owner-facing measures include entity consistency, local visibility signals, service clarity, review evidence, proof depth, content gaps, schema readiness, and AI-response observability over repeated prompts.

## What BrandSight GEO Can Offer SME Marketing Agencies

For SME marketing agencies, BrandSight GEO can support audits, monthly reporting, content roadmaps, local proof cleanup, schema implementation, competitor comparison, prompt tracking, and before/after validation. The agency value is turning AI visibility into practical execution work: better service pages, better proof, better local signals, better structured data, and clearer category positioning.

## Limitations

- Gemini only.
- Small sample of eight businesses.
- Public information only.
- One run date: July 20, 2026.
- Not an official audit of these businesses.
- Not statistically stable visibility scoring.
- No claim is made that BrandSight GEO represents, has private data from, or was engaged by any named business.
- Results are Gemini response observations, not verified rankings, revenue, traffic, market share, customer counts, or citation studies.

## Next Validation

- Run OpenAI validation tomorrow.
- Repeat across multiple providers.
- Normalize against competitor sets by category and city.
- Track repeated prompts over time for stability.
- Add side-by-side evidence scoring for website, local profile, directories, reviews, schema, credentials, and content depth.
