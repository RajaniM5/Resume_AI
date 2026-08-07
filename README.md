# Resume AI — AI-Powered Resume Screening System

NLP/ML-based resume screening with APIs for HR system integration. See [TASKS.md](TASKS.md) for the prioritized roadmap.

## Docs
- [docs/SCOPE.md](docs/SCOPE.md) — what's in/out of scope, success metrics
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — tech stack, service boundaries, governance/latency strategy
- [docs/DATA.md](docs/DATA.md) — training/eval data requirements and sourcing plan
- [docs/UI_DESIGN.md](docs/UI_DESIGN.md) — HR admin dashboard screens, tech choice, build phases

## Project layout
```
api/            FastAPI app — routing, auth, request validation
worker/         Celery workers for async batch resume processing
ml/             Parsing, matching, and scoring logic (framework-agnostic)
integrations/   HR/ATS adapters (webhooks, CSV import/export)
data/           raw/ and processed/ are gitignored (never commit real resumes); sample/ holds synthetic test fixtures
tests/          unit/ and integration/ tests
```

## Getting started
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # API/worker only, no torch
# pip install -e ".[dev,ml]"   # adds spaCy/sentence-transformers (needed for ml/ pipeline work; requires a torch wheel for your platform)
python -m spacy download en_core_web_sm  # only if you installed the ml extra

uvicorn api.main:app --reload
```

> Note: `sentence-transformers` depends on PyTorch, which doesn't publish wheels for every platform (e.g. Intel macOS + Python 3.13). If `pip install -e ".[dev,ml]"` fails to resolve locally, either use Docker (planned) or a supported Python/platform combo — CI runs on Linux, where this isn't an issue.

Run tests:
```bash
pytest
```
