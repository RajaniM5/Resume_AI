# AI-Powered Resume Screening System — Task List

Goal: NLP/ML-based resume screening with HR system integration APIs, targeting 60% reduction in manual screening effort, with attention to latency and governance (fairness, auditability, compliance).

Priority key: **P0** blocking/foundational, **P1** core functionality, **P2** integration, **P3** hardening (perf/governance), **P4** polish/ops.

## P0 — Foundations
- [ ] Define scope: job roles supported, resume formats (PDF/DOCX/text), languages, expected volume/throughput
- [ ] Define success metrics: screening accuracy, time saved, false-negative rate (qualified candidates missed), latency SLA
- [ ] Choose tech stack (e.g., Python, FastAPI, spaCy/HuggingFace transformers, PostgreSQL/vector DB)
- [ ] Design high-level architecture (ingestion → parsing → scoring → ranking → API → HR system)
- [ ] Source/assemble training & evaluation data (resumes + job descriptions + labels), with consent/licensing check
- [ ] Set up repo structure, dependency management, CI skeleton

## P1 — Core NLP/ML Pipeline
- [ ] Resume parsing: extract text from PDF/DOCX, handle OCR fallback for scanned docs
- [ ] Information extraction: name, contact, skills, experience, education, certifications (NER model or rules+ML hybrid)
- [ ] Job description parsing: extract required skills, experience level, qualifications
- [ ] Matching/scoring model: semantic similarity (embeddings) between resume and JD, skill-gap scoring
- [ ] Ranking logic: combine multiple signals into a single candidate score with explainability (which factors drove the score)
- [ ] Model evaluation harness: precision/recall against labeled dataset, baseline comparison

## P2 — API & Integration Layer
- [ ] Design REST API contract (submit resume, get score, batch screening, webhook callbacks)
- [ ] Implement API service (auth, rate limiting, input validation, versioning)
- [ ] Async processing/queue for batch resume screening (avoid blocking on model inference)
- [ ] HR system integration adapters (e.g., ATS webhooks, CSV/bulk import, common ATS APIs like Greenhouse/Workday format support)
- [ ] API documentation (OpenAPI/Swagger) + sample client usage

## P3 — Performance & Governance Hardening
- [ ] Latency optimization: model quantization/distillation, caching, batching, async inference, target p95 latency
- [ ] Load testing to validate throughput under peak HR hiring-season volume
- [ ] Bias/fairness audit: test scoring across gender-coded names, schools, employment gaps; document mitigation steps
- [ ] Explainability: expose reason codes / feature attributions per score (not just a black-box number)
- [ ] Audit logging: record every screening decision, model version, and inputs for compliance traceability
- [ ] Data privacy/compliance: PII handling, retention policy, GDPR/EEOC-relevant safeguards, human-in-the-loop override
- [ ] Model monitoring: drift detection, periodic re-evaluation against new hiring outcomes

## P4 — Deployment, Ops & Polish
- [ ] Containerize services (Docker) + deployment pipeline (staging/prod)
- [ ] Monitoring/alerting (latency, error rate, model confidence distribution)
- [ ] Admin dashboard for HR reviewers (view rankings, override decisions, feedback loop to retrain)
- [ ] End-to-end documentation (setup, architecture, runbook)
- [ ] User acceptance testing with HR stakeholders, measure actual screening-effort reduction vs. 60% target
