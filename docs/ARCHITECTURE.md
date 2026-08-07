# Architecture & Tech Stack

## Stack decisions

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Standard for NLP/ML tooling, HuggingFace/spaCy ecosystem |
| API framework | FastAPI | Async-native (fits latency goals), auto OpenAPI docs, Pydantic validation |
| NLP/parsing | spaCy (NER for entity extraction) + `pdfplumber`/`python-docx` for text extraction | Mature, fast, doesn't require GPU for extraction |
| Semantic matching | `sentence-transformers` (e.g., `all-mpnet-base-v2`) for resume/JD embeddings, cosine similarity | Good accuracy/latency tradeoff on CPU; swappable for a larger model later |
| Task queue | Celery + Redis (or RQ for simpler ops) | Async batch processing without blocking the API |
| Database | PostgreSQL | Structured candidate/screening/audit data, relational integrity for HR records |
| Vector storage | pgvector extension (start simple; move to dedicated vector DB only if scale demands it) | Avoids running a second database for MVP |
| Containerization | Docker + docker-compose (local), target Kubernetes-ready for prod | Standard portability |
| CI | GitHub Actions | Lint, type-check, test on every PR |

This is the default MVP stack; revisit if the team has existing infra (e.g., already on AWS SageMaker or an existing ATS) that should change these choices.

## High-level flow

```
Resume(s) ──▶ Ingestion API ──▶ Parser (text + structure extraction)
                                        │
                                        ▼
                              Feature/Embedding builder
                                        │
                    JD ──▶ JD Parser ──▶ Matching & Scoring
                                        │
                                        ▼
                         Ranking + Explainability layer
                                        │
                          ┌─────────────┴─────────────┐
                          ▼                            ▼
                   Audit Log (Postgres)      Results API / Webhook to HR system
                                                        │
                                                        ▼
                                          HR Admin Dashboard (review/override)
```

- Single-resume requests: synchronous path, target p95 < 2s.
- Batch requests: submitted to queue, processed by Celery workers, results retrievable via polling endpoint or webhook callback.

## Service boundaries
- `api/` — FastAPI app: request validation, auth, routing, sync scoring endpoint, batch submission/status endpoints
- `worker/` — Celery workers: batch resume processing, calls into `ml/` pipeline
- `ml/` — parsing, extraction, embedding, scoring, explainability logic (framework-agnostic, testable in isolation from API/worker)
- `integrations/` — HR/ATS adapters (webhook senders, CSV import/export)

Keeping `ml/` decoupled from `api/`/`worker/` lets model logic be evaluated/tested offline without spinning up the API.

## Governance & compliance hooks (see [TASKS.md](../TASKS.md) P3)
- Every scoring call writes an audit record: input hash, model version, output score, timestamp, requester
- Model version is pinned and logged per decision, so past decisions remain reproducible/explainable after model updates
- Fairness evaluation is a required gate before promoting a new model version to production (not just an ad hoc check)
- PII fields are flagged in the schema so they can be excluded from features used in scoring (avoid proxy discrimination via name, address, school)

## Latency strategy (see TASKS.md P3)
- Sync path only does single-resume scoring; batches always go async
- Embedding model runs on CPU for MVP with batching; revisit GPU/ONNX/quantization only if p95 targets are missed under load testing
- Cache JD embeddings (JD doesn't change per-resume within a batch) to avoid recomputation
