from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

JOB_DESCRIPTION = "Backend engineer. Requires Python and AWS. 3+ years experience."


def _resume_payload(sample_resume_base64: str, candidate_id: str = "cand-1") -> dict:
    return {
        "candidate_id": candidate_id,
        "filename": "resume.txt",
        "content_base64": sample_resume_base64,
    }


def test_screen_resume_requires_api_key(sample_resume_base64: str) -> None:
    response = client.post(
        "/api/v1/screenings",
        json={"job_description": JOB_DESCRIPTION, "resume": _resume_payload(sample_resume_base64)},
    )
    assert response.status_code == 401


def test_screen_resume_rejects_bad_api_key(sample_resume_base64: str) -> None:
    response = client.post(
        "/api/v1/screenings",
        headers={"X-API-Key": "wrong-key"},
        json={"job_description": JOB_DESCRIPTION, "resume": _resume_payload(sample_resume_base64)},
    )
    assert response.status_code == 401


def test_screen_resume_scores_matched_skills(sample_resume_base64: str, api_key_headers: dict) -> None:
    response = client.post(
        "/api/v1/screenings",
        headers=api_key_headers,
        json={"job_description": JOB_DESCRIPTION, "resume": _resume_payload(sample_resume_base64)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["candidate_id"] == "cand-1"
    assert "python" in body["matched_skills"]
    assert "aws" in body["matched_skills"]
    assert 0 <= body["score"] <= 100
    assert body["explanation"]


def test_screen_resume_rejects_unsupported_extension(sample_resume_base64: str, api_key_headers: dict) -> None:
    response = client.post(
        "/api/v1/screenings",
        headers=api_key_headers,
        json={
            "job_description": JOB_DESCRIPTION,
            "resume": {"candidate_id": "cand-1", "filename": "resume.exe", "content_base64": sample_resume_base64},
        },
    )
    assert response.status_code == 422


def test_screen_resume_rejects_invalid_base64(api_key_headers: dict) -> None:
    response = client.post(
        "/api/v1/screenings",
        headers=api_key_headers,
        json={
            "job_description": JOB_DESCRIPTION,
            "resume": {"candidate_id": "cand-1", "filename": "resume.txt", "content_base64": "not-base64!!"},
        },
    )
    assert response.status_code == 422


def test_batch_submit_and_poll_to_completion(sample_resume_base64: str, api_key_headers: dict) -> None:
    submit = client.post(
        "/api/v1/screenings/batch",
        headers=api_key_headers,
        json={
            "job_description": JOB_DESCRIPTION,
            "resumes": [_resume_payload(sample_resume_base64, "cand-1"), _resume_payload(sample_resume_base64, "cand-2")],
        },
    )
    assert submit.status_code == 202
    body = submit.json()
    assert body["submitted_count"] == 2
    job_id = body["job_id"]

    status_response = client.get(f"/api/v1/screenings/batch/{job_id}", headers=api_key_headers)
    assert status_response.status_code == 200
    status_body = status_response.json()
    # Celery runs eagerly in tests (see conftest.py), so the job is already done.
    assert status_body["status"] == "completed"
    assert status_body["total"] == 2
    assert len(status_body["results"]) == 2


def test_batch_status_unknown_job_id_pending(api_key_headers: dict) -> None:
    response = client.get("/api/v1/screenings/batch/does-not-exist", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_batch_rejects_empty_resume_list(api_key_headers: dict) -> None:
    response = client.post(
        "/api/v1/screenings/batch",
        headers=api_key_headers,
        json={"job_description": JOB_DESCRIPTION, "resumes": []},
    )
    assert response.status_code == 422
