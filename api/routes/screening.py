from __future__ import annotations

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import enforce_rate_limit, require_api_key
from api.schemas import (
    BatchScreeningAccepted,
    BatchScreeningRequest,
    BatchScreeningStatus,
    ScoreResult,
    ScreeningRequest,
)
from worker.celery_app import celery_app
from worker.tasks import score_one_resume, screen_batch

router = APIRouter(
    prefix="/api/v1/screenings",
    tags=["screening"],
    dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
)


@router.post("", response_model=ScoreResult)
def screen_resume(request: ScreeningRequest) -> ScoreResult:
    """Synchronous single-resume scoring. Target p95 < 2s (see docs/SCOPE.md)."""
    result = score_one_resume(
        {
            "candidate_id": request.resume.candidate_id,
            "filename": request.resume.filename,
            "content_base64": request.resume.content_base64,
        },
        request.job_description,
    )
    return ScoreResult(**result)


@router.post("/batch", response_model=BatchScreeningAccepted, status_code=status.HTTP_202_ACCEPTED)
def submit_batch(request: BatchScreeningRequest) -> BatchScreeningAccepted:
    """Enqueue a batch for async processing; poll GET /batch/{job_id} for results."""
    resumes_payload = [
        {
            "candidate_id": r.candidate_id,
            "filename": r.filename,
            "content_base64": r.content_base64,
        }
        for r in request.resumes
    ]
    webhook_url = str(request.webhook_url) if request.webhook_url else None
    async_result = screen_batch.delay(request.job_description, resumes_payload, webhook_url)
    return BatchScreeningAccepted(job_id=async_result.id, submitted_count=len(request.resumes))


@router.get("/batch/{job_id}", response_model=BatchScreeningStatus)
def get_batch_status(job_id: str) -> BatchScreeningStatus:
    async_result = AsyncResult(job_id, app=celery_app)

    if async_result.state == "PENDING":
        return BatchScreeningStatus(job_id=job_id, status="queued")

    if async_result.state == "PROCESSING":
        meta = async_result.info or {}
        return BatchScreeningStatus(
            job_id=job_id,
            status="processing",
            total=meta.get("total"),
            completed_count=meta.get("completed"),
        )

    if async_result.state == "SUCCESS":
        payload = async_result.result
        return BatchScreeningStatus(
            job_id=job_id,
            status="completed",
            total=payload["total"],
            completed_count=payload["total"],
            results=payload["results"],
        )

    if async_result.state == "FAILURE":
        return BatchScreeningStatus(job_id=job_id, status="failed", error=str(async_result.info))

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"unknown job state: {async_result.state}")
