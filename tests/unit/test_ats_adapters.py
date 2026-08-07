import pytest

from integrations.ats.greenhouse import MissingResumeAttachment as GreenhouseMissingAttachment
from integrations.ats.greenhouse import from_greenhouse_candidate
from integrations.ats.workday import MissingResumeAttachment as WorkdayMissingAttachment
from integrations.ats.workday import from_workday_candidate


def test_from_greenhouse_candidate_maps_resume_attachment() -> None:
    payload = {
        "id": 12345,
        "first_name": "Jane",
        "last_name": "Doe",
        "attachments": [
            {"filename": "cover_letter.pdf", "type": "cover_letter", "content_base64": "xxx"},
            {"filename": "resume.pdf", "type": "resume", "content_base64": "YWJj"},
        ],
    }
    result = from_greenhouse_candidate(payload)
    assert result == {"candidate_id": "12345", "filename": "resume.pdf", "content_base64": "YWJj"}


def test_from_greenhouse_candidate_no_resume_attachment_raises() -> None:
    with pytest.raises(GreenhouseMissingAttachment):
        from_greenhouse_candidate({"id": 1, "attachments": []})


def test_from_greenhouse_candidate_unfetched_url_raises() -> None:
    payload = {"id": 1, "attachments": [{"filename": "resume.pdf", "type": "resume", "url": "https://..."}]}
    with pytest.raises(GreenhouseMissingAttachment):
        from_greenhouse_candidate(payload)


def test_from_workday_candidate_maps_resume_attachment() -> None:
    payload = {
        "candidateId": "C-999",
        "resumeAttachment": {"fileName": "resume.docx", "fileContentBase64": "YWJj"},
    }
    result = from_workday_candidate(payload)
    assert result == {"candidate_id": "C-999", "filename": "resume.docx", "content_base64": "YWJj"}


def test_from_workday_candidate_missing_attachment_raises() -> None:
    with pytest.raises(WorkdayMissingAttachment):
        from_workday_candidate({"candidateId": "C-999"})
