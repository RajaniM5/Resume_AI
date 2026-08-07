"""Pydantic request/response models — the REST API contract.

Kept separate from ORM/DB models: these describe what crosses the wire,
not how anything is persisted.
"""

from __future__ import annotations

import base64
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5MB


class ResumeFile(BaseModel):
    """A single resume, submitted inline as base64-encoded file content."""

    candidate_id: str | None = Field(
        default=None, description="Caller-supplied candidate identifier, echoed back in results."
    )
    filename: str = Field(description="Original filename, used to select a parser (.pdf/.docx/.txt).")
    content_base64: str = Field(description="Base64-encoded raw file bytes.")

    @field_validator("filename")
    @classmethod
    def _validate_extension(cls, v: str) -> str:
        ext = "." + v.rsplit(".", 1)[-1].lower() if "." in v else ""
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            raise ValueError(f"unsupported file type '{ext}'; allowed: {sorted(ALLOWED_RESUME_EXTENSIONS)}")
        return v

    @field_validator("content_base64")
    @classmethod
    def _validate_content(cls, v: str) -> str:
        try:
            decoded = base64.b64decode(v, validate=True)
        except Exception as exc:
            raise ValueError("content_base64 is not valid base64") from exc
        if len(decoded) == 0:
            raise ValueError("resume content is empty")
        if len(decoded) > MAX_RESUME_BYTES:
            raise ValueError(f"resume exceeds max size of {MAX_RESUME_BYTES} bytes")
        return v

    def decoded_bytes(self) -> bytes:
        return base64.b64decode(self.content_base64)


class ExplanationFactor(BaseModel):
    """One contributing factor behind a score, for explainability (see docs/ARCHITECTURE.md)."""

    factor: str
    detail: str
    weight: float = Field(ge=0, le=1)


class ScoreResult(BaseModel):
    candidate_id: str | None = None
    score: float = Field(ge=0, le=100, description="Overall match score, 0-100.")
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: list[ExplanationFactor]
    model_version: str


class ScreeningRequest(BaseModel):
    """Synchronous single-resume screening request."""

    job_description: str = Field(min_length=1)
    resume: ResumeFile


class BatchScreeningRequest(BaseModel):
    """Batch screening request — processed asynchronously via the task queue."""

    job_description: str = Field(min_length=1)
    resumes: list[ResumeFile] = Field(min_length=1, max_length=500)
    webhook_url: HttpUrl | None = Field(
        default=None, description="If set, results are POSTed here when the batch completes."
    )


class BatchScreeningAccepted(BaseModel):
    job_id: str
    status: Literal["queued"] = "queued"
    submitted_count: int


class BatchScreeningStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    total: int | None = None
    completed_count: int | None = None
    results: list[ScoreResult] | None = None
    error: str | None = None


class WebhookPayload(BaseModel):
    """Body POSTed to `webhook_url` when a batch job finishes."""

    job_id: str
    status: Literal["completed", "failed"]
    results: list[ScoreResult] | None = None
    error: str | None = None
