from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from api import dashboard_data as data

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/")
def job_reqs(request: Request):
    return templates.TemplateResponse(
        request, "dashboard/job_reqs.html", {"job_reqs": data.list_job_reqs()}
    )


@router.get("/reqs/{job_req_id}")
def candidates(request: Request, job_req_id: str):
    job_req = data.get_job_req(job_req_id)
    if job_req is None:
        raise HTTPException(status_code=404, detail="Job req not found")
    return templates.TemplateResponse(
        request,
        "dashboard/candidates.html",
        {"job_req": job_req, "candidates": data.list_candidates(job_req_id)},
    )


@router.get("/candidates/{candidate_id}")
def candidate_detail(request: Request, candidate_id: str):
    candidate = data.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job_req = data.get_job_req(candidate["job_req_id"])
    return templates.TemplateResponse(
        request,
        "dashboard/candidate_detail.html",
        {"candidate": candidate, "job_req": job_req},
    )


@router.post("/candidates/{candidate_id}/override")
def override_candidate(candidate_id: str, reason: str = Form(...)):
    candidate = data.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    data.override_candidate(candidate_id, reason)
    return RedirectResponse(url=f"/dashboard/candidates/{candidate_id}", status_code=303)


@router.get("/audit")
def audit_log(request: Request):
    return templates.TemplateResponse(
        request, "dashboard/audit_log.html", {"entries": data.list_audit_log()}
    )
