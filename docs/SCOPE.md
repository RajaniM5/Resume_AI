# Scope & Success Metrics

## In scope (MVP)
- Resume ingestion: PDF and DOCX (English only for v1)
- Single job-description-at-a-time screening: rank a batch of resumes against one JD
- Structured extraction: contact info, skills, work experience, education, certifications
- Candidate scoring: semantic match score (0-100) + extracted skill-gap list against JD requirements
- Explainability: each score returns the top contributing factors (matched skills, experience fit, education fit)
- REST API for submission (single + batch) and result retrieval
- Async batch processing (target: 500 resumes/batch without blocking callers)
- Audit log of every screening decision (inputs, model version, output, timestamp)
- Human-in-the-loop: HR reviewer can override any automated ranking; override is logged

## Out of scope (v1, candidates for later)
- Non-English resumes / multilingual NLP
- Video/audio resume screening
- Automated rejection emails or scheduling (screening only, no candidate-facing actions)
- Direct two-way sync with specific ATS platforms (v1 ships generic webhook + CSV import; named ATS connectors are P2 stretch)
- Continuous learning from hiring outcomes (planned for P3, not v1)

## Success metrics
| Metric | Target | How measured |
|---|---|---|
| Manual screening effort reduction | 60% | Time HR spends per requisition, before vs. after (self-reported + timestamp logs) |
| Scoring latency (p95) | < 2s for single resume, < 5 min for 500-resume batch | API/queue timing metrics |
| Ranking quality | Top-20% model ranking captures ≥ 90% of candidates HR would have manually shortlisted | Precision@K against historical shortlists |
| False-negative rate | < 5% of qualified candidates (per historical labels) scored in bottom half | Offline eval against labeled holdout set |
| Bias/fairness | No statistically significant score disparity across gender-coded names / protected-class proxies on eval set | Fairness audit (see [ARCHITECTURE.md](ARCHITECTURE.md) governance section) |
| Availability | 99.5% uptime for screening API | Uptime monitoring |

## Assumptions
- HR provides job descriptions in free text; no structured JD schema required upstream
- Resumes arrive without prior consent-tracking concerns (assume employer already has candidate consent to automated screening — flag as a legal/compliance dependency, not something this system enforces)
- Initial volume: single-tenant, up to ~10k resumes/month
