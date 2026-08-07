"""Celery tasks: async batch resume screening.

Queue-side glue only — parsing/matching/scoring logic lives in `ml/`
(text_extraction, resume_extractor, jd_parser, matching.scoring), so both this
async path and the synchronous single-resume API route share one
implementation via `score_one_resume`.
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ml.matching.scoring import semantic_similarity, skill_gap
from ml.parsing.jd_parser import parse_job_description
from ml.parsing.resume_extractor import extract_resume
from ml.parsing.text_extraction import UnsupportedFileTypeError, extract_text
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# Blend weights when the semantic model is available. Skill coverage alone
# is the fallback when it isn't (see `score_one_resume`).
_SEMANTIC_WEIGHT = 0.6
_SKILL_COVERAGE_WEIGHT = 0.4


@dataclass(frozen=True)
class ScoringExplanationFactor:
    factor: str
    detail: str
    weight: float


def _resume_text_from_bytes(filename: str, content: bytes) -> str:
    """`ml.parsing.text_extraction.extract_text` reads from a file path, so
    write the uploaded bytes to a scratch file for the duration of parsing."""
    suffix = Path(filename).suffix or ".txt"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        return extract_text(tmp_path).text
    finally:
        os.unlink(tmp_path)


def score_one_resume(resume: dict[str, Any], job_description: str) -> dict[str, Any]:
    candidate_id = resume.get("candidate_id")
    try:
        text = _resume_text_from_bytes(resume["filename"], base64.b64decode(resume["content_base64"]))
    except UnsupportedFileTypeError as exc:
        return {
            "candidate_id": candidate_id,
            "score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "explanation": [{"factor": "parse_error", "detail": str(exc), "weight": 1.0}],
            "model_version": "n/a",
        }

    parsed_resume = extract_resume(text)
    parsed_jd = parse_job_description(job_description)
    gap = skill_gap(parsed_resume, parsed_jd)

    semantic_score: float | None = None
    try:
        semantic_score = semantic_similarity(parsed_resume, parsed_jd)
    except Exception:
        # Semantic model unavailable (extra not installed, or no network to
        # fetch weights) — degrade to skill-coverage-only rather than fail
        # the whole screening call. See ml/matching/embeddings.py.
        logger.info("semantic similarity unavailable, falling back to skill-coverage-only scoring", exc_info=True)

    required_total = len(gap.matched_skills) + len(gap.missing_skills)
    coverage_detail = f"{len(gap.matched_skills)}/{required_total} required skills present in resume"

    if semantic_score is not None:
        score = round((_SEMANTIC_WEIGHT * semantic_score + _SKILL_COVERAGE_WEIGHT * gap.coverage) * 100, 1)
        explanation = [
            ScoringExplanationFactor(
                factor="semantic_similarity",
                detail=f"embedding cosine similarity between resume and JD: {semantic_score:.2f}",
                weight=_SEMANTIC_WEIGHT,
            ),
            ScoringExplanationFactor(factor="skill_coverage", detail=coverage_detail, weight=_SKILL_COVERAGE_WEIGHT),
        ]
        model_version = "skill-coverage-v1+semantic-all-mpnet-base-v2"
    else:
        score = round(gap.coverage * 100, 1)
        explanation = [ScoringExplanationFactor(factor="skill_coverage", detail=coverage_detail, weight=1.0)]
        model_version = "skill-coverage-v1"

    return {
        "candidate_id": candidate_id,
        "score": score,
        "matched_skills": gap.matched_skills,
        "missing_skills": gap.missing_skills,
        "explanation": [asdict(factor) for factor in explanation],
        "model_version": model_version,
    }


@celery_app.task(bind=True, name="worker.tasks.screen_batch")
def screen_batch(
    self,
    job_description: str,
    resumes: list[dict[str, Any]],
    webhook_url: str | None = None,
) -> dict[str, Any]:
    total = len(resumes)
    results: list[dict[str, Any]] = []

    for i, resume in enumerate(resumes, start=1):
        results.append(score_one_resume(resume, job_description))
        self.update_state(state="PROCESSING", meta={"completed": i, "total": total})

    payload = {"job_id": self.request.id, "status": "completed", "results": results, "total": total}

    if webhook_url:
        from integrations.webhooks import deliver_webhook

        deliver_webhook(webhook_url, payload)

    return payload
